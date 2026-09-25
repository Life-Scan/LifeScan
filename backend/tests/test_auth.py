from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import obter_configuracoes
from app.core.seguranca import ALGORITMO_JWT, decodificar_token
from tests.conftest import cadastrar


def test_cadastro_devolve_token_e_usuario(cliente):
    resposta = cliente.post(
        "/auth/register",
        json={"nome": "Dra. Ana", "email": "  Ana@Clinica.com ", "senha": "senha123", "papel": "medico"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_token"] == "bearer"
    assert corpo["usuario"]["email"] == "ana@clinica.com"
    assert corpo["usuario"]["papel"] == "medico"
    assert "senha_hash" not in corpo["usuario"]
    assert corpo["usuario"]["criado_em"].endswith("Z") or "+00:00" in corpo["usuario"]["criado_em"]


def test_senha_gravada_com_bcrypt(cliente):
    from app.db.sessao import obter_sessao
    from app.main import app
    from app.models.usuario import Usuario

    cadastrar(cliente, "Carlos", "carlos@email.com", "paciente", senha="minhasenha")
    sessao = next(app.dependency_overrides[obter_sessao]())
    usuario = sessao.query(Usuario).one()
    assert usuario.senha_hash.startswith("$2b$")
    assert "minhasenha" not in usuario.senha_hash


def test_cadastro_com_email_repetido_retorna_409(cliente, medico):
    resposta = cliente.post(
        "/auth/register",
        json={"nome": "Outra Ana", "email": "ANA@clinica.com", "senha": "senha123", "papel": "paciente"},
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe uma conta com este email."


def test_cadastro_invalido_retorna_422_em_portugues(cliente):
    resposta = cliente.post(
        "/auth/register",
        json={"nome": "A", "email": "nao-e-email", "senha": "123", "papel": "admin"},
    )
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["detail"] == "Dados inválidos."
    campos = {erro["campo"]: erro["mensagem"] for erro in corpo["erros"]}
    assert campos["email"] == "Email inválido."
    assert campos["senha"] == "Deve ter pelo menos 6 caracteres."
    assert "nome" in campos and "papel" in campos


def test_login_com_sucesso(cliente, paciente):
    resposta = cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": "senha123"})
    assert resposta.status_code == 200
    token = resposta.json()["token_acesso"]
    carga = decodificar_token(token)
    assert carga["sub"] == str(paciente["usuario"]["id"])
    assert carga["papel"] == "paciente"


def test_token_expira_em_480_minutos(cliente, medico):
    carga = decodificar_token(medico["token"])
    assert carga["exp"] - carga["iat"] == 480 * 60


def test_login_com_senha_errada_retorna_401(cliente, paciente):
    resposta = cliente.post("/auth/login", json={"email": "carlos@email.com", "senha": "errada"})
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Email ou senha inválidos."


def test_login_com_email_inexistente_retorna_401(cliente):
    resposta = cliente.post("/auth/login", json={"email": "ninguem@email.com", "senha": "senha123"})
    assert resposta.status_code == 401


def test_me_devolve_usuario_logado(cliente, medico):
    resposta = cliente.get("/auth/me", headers=medico["headers"])
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@clinica.com"


def test_me_sem_token_retorna_401(cliente):
    resposta = cliente.get("/auth/me")
    assert resposta.status_code == 401


def test_me_com_token_invalido_retorna_401(cliente):
    resposta = cliente.get("/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Token de acesso inválido."


def test_me_com_token_expirado_retorna_401(cliente, medico):
    passado = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": str(medico["usuario"]["id"]), "papel": "medico", "exp": passado},
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
