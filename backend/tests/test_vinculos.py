from tests.conftest import vincular


def test_medico_busca_paciente_por_email(cliente, medico, paciente):
    resposta = cliente.get(
        "/patients/search", params={"email": " CARLOS@email.com "}, headers=medico["headers"]
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id"] == paciente["usuario"]["id"]
    assert corpo["vinculado_a_mim"] is False
    assert corpo["vinculado_a_outro_medico"] is False


def test_busca_nao_encontra_medicos_nem_emails_inexistentes(cliente, medico, outro_medico):
    for email in ("bruno@clinica.com", "ninguem@email.com"):
        resposta = cliente.get("/patients/search", params={"email": email}, headers=medico["headers"])
        assert resposta.status_code == 404
        assert resposta.json()["detail"] == "Nenhum paciente encontrado com este email."


def test_paciente_nao_pode_buscar_pacientes(cliente, paciente, outro_paciente):
    resposta = cliente.get(
        "/patients/search", params={"email": "maria@email.com"}, headers=paciente["headers"]
    )
    assert resposta.status_code == 403


def test_medico_vincula_paciente(cliente, medico, paciente):
    vinculo = vincular(cliente, medico, paciente)
    assert vinculo["ativo"] is True
    assert vinculo["medico"]["id"] == medico["usuario"]["id"]
    assert vinculo["paciente"]["id"] == paciente["usuario"]["id"]
    assert vinculo["jornada_id"] is None

    busca = cliente.get(
        "/patients/search", params={"email": "carlos@email.com"}, headers=medico["headers"]
    ).json()
    assert busca["vinculado_a_mim"] is True


def test_vinculo_repetido_retorna_409(cliente, medico, paciente):
    vincular(cliente, medico, paciente)
    resposta = cliente.post(
        "/links", json={"paciente_id": paciente["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Este paciente já está vinculado a você."


def test_paciente_so_pode_ter_um_medico(cliente, medico, outro_medico, paciente):
    vincular(cliente, medico, paciente)
    resposta = cliente.post(
        "/links", json={"paciente_id": paciente["usuario"]["id"]}, headers=outro_medico["headers"]
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Este paciente já está vinculado a outro médico."


def test_nao_vincula_medico_como_paciente(cliente, medico, outro_medico):
    resposta = cliente.post(
        "/links", json={"paciente_id": outro_medico["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 404


def test_paciente_nao_pode_criar_vinculo(cliente, paciente, outro_paciente):
    resposta = cliente.post(
        "/links", json={"paciente_id": outro_paciente["usuario"]["id"]}, headers=paciente["headers"]
    )
    assert resposta.status_code == 403


def test_listagem_de_vinculos_por_papel(cliente, medico, paciente, outro_paciente):
    vincular(cliente, medico, paciente)
    vincular(cliente, medico, outro_paciente)

    do_medico = cliente.get("/links", headers=medico["headers"]).json()
    assert len(do_medico) == 2

    do_paciente = cliente.get("/links", headers=paciente["headers"]).json()
    assert len(do_paciente) == 1
    assert do_paciente[0]["medico"]["nome"] == "Dra. Ana Souza"


def test_somente_o_medico_do_vinculo_pode_desativar(cliente, medico, outro_medico, paciente):
    vinculo = vincular(cliente, medico, paciente)
    url = f"/links/{vinculo['id']}"

    assert cliente.patch(url, json={"ativo": False}, headers=outro_medico["headers"]).status_code == 403
    assert cliente.patch(url, json={"ativo": False}, headers=paciente["headers"]).status_code == 403

    resposta = cliente.patch(url, json={"ativo": False}, headers=medico["headers"])
    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
