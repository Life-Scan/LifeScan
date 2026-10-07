from datetime import datetime, timedelta, timezone

from tests.conftest import criar_solicitacao, enviar_exame


def _registrar_consulta(cliente, medico, jornada, data: datetime, tipo: str = "consulta") -> dict:
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/consultations",
        json={
            "tipo": tipo,
            "data": data.isoformat(),
            "prescricoes": [{"descricao": "Losartana 50 mg"}],
        },
        headers=medico["headers"],
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _montar_jornada_com_historico(cliente, medico, paciente, jornada):
    agora = datetime.now(timezone.utc)
    # Consulta realizada no passado, antes de tudo que foi criado agora
    _registrar_consulta(cliente, medico, jornada, agora - timedelta(days=10))
    solicitacao = criar_solicitacao(cliente, medico, jornada, tipo="exame")
    enviar_exame(cliente, paciente, jornada, solicitacao_id=solicitacao["id"])
    criar_solicitacao(cliente, medico, jornada, tipo="consulta_extra")
    # Retorno marcado para o futuro fica no fim
    _registrar_consulta(cliente, medico, jornada, agora + timedelta(days=5), tipo="retorno")


def test_linha_do_tempo_em_ordem_cronologica(cliente, medico, paciente, jornada):
    _montar_jornada_com_historico(cliente, medico, paciente, jornada)

    resposta = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=paciente["headers"])
    assert resposta.status_code == 200
    eventos = resposta.json()

    assert [e["tipo"] for e in eventos] == ["consulta", "solicitacao", "exame", "solicitacao", "consulta"]
    datas = [e["data"] for e in eventos]
    assert datas == sorted(datas)
    for evento in eventos:
        assert set(evento) == {"tipo", "id", "data", "resumo", "dados"}
        assert evento["data"].endswith("Z")


def test_resumos_e_dados_de_cada_evento(cliente, medico, paciente, jornada):
    _montar_jornada_com_historico(cliente, medico, paciente, jornada)
    eventos = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=medico["headers"]).json()

    assert eventos[0]["resumo"] == "Consulta realizada (1 prescrição)"
    # O exame atendeu a solicitação, e o resumo reflete o status atual
    assert eventos[1]["resumo"].endswith("(atendida)")
    assert eventos[1]["dados"]["status"] == "atendida"
    assert eventos[2]["resumo"] == "Carlos Lima enviou: Hemograma completo"
    assert eventos[2]["dados"]["arquivo"]["nome_original"] == "hemograma.pdf"
    assert eventos[3]["resumo"].startswith("Solicitação de consulta extra")
    assert eventos[4]["resumo"] == "Retorno realizado (1 prescrição)"


def test_filtro_por_tipo(cliente, medico, paciente, jornada):
    _montar_jornada_com_historico(cliente, medico, paciente, jornada)
    url = f"/journeys/{jornada['id']}/timeline"

    so_exames = cliente.get(url, params={"tipos": "exame"}, headers=medico["headers"]).json()
    assert [e["tipo"] for e in so_exames] == ["exame"]

    varios = cliente.get(url, params={"tipos": "consulta, exame"}, headers=medico["headers"]).json()
    assert [e["tipo"] for e in varios] == ["consulta", "exame", "consulta"]


def test_filtro_com_tipo_invalido_retorna_422(cliente, medico, jornada):
    # "mensagem" deixou de existir junto com o chat
    for tipos in ("exame,receita", "mensagem"):
        resposta = cliente.get(
            f"/journeys/{jornada['id']}/timeline", params={"tipos": tipos}, headers=medico["headers"]
        )
        assert resposta.status_code == 422
        assert "Tipo inválido" in resposta.json()["detail"]


def test_linha_do_tempo_vazia(cliente, medico, jornada):
    resposta = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=medico["headers"])
    assert resposta.json() == []


def test_linha_do_tempo_exige_acesso(cliente, outro_paciente, parceiro, jornada):
    url = f"/journeys/{jornada['id']}/timeline"
    assert cliente.get(url).status_code == 401
    assert cliente.get(url, headers=outro_paciente["headers"]).status_code == 403
    assert cliente.get(url, headers=parceiro["headers"]).status_code == 403


def test_chat_foi_removido(cliente, medico, jornada):
    assert cliente.get(f"/journeys/{jornada['id']}/messages", headers=medico["headers"]).status_code == 404
