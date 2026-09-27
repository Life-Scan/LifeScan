"""Configuração dos testes: SQLite em memória, isolado do MySQL de desenvolvimento."""

import os
from datetime import datetime, timedelta, timezone

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
from app.core.config import obter_configuracoes
from app.db.base import Base
from app.db.sessao import obter_sessao
from app.main import app


@pytest.fixture
def config_teste(tmp_path, monkeypatch):
    """Configuração da aplicação com a pasta de uploads isolada em um diretório temporário."""
    config = obter_configuracoes()
    monkeypatch.setattr(config, "pasta_uploads_texto", str(tmp_path / "uploads"))
    return config


@pytest.fixture
def cliente(config_teste):
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


def criar_solicitacao(cliente, medico: dict, jornada: dict, tipo: str = "exame", dias: int = 7) -> dict:
    prazo = (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/requests",
        json={"tipo": tipo, "descricao": f"Solicitação de {tipo}", "prazo": prazo},
        headers=medico["headers"],
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def enviar_exame(
    cliente,
    usuario: dict,
    jornada: dict,
    nome: str = "hemograma.pdf",
    conteudo: bytes = b"%PDF-1.4 conteudo de teste",
    solicitacao_id: int | None = None,
):
    dados = {"titulo": "Hemograma completo"}
    if solicitacao_id is not None:
        dados["solicitacao_id"] = str(solicitacao_id)
    return cliente.post(
        f"/journeys/{jornada['id']}/exams",
        data=dados,
        files={"arquivo": (nome, conteudo)},
        headers=usuario["headers"],
    )


def definir_prazo(solicitacao_id: int, deslocamento: timedelta) -> None:
    """Muda o prazo direto no banco (a API não aceita prazos no passado).
    O deslocamento é relativo ao momento atual."""
    from app.models.solicitacao import Solicitacao

    sessao = next(app.dependency_overrides[obter_sessao]())
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    solicitacao.prazo = datetime.now(timezone.utc).replace(tzinfo=None) + deslocamento
    sessao.commit()
    sessao.close()


def enviar_mensagem(cliente, usuario: dict, jornada: dict, conteudo: str) -> dict:
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/messages", data={"conteudo": conteudo}, headers=usuario["headers"]
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()
