from datetime import datetime, timedelta, timezone

from tests.conftest import criar_solicitacao, enviar_exame, enviar_mensagem


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
    enviar_mensagem(cliente, paciente, jornada, "Doutora, já agendei o exame.")
    enviar_exame(cliente, paciente, jornada, solicitacao_id=solicitacao["id"])
    enviar_mensagem(cliente, medico, jornada, "Recebido, obrigada!")
    # Retorno marcado para o futuro fica no fim
    _registrar_consulta(cliente, medico, jornada, agora + timedelta(days=5), tipo="retorno")


def test_linha_do_tempo_em_ordem_cronologica(cliente, medico, paciente, jornada):
    _montar_jornada_com_historico(cliente, medico, paciente, jornada)

    resposta = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=paciente["headers"])
    assert resposta.status_code == 200
    eventos = resposta.json()

    assert [e["tipo"] for e in eventos] == [
        "consulta",
        "solicitacao",
        "mensagem",
        "exame",
        "mensagem",
        "consulta",
    ]
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
    assert eventos[2]["resumo"] == "Carlos Lima: Doutora, já agendei o exame."
    assert eventos[3]["resumo"] == "Carlos Lima enviou: Hemograma completo"
    assert eventos[3]["dados"]["arquivo"]["nome_original"] == "hemograma.pdf"
    assert eventos[5]["resumo"] == "Retorno realizado (1 prescrição)"


def test_filtro_por_tipo(cliente, medico, paciente, jornada):
    _montar_jornada_com_historico(cliente, medico, paciente, jornada)
    url = f"/journeys/{jornada['id']}/timeline"

    so_mensagens = cliente.get(url, params={"tipos": "mensagem"}, headers=medico["headers"]).json()
    assert [e["tipo"] for e in so_mensagens] == ["mensagem", "mensagem"]

    varios = cliente.get(url, params={"tipos": "consulta, exame"}, headers=medico["headers"]).json()
    assert [e["tipo"] for e in varios] == ["consulta", "exame", "consulta"]


def test_filtro_com_tipo_invalido_retorna_422(cliente, medico, jornada):
    resposta = cliente.get(
        f"/journeys/{jornada['id']}/timeline", params={"tipos": "exame,receita"}, headers=medico["headers"]
    )
    assert resposta.status_code == 422
    assert "receita" in resposta.json()["detail"]


def test_linha_do_tempo_vazia(cliente, medico, jornada):
    resposta = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=medico["headers"])
    assert resposta.json() == []


def test_mensagem_so_com_anexo_no_resumo(cliente, paciente, jornada):
    cliente.post(
        f"/journeys/{jornada['id']}/messages",
        files={"arquivo": ("dieta.pdf", b"%PDF")},
        headers=paciente["headers"],
    )
    evento = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=paciente["headers"]).json()[0]
    assert evento["resumo"] == "Carlos Lima enviou um anexo: dieta.pdf"


def test_linha_do_tempo_exige_acesso(cliente, medico, outro_medico, outro_paciente, jornada):
    url = f"/journeys/{jornada['id']}/timeline"
    assert cliente.get(url).status_code == 401
    assert cliente.get(url, headers=outro_medico["headers"]).status_code == 403
    assert cliente.get(url, headers=outro_paciente["headers"]).status_code == 403


def test_linha_do_tempo_bloqueada_com_vinculo_inativo(cliente, medico, paciente, jornada):
    vinculo_id = cliente.get("/links", headers=medico["headers"]).json()[0]["id"]
    cliente.patch(f"/links/{vinculo_id}", json={"ativo": False}, headers=medico["headers"])
    resposta = cliente.get(f"/journeys/{jornada['id']}/timeline", headers=paciente["headers"])
    assert resposta.status_code == 403
