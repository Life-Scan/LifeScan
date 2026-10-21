"""Anamnese do paciente: mantida pelo médico, lida pelo paciente e pelos parceiros atribuídos."""

from datetime import date, timedelta

ANAMNESE = {
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


def _url(acompanhamento) -> str:
    return f"/follow-ups/{acompanhamento['id']}/anamnesis"


def test_anamnese_ainda_nao_preenchida(cliente, medico, paciente, acompanhamento):
    resposta = cliente.get(_url(acompanhamento), headers=medico["headers"])
    assert resposta.status_code == 200
    anamnese = resposta.json()
    assert anamnese["preenchida"] is False
    assert anamnese["paciente"]["nome"] == "Carlos Lima"
    assert anamnese["idade"] is None
    assert anamnese["atualizado_em"] is None


def test_medico_preenche_a_anamnese(cliente, medico, acompanhamento):
    resposta = cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])
    assert resposta.status_code == 200, resposta.text
    anamnese = resposta.json()
    assert anamnese["preenchida"] is True
    assert anamnese["sexo"] == "masculino"
    assert anamnese["altura_cm"] == 172
    assert anamnese["peso_kg"] == 84.5
    assert anamnese["diagnosticos"] == "Hipertensão estágio 1"
    # Texto só com espaços é gravado como vazio
    assert anamnese["observacoes"] is None
    assert anamnese["atualizado_em"] is not None

    hoje = date.today()
    esperada = hoje.year - 1978 - ((hoje.month, hoje.day) < (3, 14))
    assert anamnese["idade"] == esperada


def test_salvar_substitui_a_anamnese_inteira(cliente, medico, acompanhamento):
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])
    resposta = cliente.put(_url(acompanhamento), json={"alergias": "Nenhuma conhecida"}, headers=medico["headers"])
    anamnese = resposta.json()
    assert anamnese["alergias"] == "Nenhuma conhecida"
    assert anamnese["diagnosticos"] is None
    assert anamnese["data_nascimento"] is None
    assert anamnese["idade"] is None


def test_validacoes_da_anamnese(cliente, medico, acompanhamento):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    for dados in (
        {"data_nascimento": amanha},
        {"altura_cm": 5},
        {"peso_kg": 900},
        {"sexo": "indefinido"},
    ):
        resposta = cliente.put(_url(acompanhamento), json=dados, headers=medico["headers"])
        assert resposta.status_code == 422, dados

    resposta = cliente.put(_url(acompanhamento), json={"data_nascimento": amanha}, headers=medico["headers"])
    assert "futuro" in str(resposta.json())


def test_paciente_le_a_propria_anamnese_mas_nao_edita(cliente, medico, paciente, acompanhamento):
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])

    leitura = cliente.get(_url(acompanhamento), headers=paciente["headers"])
    assert leitura.status_code == 200
    assert leitura.json()["objetivos"] == "Reduzir a pressão e perder 8 kg"

    assert cliente.put(_url(acompanhamento), json=ANAMNESE, headers=paciente["headers"]).status_code == 403


def test_parceiro_atribuido_le_a_anamnese_mas_nao_edita(cliente, medico, parceiro_atribuido, acompanhamento):
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])

    leitura = cliente.get(_url(acompanhamento), headers=parceiro_atribuido["headers"])
    assert leitura.status_code == 200
    assert leitura.json()["restricoes"] == "Evitar exercícios de alto impacto"

    assert cliente.put(_url(acompanhamento), json=ANAMNESE, headers=parceiro_atribuido["headers"]).status_code == 403


def test_quem_nao_participa_nao_le_a_anamnese(cliente, medico, parceiro, outro_paciente, acompanhamento):
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])
    # Parceiro existe, mas não foi atribuído a este acompanhamento
    for usuario in (parceiro, outro_paciente):
        assert cliente.get(_url(acompanhamento), headers=usuario["headers"]).status_code == 403
    assert cliente.get(_url(acompanhamento)).status_code == 401


def test_anamnese_continua_editavel_com_o_acompanhamento_encerrado(cliente, medico, acompanhamento):
    cliente.patch(f"/follow-ups/{acompanhamento['id']}/status", json={"status": "encerrado"}, headers=medico["headers"])
    resposta = cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])
    assert resposta.status_code == 200


def test_leitura_e_escrita_ficam_na_trilha_de_acesso(cliente, medico, paciente, acompanhamento):
    cliente.get(_url(acompanhamento), headers=medico["headers"])
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])
    cliente.get(_url(acompanhamento), headers=paciente["headers"])

    trilha = cliente.get(
        f"{_url(acompanhamento)}/acessos",
        headers=paciente["headers"],
    )
    assert trilha.status_code == 200
    registros = trilha.json()
    assert len(registros) == 3
    # Sem nomes: só o papel de quem acessou (LGPD: log pseudônimo)
    for registro in registros:
        assert set(registro) == {"tipo_usuario", "acao", "ocorreu_em"}

    # Mais recentes primeiro: leitura do paciente, escrita e leitura do médico
    assert [
        (r["tipo_usuario"], r["acao"]) for r in registros
    ] == [
        ("paciente", "leitura"),
        ("medico", "escrita"),
        ("medico", "leitura"),
    ]


def test_medico_vê_a_trilha_mas_parceiro_nao(cliente, medico, parceiro_atribuido, acompanhamento):
    cliente.get(_url(acompanhamento), headers=medico["headers"])
    assert cliente.get(f"{_url(acompanhamento)}/acessos", headers=medico["headers"]).status_code == 200
    assert cliente.get(f"{_url(acompanhamento)}/acessos", headers=parceiro_atribuido["headers"]).status_code == 403


def test_parceiro_ve_a_idade_mas_nao_a_data_de_nascimento(cliente, medico, paciente, parceiro_atribuido, acompanhamento):
    cliente.put(_url(acompanhamento), json=ANAMNESE, headers=medico["headers"])

    hoje = date.today()
    esperada = hoje.year - 1978 - ((hoje.month, hoje.day) < (3, 14))

    para_medico = cliente.get(_url(acompanhamento), headers=medico["headers"]).json()
    assert para_medico["data_nascimento"] == "1978-03-14"
    assert para_medico["idade"] == esperada

    para_paciente = cliente.get(_url(acompanhamento), headers=paciente["headers"]).json()
    assert para_paciente["data_nascimento"] == "1978-03-14"

    # Minimização (LGPD, art. 6º, III): o parceiro vê só a idade, sem a data completa
    para_parceiro = cliente.get(_url(acompanhamento), headers=parceiro_atribuido["headers"]).json()
    assert para_parceiro["data_nascimento"] is None
    assert para_parceiro["idade"] == esperada
    assert para_parceiro["diagnosticos"] == "Hipertensão estágio 1"
