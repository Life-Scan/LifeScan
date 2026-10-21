from datetime import datetime, timedelta, timezone

from tests.conftest import criar_solicitacao, definir_prazo


def test_medico_cria_solicitacoes_de_todos_os_tipos(cliente, medico, acompanhamento):
    for tipo in ("exame", "consulta_extra", "orientacao_profissional", "outro"):
        solicitacao = criar_solicitacao(cliente, medico, acompanhamento, tipo=tipo)
        assert solicitacao["tipo"] == tipo
        assert solicitacao["status"] == "pendente"
        assert solicitacao["vencida"] is False


def test_prazo_no_passado_retorna_422(cliente, medico, acompanhamento):
    ontem = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    resposta = cliente.post(
        f"/follow-ups/{acompanhamento['id']}/requests",
        json={"tipo": "exame", "descricao": "Hemograma", "prazo": ontem},
        headers=medico["headers"],
    )
    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "O prazo deve ser uma data futura."


def test_paciente_nao_cria_solicitacao(cliente, paciente, acompanhamento):
    prazo = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    resposta = cliente.post(
        f"/follow-ups/{acompanhamento['id']}/requests",
        json={"tipo": "exame", "descricao": "Hemograma", "prazo": prazo},
        headers=paciente["headers"],
    )
    assert resposta.status_code == 403


def test_vencida_e_calculada_e_nao_gravada(cliente, medico, paciente, acompanhamento):
    solicitacao = criar_solicitacao(cliente, medico, acompanhamento)
    definir_prazo(solicitacao["id"], timedelta(days=-1))

    lista = cliente.get(f"/follow-ups/{acompanhamento['id']}/requests", headers=paciente["headers"]).json()
    assert lista[0]["status"] == "pendente"
    assert lista[0]["vencida"] is True


def test_paciente_ve_consulta_extra_mas_nao_age_sobre_ela(cliente, medico, paciente, acompanhamento):
    consulta_extra = criar_solicitacao(cliente, medico, acompanhamento, tipo="consulta_extra")

    lista = cliente.get(f"/follow-ups/{acompanhamento['id']}/requests", headers=paciente["headers"]).json()
    assert [s["tipo"] for s in lista] == ["consulta_extra"]

    for acao in ("complete", "cancel"):
        resposta = cliente.patch(f"/requests/{consulta_extra['id']}/{acao}", headers=paciente["headers"])
        assert resposta.status_code == 403


def test_medico_conclui_e_cancela_solicitacoes(cliente, medico, acompanhamento):
    consulta_extra = criar_solicitacao(cliente, medico, acompanhamento, tipo="consulta_extra")
    outro = criar_solicitacao(cliente, medico, acompanhamento, tipo="outro")

    concluida = cliente.patch(f"/requests/{consulta_extra['id']}/complete", headers=medico["headers"]).json()
    assert concluida["status"] == "atendida"
    assert concluida["atendida_em"] is not None

    cancelada = cliente.patch(f"/requests/{outro['id']}/cancel", headers=medico["headers"]).json()
    assert cancelada["status"] == "cancelada"
    assert cancelada["vencida"] is False

    # Já resolvidas não podem mudar de novo
    resposta = cliente.patch(f"/requests/{outro['id']}/complete", headers=medico["headers"])
    assert resposta.status_code == 409


def test_filtro_por_status(cliente, medico, acompanhamento):
    primeira = criar_solicitacao(cliente, medico, acompanhamento)
    criar_solicitacao(cliente, medico, acompanhamento)
    cliente.patch(f"/requests/{primeira['id']}/cancel", headers=medico["headers"])

    pendentes = cliente.get(
        f"/follow-ups/{acompanhamento['id']}/requests", params={"status": "pendente"}, headers=medico["headers"]
    ).json()
    assert len(pendentes) == 1


def test_parceiro_nao_conclui_solicitacao(cliente, medico, parceiro, acompanhamento):
    solicitacao = criar_solicitacao(cliente, medico, acompanhamento)
    resposta = cliente.patch(f"/requests/{solicitacao['id']}/complete", headers=parceiro["headers"])
    assert resposta.status_code == 403
