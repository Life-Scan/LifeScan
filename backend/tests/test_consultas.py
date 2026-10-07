def _dados_consulta(**extras) -> dict:
    return {
        "tipo": "consulta",
        "data": "2026-09-20T14:30:00-03:00",
        "anotacoes": "Pressão 14x9. Iniciar medicação.",
        "prescricoes": [
            {"descricao": "Losartana 50 mg", "dosagem": "1 comprimido", "instrucoes": "Pela manhã"},
            {"descricao": "Caminhada leve"},
        ],
        **extras,
    }


def test_medico_registra_consulta_com_prescricoes(cliente, medico, jornada):
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/consultations", json=_dados_consulta(), headers=medico["headers"]
    )
    assert resposta.status_code == 201, resposta.text
    consulta = resposta.json()
    assert consulta["tipo"] == "consulta"
    # 14:30 em -03:00 é gravado e devolvido como 17:30 UTC
    assert consulta["data"] == "2026-09-20T17:30:00Z"
    assert [p["descricao"] for p in consulta["prescricoes"]] == ["Losartana 50 mg", "Caminhada leve"]
    assert consulta["prescricoes"][1]["dosagem"] is None


def test_medico_registra_retorno(cliente, medico, jornada):
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/consultations",
        json=_dados_consulta(tipo="retorno", prescricoes=[]),
        headers=medico["headers"],
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "retorno"


def test_tipo_de_consulta_invalido_retorna_422(cliente, medico, jornada):
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/consultations",
        json=_dados_consulta(tipo="cirurgia"),
        headers=medico["headers"],
    )
    assert resposta.status_code == 422


def test_paciente_nao_registra_consulta_mas_ve_a_lista(cliente, medico, paciente, jornada):
    url = f"/journeys/{jornada['id']}/consultations"
    assert cliente.post(url, json=_dados_consulta(), headers=paciente["headers"]).status_code == 403

    cliente.post(url, json=_dados_consulta(), headers=medico["headers"])
    lista = cliente.get(url, headers=paciente["headers"])
    assert lista.status_code == 200
    assert len(lista.json()) == 1


def test_consultas_listadas_da_mais_recente_para_a_mais_antiga(cliente, medico, jornada):
    url = f"/journeys/{jornada['id']}/consultations"
    for data in ("2026-08-01T10:00:00Z", "2026-09-01T10:00:00Z", "2026-07-01T10:00:00Z"):
        cliente.post(url, json=_dados_consulta(data=data), headers=medico["headers"])
    datas = [c["data"][:10] for c in cliente.get(url, headers=medico["headers"]).json()]
    assert datas == ["2026-09-01", "2026-08-01", "2026-07-01"]


def test_nao_registra_consulta_em_jornada_encerrada(cliente, medico, jornada):
    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/consultations", json=_dados_consulta(), headers=medico["headers"]
    )
    assert resposta.status_code == 409


def test_terceiros_nao_veem_consultas(cliente, outro_paciente, jornada):
    resposta = cliente.get(f"/journeys/{jornada['id']}/consultations", headers=outro_paciente["headers"])
    assert resposta.status_code == 403
