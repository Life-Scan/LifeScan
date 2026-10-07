"""Ficha do paciente: mantida pelo médico, lida pelo paciente e pelos parceiros atribuídos."""

from datetime import date, timedelta

FICHA = {
    "data_nascimento": "1978-03-14",
    "sexo": "masculino",
    "altura_cm": 172,
    "peso_kg": 84.5,
    "diagnosticos": "Hipertensão estágio 1",
    "alergias": "Dipirona",
    "medicamentos_em_uso": "Losartana 50 mg",
    "restricoes": "Evitar exercícios de alto impacto",
    "objetivos": "Reduzir a pressão e perder 8 kg",
    "observacoes": "  ",
}


def _url(jornada) -> str:
    return f"/journeys/{jornada['id']}/patient-record"


def test_ficha_ainda_nao_preenchida(cliente, medico, paciente, jornada):
    resposta = cliente.get(_url(jornada), headers=medico["headers"])
    assert resposta.status_code == 200
    ficha = resposta.json()
    assert ficha["preenchida"] is False
    assert ficha["paciente"]["nome"] == "Carlos Lima"
    assert ficha["idade"] is None
    assert ficha["atualizado_em"] is None


def test_medico_preenche_a_ficha(cliente, medico, jornada):
    resposta = cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])
    assert resposta.status_code == 200, resposta.text
    ficha = resposta.json()
    assert ficha["preenchida"] is True
    assert ficha["sexo"] == "masculino"
    assert ficha["altura_cm"] == 172
    assert ficha["peso_kg"] == 84.5
    assert ficha["diagnosticos"] == "Hipertensão estágio 1"
    # Texto só com espaços é gravado como vazio
    assert ficha["observacoes"] is None
    assert ficha["atualizado_em"] is not None

    hoje = date.today()
    esperada = hoje.year - 1978 - ((hoje.month, hoje.day) < (3, 14))
    assert ficha["idade"] == esperada


def test_salvar_substitui_a_ficha_inteira(cliente, medico, jornada):
    cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])
    resposta = cliente.put(_url(jornada), json={"alergias": "Nenhuma conhecida"}, headers=medico["headers"])
    ficha = resposta.json()
    assert ficha["alergias"] == "Nenhuma conhecida"
    assert ficha["diagnosticos"] is None
    assert ficha["data_nascimento"] is None
    assert ficha["idade"] is None


def test_validacoes_da_ficha(cliente, medico, jornada):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    for dados in (
        {"data_nascimento": amanha},
        {"altura_cm": 5},
        {"peso_kg": 900},
        {"sexo": "indefinido"},
    ):
        resposta = cliente.put(_url(jornada), json=dados, headers=medico["headers"])
        assert resposta.status_code == 422, dados

    resposta = cliente.put(_url(jornada), json={"data_nascimento": amanha}, headers=medico["headers"])
    assert "futuro" in str(resposta.json())


def test_paciente_le_a_propria_ficha_mas_nao_edita(cliente, medico, paciente, jornada):
    cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])

    leitura = cliente.get(_url(jornada), headers=paciente["headers"])
    assert leitura.status_code == 200
    assert leitura.json()["objetivos"] == "Reduzir a pressão e perder 8 kg"

    assert cliente.put(_url(jornada), json=FICHA, headers=paciente["headers"]).status_code == 403


def test_parceiro_atribuido_le_a_ficha_mas_nao_edita(cliente, medico, parceiro_atribuido, jornada):
    cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])

    leitura = cliente.get(_url(jornada), headers=parceiro_atribuido["headers"])
    assert leitura.status_code == 200
    assert leitura.json()["restricoes"] == "Evitar exercícios de alto impacto"

    assert cliente.put(_url(jornada), json=FICHA, headers=parceiro_atribuido["headers"]).status_code == 403


def test_quem_nao_participa_nao_le_a_ficha(cliente, medico, parceiro, outro_paciente, jornada):
    cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])
    # Parceiro existe, mas não foi atribuído a esta jornada
    for usuario in (parceiro, outro_paciente):
        assert cliente.get(_url(jornada), headers=usuario["headers"]).status_code == 403
    assert cliente.get(_url(jornada)).status_code == 401


def test_ficha_continua_editavel_com_a_jornada_encerrada(cliente, medico, jornada):
    cliente.patch(f"/journeys/{jornada['id']}/status", json={"status": "encerrada"}, headers=medico["headers"])
    resposta = cliente.put(_url(jornada), json=FICHA, headers=medico["headers"])
    assert resposta.status_code == 200
