"""Engine e sessões do SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import obter_configuracoes

engine = create_engine(obter_configuracoes().url_banco, pool_pre_ping=True)
SessaoLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: abre uma sessão por requisição."""
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
