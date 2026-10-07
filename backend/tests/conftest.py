"""Configuração dos testes: SQLite em memória, isolado do MySQL de desenvolvimento."""

import os
import re
from datetime import datetime, timedelta, timezone

# Precisa vir antes de importar a aplicação: as variáveis de ambiente têm
# prioridade sobre o .env, então os testes nunca tocam o banco real.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "segredo-dos-testes-com-tamanho-suficiente-para-hs256"
os.environ["JWT_EXPIRE_MINUTES"] = "480"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["EMAIL_MODE"] = "console"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha
from app.db.base import Base
from app.db.sessao import obter_sessao
from app.main import app
from app.models.usuario import PROFISSAO_MEDICO, TipoUsuario, Usuario
from app.services.email import caixa_de_saida

SENHA = "senha123"


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
    caixa_de_saida.clear()
    with TestClient(app) as cliente_teste:
        yield cliente_teste
    app.dependency_overrides.clear()
    engine.dispose()


def abrir_sessao():
    """Sessão direta no banco do teste, para preparar ou conferir dados sem passar pela API."""
    return next(app.dependency_overrides[obter_sessao]())


def entrar(cliente, email: str, senha: str = SENHA) -> dict:
    """Faz login e devolve {'token', 'usuario', 'headers'}."""
    resposta = cliente.post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    return {
        "token": corpo["token_acesso"],
        "usuario": corpo["usuario"],
        "headers": {"Authorization": f"Bearer {corpo['token_acesso']}"},
    }


def senha_provisoria_enviada(email: str) -> str:
    """Lê, no último email enviado para o endereço, a senha provisória."""
    for mensagem in reversed(caixa_de_saida):
        if mensagem.destinatario == email:
            return re.search(r"Senha provisória: (\S+)", mensagem.corpo).group(1)
    raise AssertionError(f"Nenhum email enviado para {email}")


def criar_conta(cliente, medico: dict, tipo: str, nome: str, email: str, profissao: str | None = None):
    """O médico cria a conta de um paciente ou parceiro. Devolve a resposta HTTP."""
    dados = {"tipo_usuario": tipo, "nome": nome, "email": email}
    if profissao is not None:
        dados["profissao"] = profissao
    return cliente.post("/users", json=dados, headers=medico["headers"])


def criar_conta_ativa(cliente, medico: dict, tipo: str, nome: str, email: str, profissao: str | None = None) -> dict:
    """Cria a conta e faz o primeiro acesso completo: entra com a provisória e define a senha."""
    resposta = criar_conta(cliente, medico, tipo, nome, email, profissao)
    assert resposta.status_code == 201, resposta.text
    provisoria = senha_provisoria_enviada(email)
    primeiro_acesso = entrar(cliente, email, provisoria)
    troca = cliente.post(
        "/auth/change-password",
        json={"senha_atual": provisoria, "nova_senha": SENHA},
        headers=primeiro_acesso["headers"],
    )
    assert troca.status_code == 200, troca.text
    return entrar(cliente, email)


@pytest.fixture
def medico(cliente):
    """O único médico do sistema, criado direto no banco (como faz scripts.criar_medico)."""
    sessao = abrir_sessao()
    sessao.add(
        Usuario(
            tipo_usuario=TipoUsuario.medico,
            nome="Dra. Ana Souza",
            email="ana@clinica.com",
            profissao=PROFISSAO_MEDICO,
            senha_hash=gerar_hash_senha(SENHA),
        )
    )
    sessao.commit()
    sessao.close()
    return entrar(cliente, "ana@clinica.com")


@pytest.fixture
def paciente(cliente, medico):
    return criar_conta_ativa(cliente, medico, "paciente", "Carlos Lima", "carlos@email.com")


@pytest.fixture
def outro_paciente(cliente, medico):
    return criar_conta_ativa(cliente, medico, "paciente", "Maria Alves", "maria@email.com")


@pytest.fixture
def parceiro(cliente, medico):
    return criar_conta_ativa(
        cliente, medico, "parceiro", "Marina Costa", "marina@nutri.com", profissao="Nutricionista"
    )


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
    """Jornada aberta pelo médico para o paciente."""
    return criar_jornada(cliente, medico, paciente)


def atribuir_parceiro(cliente, medico: dict, jornada: dict, parceiro: dict) -> dict:
    resposta = cliente.post(
        f"/journeys/{jornada['id']}/partners",
        json={"parceiro_id": parceiro["usuario"]["id"]},
        headers=medico["headers"],
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def parceiro_atribuido(cliente, medico, parceiro, jornada):
    """Parceiro já atribuído à jornada do paciente."""
    atribuir_parceiro(cliente, medico, jornada, parceiro)
    return parceiro


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

    sessao = abrir_sessao()
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    solicitacao.prazo = datetime.now(timezone.utc).replace(tzinfo=None) + deslocamento
    sessao.commit()
    sessao.close()
