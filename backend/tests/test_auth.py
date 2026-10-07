from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import obter_configuracoes
from app.core.seguranca import ALGORITMO_JWT, decodificar_token
from app.models.usuario import Usuario
from app.services.email import caixa_de_saida
from tests.conftest import SENHA, abrir_sessao, criar_conta, entrar, senha_provisoria_enviada


def _expirar_senha_provisoria(email: str) -> None:
    sessao = abrir_sessao()
    usuario = sessao.query(Usuario).filter_by(email=email).one()
    usuario.senha_provisoria_expira_em = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    sessao.commit()
    sessao.close()


# --- Login e sessão


def test_login_do_medico(cliente, medico):
    usuario = medico["usuario"]
    assert usuario["tipo_usuario"] == "medico"
    assert usuario["profissao"] == "Médico"
    assert usuario["deve_trocar_senha"] is False
    assert "senha_hash" not in usuario
    assert usuario["criado_em"].endswith("Z")

    carga = decodificar_token(medico["token"])
    assert carga["sub"] == str(usuario["id"])
    assert carga["tipo_usuario"] == "medico"
    assert carga["exp"] - carga["iat"] == 480 * 60


def test_login_normaliza_o_email(cliente, medico):
    resposta = cliente.post("/auth/login", json={"email": "  ANA@Clinica.com ", "senha": SENHA})
    assert resposta.status_code == 200


def test_senhas_gravadas_com_bcrypt(cliente, medico, paciente):
    sessao = abrir_sessao()
    for usuario in sessao.query(Usuario).all():
        assert usuario.senha_hash.startswith("$2b$")
        assert SENHA not in usuario.senha_hash
    sessao.close()


def test_login_com_senha_errada_ou_email_inexistente_retorna_401(cliente, medico):
    for dados in (
        {"email": "ana@clinica.com", "senha": "errada"},
        {"email": "ninguem@email.com", "senha": SENHA},
    ):
        resposta = cliente.post("/auth/login", json=dados)
        assert resposta.status_code == 401
        assert resposta.json()["detail"] == "Email ou senha inválidos."


def test_login_invalido_retorna_422_em_portugues(cliente):
    resposta = cliente.post("/auth/login", json={"email": "nao-e-email"})
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["detail"] == "Dados inválidos."
    campos = {erro["campo"]: erro["mensagem"] for erro in corpo["erros"]}
    assert campos["email"] == "Email inválido."
    assert campos["senha"] == "Campo obrigatório."


def test_me_devolve_usuario_logado(cliente, medico):
    resposta = cliente.get("/auth/me", headers=medico["headers"])
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@clinica.com"


def test_me_sem_token_ou_com_token_invalido_retorna_401(cliente):
    assert cliente.get("/auth/me").status_code == 401
    resposta = cliente.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Token de acesso inválido."


def test_me_com_token_expirado_retorna_401(cliente, medico):
    passado = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": str(medico["usuario"]["id"]), "tipo_usuario": "medico", "exp": passado},
        obter_configuracoes().segredo_jwt,
        algorithm=ALGORITMO_JWT,
    )
    resposta = cliente.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Sessão expirada. Faça login novamente."


def test_cors_permite_origem_configurada(cliente):
    resposta = cliente.options(
        "/auth/login",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert resposta.headers.get("access-control-allow-origin") == "http://localhost:5173"


# --- Primeiro acesso com a senha provisória


def test_primeiro_acesso_exige_troca_de_senha(cliente, medico):
    criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com")
    provisoria = senha_provisoria_enviada("carlos@email.com")

    acesso = entrar(cliente, "carlos@email.com", provisoria)
    assert acesso["usuario"]["deve_trocar_senha"] is True

    # Enquanto não trocar a senha, só /auth/me e a própria troca funcionam
    assert cliente.get("/auth/me", headers=acesso["headers"]).status_code == 200
    for rota in ("/journeys", "/dashboard/pending"):
        bloqueio = cliente.get(rota, headers=acesso["headers"])
        assert bloqueio.status_code == 403
        assert bloqueio.json()["detail"] == "Defina uma nova senha para continuar usando o sistema."

    troca = cliente.post(
        "/auth/set-password", json={"nova_senha": "minha-senha-nova"}, headers=acesso["headers"]
    )
    assert troca.status_code == 200
    assert troca.json()["deve_trocar_senha"] is False

    # O mesmo token passa a funcionar, e a provisória deixa de valer
    assert cliente.get("/journeys", headers=acesso["headers"]).status_code == 200
    assert cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": provisoria}).status_code == 401
    assert entrar(cliente, "carlos@email.com", "minha-senha-nova")["usuario"]["deve_trocar_senha"] is False


def test_senha_provisoria_expirada_nao_permite_login(cliente, medico):
    criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com")
    provisoria = senha_provisoria_enviada("carlos@email.com")
    _expirar_senha_provisoria("carlos@email.com")

    resposta = cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": provisoria})
    assert resposta.status_code == 401
    assert "expirou" in resposta.json()["detail"]


# --- Definição de senha


def test_nao_existe_troca_de_senha_fora_do_primeiro_acesso(cliente, medico, paciente):
    """Quem já definiu a senha não tem como trocá-la por aqui: usa "esqueci minha senha"."""
    for usuario in (medico, paciente):
        resposta = cliente.post("/auth/set-password", json={"nova_senha": "outra-senha"}, headers=usuario["headers"])
        assert resposta.status_code == 403
        assert "Esqueci minha senha" in resposta.json()["detail"]
    # A senha continua a mesma, e a rota antiga não existe mais
    entrar(cliente, "carlos@email.com", SENHA)
    antiga = cliente.post(
        "/auth/change-password",
        json={"senha_atual": SENHA, "nova_senha": "outra-senha"},
        headers=paciente["headers"],
    )
    assert antiga.status_code == 404


def test_validacoes_ao_definir_a_senha(cliente, medico):
    criar_conta(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com")
    provisoria = senha_provisoria_enviada("carlos@email.com")
    headers = entrar(cliente, "carlos@email.com", provisoria)["headers"]
    url = "/auth/set-password"

    curta = cliente.post(url, json={"nova_senha": "123"}, headers=headers)
    assert curta.status_code == 422
    assert curta.json()["erros"][0]["mensagem"] == "Deve ter pelo menos 6 caracteres."

    igual = cliente.post(url, json={"nova_senha": provisoria}, headers=headers)
    assert igual.status_code == 422
    assert igual.json()["detail"] == "Escolha uma senha diferente da senha provisória."

    assert cliente.post(url, json={"nova_senha": "senha-valida"}).status_code == 401
    assert cliente.post(url, json={"nova_senha": "senha-valida"}, headers=headers).status_code == 200


# --- Esqueci minha senha


def test_esqueci_minha_senha_envia_provisoria_e_mantem_a_senha_atual(cliente, paciente):
    caixa_de_saida.clear()
    resposta = cliente.post("/auth/forgot-password", json={"email": "carlos@email.com"})
    assert resposta.status_code == 200

    email = caixa_de_saida[-1]
    assert email.assunto == "Redefinição de senha do LifeScan"
    assert "vale por 60 minutos" in email.corpo

    # A senha atual continua funcionando (ninguém consegue trancar a conta de outra pessoa)
    assert entrar(cliente, "carlos@email.com")["usuario"]["deve_trocar_senha"] is False

    provisoria = senha_provisoria_enviada("carlos@email.com")
    acesso = entrar(cliente, "carlos@email.com", provisoria)
    assert acesso["usuario"]["deve_trocar_senha"] is True
    cliente.post("/auth/set-password", json={"nova_senha": "senha-recuperada"}, headers=acesso["headers"])
    entrar(cliente, "carlos@email.com", "senha-recuperada")
    assert cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": SENHA}).status_code == 401


def test_esqueci_minha_senha_nao_revela_se_a_conta_existe(cliente, medico, paciente):
    cliente.patch(f"/users/{paciente['usuario']['id']}", json={"ativo": False}, headers=medico["headers"])
    caixa_de_saida.clear()

    respostas = [
        cliente.post("/auth/forgot-password", json={"email": email})
        for email in ("ana@clinica.com", "ninguem@email.com", "carlos@email.com")
    ]
    assert {r.status_code for r in respostas} == {200}
    assert len({r.json()["mensagem"] for r in respostas}) == 1
    # Só a conta existente e ativa recebeu email
    assert [e.destinatario for e in caixa_de_saida] == ["ana@clinica.com"]
