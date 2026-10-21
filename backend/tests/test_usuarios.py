"""Contas de pacientes e parceiros criadas pelo médico."""

import pytest

from app.services.email import caixa_de_saida
from tests.conftest import SENHA, criar_conta, criar_conta_ativa, entrar, senha_provisoria_enviada


def test_excluir_paciente_desativado_libera_email(cliente, medico, paciente):
    usuario_id = paciente['usuario']['id']
    url = f'/users/{usuario_id}'
    assert cliente.patch(url, json={'ativo': False}, headers=medico['headers']).status_code == 200
    assert cliente.delete(url, headers=medico['headers']).status_code == 200
    contas = cliente.get('/users', headers=medico['headers']).json()
    assert all(conta['id'] != usuario_id for conta in contas)
    assert cliente.get('/auth/me', headers=paciente['headers']).status_code == 401
    assert criar_conta(cliente, medico, 'paciente', 'Novo paciente', paciente['usuario']['email']).status_code == 201


def test_exclusao_exige_medico_e_paciente_desativado(cliente, medico, paciente, parceiro):
    url = f"/users/{paciente['usuario']['id']}"
    assert cliente.delete(url).status_code == 401
    for acesso in (paciente, parceiro):
        assert cliente.delete(url, headers=acesso['headers']).status_code == 403
    assert cliente.delete(url, headers=medico['headers']).status_code == 409
    assert cliente.delete(f"/users/{medico['usuario']['id']}", headers=medico['headers']).status_code == 404
    parceiro_url = f"/users/{parceiro['usuario']['id']}"
    cliente.patch(parceiro_url, json={'ativo': False}, headers=medico['headers'])
    assert cliente.delete(parceiro_url, headers=medico['headers']).status_code == 409
    assert cliente.delete('/users/999999', headers=medico['headers']).status_code == 404


def test_exclusao_preserva_acompanhamento_e_conta(cliente, medico, paciente, acompanhamento):
    url = f"/users/{paciente['usuario']['id']}"
    cliente.patch(url, json={'ativo': False}, headers=medico['headers'])
    resposta = cliente.delete(url, headers=medico['headers'])
    assert resposta.status_code == 409
    assert 'histórico' in resposta.json()['detail']
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=medico['headers']).status_code == 200
    assert cliente.patch(url, json={'ativo': True}, headers=medico['headers']).status_code == 200
    assert entrar(cliente, paciente['usuario']['email'])['usuario']['id'] == paciente['usuario']['id']


def test_nao_existe_cadastro_publico(cliente):
    resposta = cliente.post(
        "/auth/register",
        json={"nome": "Fulano", "email": "fulano@email.com", "senha": SENHA, "papel": "paciente"},
    )
    assert resposta.status_code == 404


def test_medico_cria_conta_de_paciente_e_email_e_enviado(cliente, medico):
    resposta = criar_conta(cliente, medico, "paciente", "Carlos Lima", " Carlos@Email.com ")
    assert resposta.status_code == 201, resposta.text
    conta = resposta.json()
    assert conta["tipo_usuario"] == "paciente"
    assert conta["email"] == "carlos@email.com"
    assert conta["profissao"] is None
    assert conta["ativo"] is True
    assert conta["primeiro_acesso_pendente"] is True
    assert conta["ultimo_login_em"] is None
    assert conta["acompanhamento_id"] is None
    assert "senha" not in " ".join(conta)

    email = caixa_de_saida[-1]
    assert email.destinatario == "carlos@email.com"
    assert email.assunto == "Seu acesso ao LifeScan"
    assert "Carlos Lima" in email.corpo
    assert "vale por 7 dias" in email.corpo
    assert len(senha_provisoria_enviada("carlos@email.com")) == 10


def test_paciente_nao_precisa_de_profissao_e_ela_e_ignorada(cliente, medico):
    resposta = criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com", profissao="Engenheiro")
    assert resposta.status_code == 201
    assert resposta.json()["profissao"] is None


def test_parceiro_exige_profissao(cliente, medico):
    sem_profissao = criar_conta(cliente, medico, "parceiro", "Marina Costa", "marina@nutri.com")
    assert sem_profissao.status_code == 422
    assert "Informe a profissão do parceiro." in str(sem_profissao.json())

    com_profissao = criar_conta(cliente, medico, "parceiro", "Marina Costa", "marina@nutri.com", "Nutricionista")
    assert com_profissao.status_code == 201
    assert com_profissao.json()["profissao"] == "Nutricionista"


def test_nao_e_possivel_criar_outro_medico(cliente, medico):
    resposta = criar_conta(cliente, medico, "medico", "Dr. Bruno", "bruno@clinica.com", "Médico")
    assert resposta.status_code == 422


def test_email_repetido_retorna_409(cliente, medico, paciente):
    resposta = criar_conta(cliente, medico, "parceiro", "Outro", "carlos@email.com", "Fisioterapeuta")
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe uma conta com este email."


def test_so_o_medico_administra_contas(cliente, paciente, parceiro):
    for usuario in (paciente, parceiro):
        assert criar_conta(cliente, usuario, "paciente", "Novo", "novo@email.com").status_code == 403
        assert cliente.get("/users", headers=usuario["headers"]).status_code == 403
    assert cliente.get("/users").status_code == 401


def test_listagem_e_filtro_por_tipo(cliente, medico, paciente, outro_paciente, parceiro):
    todas = cliente.get("/users", headers=medico["headers"]).json()
    assert [c["nome"] for c in todas] == ["Carlos Lima", "Maria Alves", "Marina Costa"]
    # O próprio médico não aparece entre as contas administradas
    assert all(c["tipo_usuario"] != "medico" for c in todas)

    parceiros = cliente.get("/users", params={"tipo": "parceiro"}, headers=medico["headers"]).json()
    assert [c["email"] for c in parceiros] == ["marina@nutri.com"]


def test_listagem_mostra_primeiro_acesso_e_acompanhamento(cliente, medico, paciente, acompanhamento):
    criar_conta(cliente, medico, "paciente", "Maria Alves", "maria@email.com")
    contas = {c["email"]: c for c in cliente.get("/users", headers=medico["headers"]).json()}

    assert contas["carlos@email.com"]["primeiro_acesso_pendente"] is False
    assert contas["carlos@email.com"]["ultimo_login_em"] is not None
    assert contas["carlos@email.com"]["acompanhamento_id"] == acompanhamento["id"]
    assert contas["maria@email.com"]["primeiro_acesso_pendente"] is True
    assert contas["maria@email.com"]["acompanhamento_id"] is None


def test_medico_atualiza_nome_e_profissao(cliente, medico, parceiro):
    resposta = cliente.patch(
        f"/users/{parceiro['usuario']['id']}",
        json={"nome": "Marina C. Silva", "profissao": "Nutricionista esportiva"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Marina C. Silva"
    assert resposta.json()["profissao"] == "Nutricionista esportiva"


def test_corrigir_paciente_preserva_conta_acompanhamento_e_senha(cliente, medico, paciente, acompanhamento):
    usuario_id = paciente["usuario"]["id"]
    resposta = cliente.patch(
        f"/users/{usuario_id}",
        json={"nome": "  Carlos Corrigido  ", "email": " Carlos.Novo@Email.com "},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200, resposta.text
    conta = resposta.json()
    assert conta["id"] == usuario_id
    assert conta["nome"] == "Carlos Corrigido"
    assert conta["email"] == "carlos.novo@email.com"
    assert conta["acompanhamento_id"] == acompanhamento["id"]
    assert conta["ativo"] is True
    assert cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": SENHA}).status_code == 401
    assert entrar(cliente, "carlos.novo@email.com")["usuario"]["id"] == usuario_id
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=paciente["headers"]).status_code == 200


@pytest.mark.parametrize("email", [" MARIA@EMAIL.COM ", "ana@clinica.com"])
def test_edicao_recusa_email_de_outra_conta_sem_alterar_nome(cliente, medico, paciente, outro_paciente, email):
    resposta = cliente.patch(
        f"/users/{paciente['usuario']['id']}",
        json={"nome": "Não deve salvar", "email": email},
        headers=medico["headers"],
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe uma conta com este email."
    atual = cliente.get("/auth/me", headers=paciente["headers"]).json()
    assert atual["nome"] == "Carlos Lima"
    assert atual["email"] == "carlos@email.com"


def test_edicao_aceita_email_da_propria_conta(cliente, medico, paciente):
    resposta = cliente.patch(
        f"/users/{paciente['usuario']['id']}",
        json={"nome": "Carlos Corrigido", "email": "CARLOS@EMAIL.COM"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carlos Corrigido"


@pytest.mark.parametrize("dados", [{"email": "email-invalido"}, {"email": ""}, {"nome": " "}])
def test_edicao_valida_nome_e_email(cliente, medico, paciente, dados):
    resposta = cliente.patch(f"/users/{paciente['usuario']['id']}", json=dados, headers=medico["headers"])
    assert resposta.status_code == 422


def test_so_medico_pode_corrigir_dados(cliente, paciente, parceiro):
    url = f"/users/{paciente['usuario']['id']}"
    for usuario in (paciente, parceiro):
        assert cliente.patch(url, json={"email": "novo@email.com"}, headers=usuario["headers"]).status_code == 403
    assert cliente.patch(url, json={"email": "novo@email.com"}).status_code == 401


def test_corrigir_email_e_reenviar_acesso_para_novo_endereco(cliente, medico):
    conta = criar_conta(cliente, medico, "paciente", "Paciente Teste", "errado@email.com").json()
    total_emails = len(caixa_de_saida)
    resposta = cliente.patch(
        f"/users/{conta['id']}", json={"email": "correto@email.com"}, headers=medico["headers"]
    )
    assert resposta.status_code == 200
    assert len(caixa_de_saida) == total_emails
    assert cliente.post(f"/users/{conta['id']}/resend-access", headers=medico["headers"]).status_code == 200
    assert caixa_de_saida[-1].destinatario == "correto@email.com"
    senha = senha_provisoria_enviada("correto@email.com")
    assert entrar(cliente, "correto@email.com", senha)["usuario"]["id"] == conta["id"]


def test_conta_desativada_perde_o_acesso_e_pode_ser_reativada(cliente, medico, paciente):
    url = f"/users/{paciente['usuario']['id']}"
    assert cliente.patch(url, json={"ativo": False}, headers=medico["headers"]).json()["ativo"] is False

    # O token antigo deixa de valer e o login é recusado
    assert cliente.get("/auth/me", headers=paciente["headers"]).status_code == 401
    login = cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": SENHA})
    assert login.status_code == 403
    assert "desativada" in login.json()["detail"]

    cliente.patch(url, json={"ativo": True}, headers=medico["headers"])
    assert cliente.get("/auth/me", headers=paciente["headers"]).status_code == 200


def test_conta_do_medico_nao_e_administrada_por_esta_rota(cliente, medico):
    url = f"/users/{medico['usuario']['id']}"
    assert cliente.patch(url, json={"ativo": False}, headers=medico["headers"]).status_code == 404
    assert cliente.post(f"{url}/resend-access", headers=medico["headers"]).status_code == 404


def test_reenviar_acesso_gera_nova_senha_provisoria(cliente, medico):
    conta = criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com").json()
    primeira = senha_provisoria_enviada("carlos@email.com")

    resposta = cliente.post(f"/users/{conta['id']}/resend-access", headers=medico["headers"])
    assert resposta.status_code == 200
    segunda = senha_provisoria_enviada("carlos@email.com")
    assert segunda != primeira

    # Só a senha mais recente funciona
    assert cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": primeira}).status_code == 401
    assert entrar(cliente, "carlos@email.com", segunda)["usuario"]["deve_trocar_senha"] is True


def test_nao_reenvia_acesso_para_conta_desativada(cliente, medico, paciente):
    url = f"/users/{paciente['usuario']['id']}"
    cliente.patch(url, json={"ativo": False}, headers=medico["headers"])
    assert cliente.post(f"{url}/resend-access", headers=medico["headers"]).status_code == 409


def test_medico_trabalha_na_acompanhamento_antes_do_primeiro_acesso_do_paciente(cliente, medico):
    """O sistema não depende de o paciente entrar: o médico já centraliza os dados."""
    conta = criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com").json()
    assert conta["primeiro_acesso_pendente"] is True

    acompanhamento = cliente.post(
        "/follow-ups",
        json={"paciente_id": conta["id"], "titulo": "Controle da hipertensão"},
        headers=medico["headers"],
    )
    assert acompanhamento.status_code == 201
    acompanhamento_id = acompanhamento.json()["id"]

    consulta = cliente.post(
        f"/follow-ups/{acompanhamento_id}/consultations",
        json={"tipo": "consulta", "data": "2026-10-01T14:00:00Z", "anotacoes": "Primeira consulta."},
        headers=medico["headers"],
    )
    assert consulta.status_code == 201

    exame = cliente.post(
        f"/follow-ups/{acompanhamento_id}/documents",
        data={"titulo": "Exame trazido na consulta"},
        files={"arquivo": ("exame.pdf", b"%PDF")},
        headers=medico["headers"],
    )
    assert exame.status_code == 201

    # Quando o paciente finalmente entra, encontra tudo lá
    paciente = criar_conta_ativa_existente(cliente)
    eventos = cliente.get(f"/follow-ups/{acompanhamento_id}/timeline", headers=paciente["headers"]).json()
    assert [e["tipo"] for e in eventos] == ["consulta", "documento"]


def criar_conta_ativa_existente(cliente) -> dict:
    """Primeiro acesso de uma conta já criada: entra com a provisória e define a senha."""
    provisoria = senha_provisoria_enviada("carlos@email.com")
    acesso = entrar(cliente, "carlos@email.com", provisoria)
    cliente.post("/auth/set-password", json={"nova_senha": SENHA}, headers=acesso["headers"])
    return entrar(cliente, "carlos@email.com")


def test_painel_do_parceiro(cliente, parceiro, acompanhamento):
    assert cliente.get("/follow-ups", headers=parceiro["headers"]).json() == []
    assert cliente.get(f"/follow-ups/{acompanhamento['id']}", headers=parceiro["headers"]).status_code == 403
    painel = cliente.get("/dashboard/pending", headers=parceiro["headers"]).json()
    assert painel == {"tipo_usuario": "parceiro", "solicitacoes_pendentes": []}


def test_conta_ativa_helper(cliente, medico):
    usuario = criar_conta_ativa(cliente, medico, "paciente", "Maria Alves", "maria@email.com")
    assert usuario["usuario"]["deve_trocar_senha"] is False


def test_medico_atualiza_email(cliente, medico, paciente):
    resposta = cliente.patch(
        f"/users/{paciente['usuario']['id']}",
        json={"email": "carlos.novo@email.com"},
        headers=medico["headers"],
    )
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "carlos.novo@email.com"



def test_medico_atualiza_email_duplicado(cliente, medico, paciente, parceiro):
    resposta = cliente.patch(
        f"/users/{paciente['usuario']['id']}",
        json={"email": parceiro["usuario"]["email"]},
        headers=medico["headers"],
    )
    assert resposta.status_code == 409
    assert "Já existe uma conta com este email" in resposta.json()["detail"]
