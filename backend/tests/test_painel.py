from datetime import timedelta

from tests.conftest import criar_acompanhamento, criar_solicitacao, definir_prazo, enviar_documento


def _painel(cliente, usuario) -> dict:
    resposta = cliente.get("/dashboard/pending", headers=usuario["headers"])
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_painel_vazio_por_tipo_de_usuario(cliente, medico, paciente, acompanhamento):
    assert _painel(cliente, medico) == {
        "tipo_usuario": "medico",
        "dias_prazo_proximo": 3,
        "documentos_aguardando_revisao": [],
        "solicitacoes_vencidas": [],
        "solicitacoes_proximas_do_prazo": [],
    }
    assert _painel(cliente, paciente) == {
        "tipo_usuario": "paciente",
        "solicitacoes_pendentes": [],
        "consultas_extras": [],
    }


def test_painel_exige_login(cliente):
    assert cliente.get("/dashboard/pending").status_code == 401


def test_medico_ve_documentos_aguardando_revisao(cliente, medico, paciente, acompanhamento):
    enviar_documento(cliente, paciente, acompanhamento)
    revisado = enviar_documento(cliente, paciente, acompanhamento).json()
    cliente.patch(f"/documents/{revisado['id']}/review", json={}, headers=medico["headers"])
    # Arquivo enviado pelo próprio médico não entra como pendência dele
    enviar_documento(cliente, medico, acompanhamento)

    exames = _painel(cliente, medico)["documentos_aguardando_revisao"]
    assert len(exames) == 1
    assert exames[0]["status"] == "enviado"
    assert exames[0]["acompanhamento"]["paciente"]["nome"] == "Carlos Lima"


def test_medico_ve_solicitacoes_vencidas_e_proximas(cliente, medico, acompanhamento):
    vencida = criar_solicitacao(cliente, medico, acompanhamento)
    definir_prazo(vencida["id"], timedelta(days=-2))
    proxima = criar_solicitacao(cliente, medico, acompanhamento, dias=2)
    criar_solicitacao(cliente, medico, acompanhamento, dias=10)  # longe do prazo: fora do painel
    cancelada = criar_solicitacao(cliente, medico, acompanhamento, dias=1)
    cliente.patch(f"/requests/{cancelada['id']}/cancel", headers=medico["headers"])

    painel = _painel(cliente, medico)
    assert [s["id"] for s in painel["solicitacoes_vencidas"]] == [vencida["id"]]
    assert painel["solicitacoes_vencidas"][0]["vencida"] is True
    assert [s["id"] for s in painel["solicitacoes_proximas_do_prazo"]] == [proxima["id"]]


def test_prazo_proximo_segue_configuracao(cliente, medico, acompanhamento, config_teste, monkeypatch):
    monkeypatch.setattr(config_teste, "dias_prazo_proximo", 15)
    criar_solicitacao(cliente, medico, acompanhamento, dias=10)
    painel = _painel(cliente, medico)
    assert painel["dias_prazo_proximo"] == 15
    assert len(painel["solicitacoes_proximas_do_prazo"]) == 1


def test_paciente_ve_pendencias_e_consultas_extras(cliente, medico, paciente, acompanhamento):
    vencida = criar_solicitacao(cliente, medico, acompanhamento, tipo="exame")
    definir_prazo(vencida["id"], timedelta(days=-1))
    futura = criar_solicitacao(cliente, medico, acompanhamento, tipo="orientacao_profissional", dias=20)
    consulta_extra = criar_solicitacao(cliente, medico, acompanhamento, tipo="consulta_extra", dias=4)
    atendida = criar_solicitacao(cliente, medico, acompanhamento, tipo="exame")
    enviar_documento(cliente, paciente, acompanhamento, solicitacao_id=atendida["id"])

    painel = _painel(cliente, paciente)
    pendentes = painel["solicitacoes_pendentes"]
    # Todas as pendentes, com prazo, vencidas primeiro
    assert [s["id"] for s in pendentes] == [vencida["id"], futura["id"]]
    assert [s["vencida"] for s in pendentes] == [True, False]
    assert [s["id"] for s in painel["consultas_extras"]] == [consulta_extra["id"]]


def test_painel_do_paciente_so_mostra_a_proprio_acompanhamento(cliente, medico, paciente, outro_paciente, acompanhamento):
    outro_acompanhamento = criar_acompanhamento(cliente, medico, outro_paciente)
    criar_solicitacao(cliente, medico, outro_acompanhamento)

    assert _painel(cliente, paciente)["solicitacoes_pendentes"] == []
    assert len(_painel(cliente, outro_paciente)["solicitacoes_pendentes"]) == 1


def test_painel_do_medico_reune_todos_os_pacientes(cliente, medico, paciente, outro_paciente, acompanhamento):
    outro_acompanhamento = criar_acompanhamento(cliente, medico, outro_paciente)
    enviar_documento(cliente, paciente, acompanhamento)
    enviar_documento(cliente, outro_paciente, outro_acompanhamento)

    exames = _painel(cliente, medico)["documentos_aguardando_revisao"]
    assert {e["acompanhamento"]["paciente"]["nome"] for e in exames} == {"Carlos Lima", "Maria Alves"}


def test_acompanhamento_encerrado_sai_do_painel(cliente, medico, paciente, acompanhamento):
    enviar_documento(cliente, paciente, acompanhamento)
    criar_solicitacao(cliente, medico, acompanhamento, dias=1)
    assert len(_painel(cliente, medico)["documentos_aguardando_revisao"]) == 1

    cliente.patch(f"/follow-ups/{acompanhamento['id']}/status", json={"status": "encerrado"}, headers=medico["headers"])
    assert _painel(cliente, medico)["documentos_aguardando_revisao"] == []
    assert _painel(cliente, paciente)["solicitacoes_pendentes"] == []
