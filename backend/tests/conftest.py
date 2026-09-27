"""Configuração dos testes: SQLite em memória, isolado do MySQL de desenvolvimento."""

import os

# Precisa vir antes de importar a aplicação: as variáveis de ambiente têm
# prioridade sobre o .env, então os testes nunca tocam o banco real.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-dos-testes-com-tamanho-suficiente-para-hs256"
os.environ["JWT_EXPIRE_MINUTES"] = "480"
os.environ["BCRYPT_ROUNDS"] = "4"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db.base import Base
from app.db.sessao import obter_sessao
from app.main import app


@pytest.fixture
def cliente():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessaoTeste = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def obter_sessao_teste():
        sessao = SessaoTeste()
        try:
            yield sessao
        finally:
            sessao.close()

    app.dependency_overrides[obter_sessao] = obter_sessao_teste
    with TestClient(app) as cliente_teste:
        yield cliente_teste
    app.dependency_overrides.clear()
    engine.dispose()


def cadastrar(cliente, nome: str, email: str, papel: str, senha: str = "senha123") -> dict:
    """Cadastra um usuário e devolve {'token', 'usuario', 'headers'}."""
    resposta = cliente.post(
        "/auth/register",
        json={"nome": nome, "email": email, "senha": senha, "papel": papel},
    )
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    return {
        "token": corpo["token_acesso"],
        "usuario": corpo["usuario"],
        "headers": {"Authorization": f"Bearer {corpo['token_acesso']}"},
    }


@pytest.fixture
def medico(cliente):
    return cadastrar(cliente, "Dra. Ana Souza", "ana@clinica.com", "medico")


@pytest.fixture
def paciente(cliente):
    return cadastrar(cliente, "Carlos Lima", "carlos@email.com", "paciente")


@pytest.fixture
def outro_medico(cliente):
    return cadastrar(cliente, "Dr. Bruno Reis", "bruno@clinica.com", "medico")


@pytest.fixture
def outro_paciente(cliente):
    return cadastrar(cliente, "Maria Alves", "maria@email.com", "paciente")


def vincular(cliente, medico: dict, paciente: dict) -> dict:
    resposta = cliente.post(
        "/links", json={"paciente_id": paciente["usuario"]["id"]}, headers=medico["headers"]
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_jornada(cliente, medico: dict, paciente: dict, titulo: str = "Controle da hipertensão") -> dict:
    resposta = cliente.post(
        "/journeys",
        json={"paciente_id": paciente["usuario"]["id"], "titulo": titulo},
        headers=medico["headers"],
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def jornada(cliente, medico, paciente):
    """Médico e paciente vinculados, com uma jornada aberta."""
    vincular(cliente, medico, paciente)
    return criar_jornada(cliente, medico, paciente)
