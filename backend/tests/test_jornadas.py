from tests.conftest import criar_jornada, vincular


def test_medico_abre_jornada_para_paciente_vinculado(cliente, medico, paciente, jornada):
    assert jornada["titulo"] == "Controle da hipertensão"
    assert jornada["passo_atual"] == "consulta"
    assert jornada["status"] == "ativa"
    assert jornada["paciente"]["id"] == paciente["usuario"]["id"]

    vinculos = cliente.get("/links", headers=medico["headers"]).json()
    assert vinculos[0]["jornada_id"] == jornada["id"]


def test_nao_abre_jornada_sem_vinculo(cliente, medico, paciente):
    resposta = cliente.post(
        "/journeys",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": "Sem vínculo"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 403


def test_nao_abre_jornada_para_paciente_de_outro_medico(cliente, medico, outro_medico, paciente):
    vincular(cliente, medico, paciente)
    resposta = cliente.post(
        "/journeys",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": "Tentativa"},
        headers=outro_medico["headers"],
    )
    assert resposta.status_code == 403


def test_paciente_tem_apenas_uma_jornada(cliente, medico, paciente, jornada):
    resposta = cliente.post(
        "/journeys",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": "Segunda jornada"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Este paciente já possui uma jornada."


def test_paciente_nao_pode_abrir_jornada(cliente, medico, paciente):
    vincular(cliente, medico, paciente)
    resposta = cliente.post(
        "/journeys",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": "Minha jornada"},
        headers=paciente["headers"],
    )
    assert resposta.status_code == 403


def test_medico_e_paciente_acessam_a_jornada(cliente, medico, paciente, jornada):
    for usuario in (medico, paciente):
        resposta = cliente.get(f"/journeys/{jornada['id']}", headers=usuario["headers"])
        assert resposta.status_code == 200


def test_terceiros_nao_acessam_a_jornada(cliente, outro_medico, outro_paciente, jornada):
    for usuario in (outro_medico, outro_paciente):
        resposta = cliente.get(f"/journeys/{jornada['id']}", headers=usuario["headers"])
        assert resposta.status_code == 403
        assert resposta.json()["detail"] == "Você não tem acesso a esta jornada."


def test_jornada_inexistente_retorna_404(cliente, medico):
    assert cliente.get("/journeys/999", headers=medico["headers"]).status_code == 404


def test_sem_token_nao_acessa_jornada(cliente, jornada):
    assert cliente.get(f"/journeys/{jornada['id']}").status_code == 401


def test_vinculo_inativo_bloqueia_a_jornada(cliente, medico, paciente, jornada):
    vinculo_id = cliente.get("/links", headers=medico["headers"]).json()[0]["id"]
    cliente.patch(f"/links/{vinculo_id}", json={"ativo": False}, headers=medico["headers"])

    for usuario in (medico, paciente):
        resposta = cliente.get(f"/journeys/{jornada['id']}", headers=usuario["headers"])
        assert resposta.status_code == 403
        assert "vínculo" in resposta.json()["detail"]
        assert cliente.get("/journeys", headers=usuario["headers"]).json() == []

    cliente.patch(f"/links/{vinculo_id}", json={"ativo": True}, headers=medico["headers"])
    assert cliente.get(f"/journeys/{jornada['id']}", headers=paciente["headers"]).status_code == 200


def test_listagem_de_jornadas_por_papel(cliente, medico, paciente, outro_paciente, jornada):
    vincular(cliente, medico, outro_paciente)
    criar_jornada(cliente, medico, outro_paciente, titulo="Reabilitação do joelho")

    assert len(cliente.get("/journeys", headers=medico["headers"]).json()) == 2
    do_paciente = cliente.get("/journeys", headers=paciente["headers"]).json()
    assert [j["id"] for j in do_paciente] == [jornada["id"]]


def test_medico_altera_passo_atual(cliente, medico, jornada):
    url = f"/journeys/{jornada['id']}/step"
    for passo in ("exame", "retorno", "consulta"):
        resposta = cliente.patch(url, json={"passo_atual": passo}, headers=medico["headers"])
        assert resposta.status_code == 200
        assert resposta.json()["passo_atual"] == passo


def test_passo_invalido_retorna_422(cliente, medico, jornada):
    resposta = cliente.patch(
        f"/journeys/{jornada['id']}/step", json={"passo_atual": "cirurgia"}, headers=medico["headers"]
    )
    assert resposta.status_code == 422


def test_paciente_nao_altera_passo_nem_status(cliente, paciente, jornada):
    base = f"/journeys/{jornada['id']}"
    assert cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=paciente["headers"]).status_code == 403
    assert cliente.patch(f"{base}/status", json={"status": "encerrada"}, headers=paciente["headers"]).status_code == 403


def test_jornada_encerrada_fica_somente_leitura(cliente, medico, paciente, jornada):
    base = f"/journeys/{jornada['id']}"
    resposta = cliente.patch(f"{base}/status", json={"status": "encerrada"}, headers=medico["headers"])
    assert resposta.json()["status"] == "encerrada"

    resposta = cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=medico["headers"])
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Esta jornada está encerrada e não pode ser alterada."

    # A leitura continua liberada
    assert cliente.get(base, headers=paciente["headers"]).status_code == 200

    # O médico pode reabrir
    cliente.patch(f"{base}/status", json={"status": "ativa"}, headers=medico["headers"])
    resposta = cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=medico["headers"])
    assert resposta.status_code == 200
