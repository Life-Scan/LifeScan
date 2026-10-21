from tests.conftest import criar_conta, criar_acompanhamento


def test_medico_abre_acompanhamento_para_paciente(cliente, medico, paciente, acompanhamento):
    assert acompanhamento["titulo"] == "Controle da hipertensão"
    assert acompanhamento["passo_atual"] == "consulta"
    assert acompanhamento["status"] == "ativo"
    assert acompanhamento["paciente"]["id"] == paciente["usuario"]["id"]
    assert acompanhamento["medico"]["id"] == medico["usuario"]["id"]


def test_acompanhamento_so_pode_ser_aberto_para_pacientes(cliente, medico, parceiro):
    for usuario_id in (parceiro["usuario"]["id"], medico["usuario"]["id"], 999):
        resposta = cliente.post(
            "/follow-ups", json={"paciente_id": usuario_id, "titulo": "Tentativa"}, headers=medico["headers"]
        )
        assert resposta.status_code == 404


def test_nao_abre_acompanhamento_para_paciente_desativado(cliente, medico):
    conta = criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com").json()
    cliente.patch(f"/users/{conta['id']}", json={"ativo": False}, headers=medico["headers"])
    resposta = cliente.post(
        "/follow-ups", json={"paciente_id": conta["id"], "titulo": "Tentativa"}, headers=medico["headers"]
    )
    assert resposta.status_code == 409


def test_paciente_tem_apenas_um_acompanhamento(cliente, medico, paciente, acompanhamento):
    resposta = cliente.post(
        "/follow-ups",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": "Segundo acompanhamento"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Este paciente já possui um acompanhamento."


def test_paciente_e_parceiro_nao_abrem_acompanhamento(cliente, paciente, parceiro):
    for usuario in (paciente, parceiro):
        resposta = cliente.post(
            "/follow-ups",
            json={"paciente_id": paciente["usuario"]["id"], "titulo": "Meu acompanhamento"},
            headers=usuario["headers"],
        )
        assert resposta.status_code == 403


def test_medico_e_paciente_acessam_o_acompanhamento(cliente, medico, paciente, acompanhamento):
    for usuario in (medico, paciente):
        resposta = cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=usuario["headers"])
        assert resposta.status_code == 200


def test_terceiros_nao_acessam_o_acompanhamento(cliente, outro_paciente, parceiro, acompanhamento):
    for usuario in (outro_paciente, parceiro):
        resposta = cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=usuario["headers"])
        assert resposta.status_code == 403
        assert resposta.json()["detail"] == "Você não tem acesso a este acompanhamento."


def test_acompanhamento_inexistente_retorna_404(cliente, medico):
    assert cliente.get("/follow-ups/999", headers=medico["headers"]).status_code == 404


def test_sem_token_nao_acessa_acompanhamento(cliente, acompanhamento):
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}").status_code == 401


def test_paciente_desativado_perde_o_acesso_mas_o_medico_nao(cliente, medico, paciente, acompanhamento):
    url_conta = f"/users/{paciente['usuario']['id']}"
    cliente.patch(url_conta, json={"ativo": False}, headers=medico["headers"])

    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=paciente["headers"]).status_code == 401
    # O médico continua com os dados do paciente à mão
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=medico["headers"]).status_code == 200
    assert len(cliente.get("/follow-ups", headers=medico["headers"]).json()) == 1

    cliente.patch(url_conta, json={"ativo": True}, headers=medico["headers"])
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=paciente["headers"]).status_code == 200


def test_listagem_de_acompanhamentos_por_tipo_de_usuario(cliente, medico, paciente, outro_paciente, acompanhamento):
    criar_acompanhamento(cliente, medico, outro_paciente, titulo="Reabilitação do joelho")

    assert len(cliente.get("/follow-ups", headers=medico["headers"]).json()) == 2
    do_paciente = cliente.get("/follow-ups", headers=paciente["headers"]).json()
    assert [j["id"] for j in do_paciente] == [acompanhamento["id"]]


def test_medico_altera_passo_atual(cliente, medico, acompanhamento):
    url = f"/follow-ups/{acompanhamento['id']}/step"
    for passo in ("exame", "retorno", "consulta"):
        resposta = cliente.patch(url, json={"passo_atual": passo}, headers=medico["headers"])
        assert resposta.status_code == 200
        assert resposta.json()["passo_atual"] == passo


def test_passo_invalido_retorna_422(cliente, medico, acompanhamento):
    resposta = cliente.patch(
        f"/follow-ups/{acompanhamento['id']}/step", json={"passo_atual": "cirurgia"}, headers=medico["headers"]
    )
    assert resposta.status_code == 422


def test_paciente_nao_altera_passo_nem_status(cliente, paciente, acompanhamento):
    base = f"/follow-ups/{acompanhamento['id']}"
    assert cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=paciente["headers"]).status_code == 403
    assert cliente.patch(f"{base}/status", json={"status": "encerrado"}, headers=paciente["headers"]).status_code == 403


def test_acompanhamento_encerrado_fica_somente_leitura(cliente, medico, paciente, acompanhamento):
    base = f"/follow-ups/{acompanhamento['id']}"
    resposta = cliente.patch(f"{base}/status", json={"status": "encerrado"}, headers=medico["headers"])
    assert resposta.json()["status"] == "encerrado"

    resposta = cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=medico["headers"])
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Este acompanhamento está encerrado e não pode ser alterado."

    # A leitura continua liberada
    assert cliente.get(base, headers=paciente["headers"]).status_code == 200

    # O médico pode reabrir
    cliente.patch(f"{base}/status", json={"status": "ativo"}, headers=medico["headers"])
    resposta = cliente.patch(f"{base}/step", json={"passo_atual": "exame"}, headers=medico["headers"])
    assert resposta.status_code == 200
