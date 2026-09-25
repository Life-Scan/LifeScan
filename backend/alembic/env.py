"""Ambiente do Alembic: usa a URL do .env e o metadata dos modelos da aplicação."""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app import models  # noqa: F401  (registra todos os modelos no metadata)
from app.core.config import obter_configuracoes
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
url_banco = obter_configuracoes().url_banco


def executar_migracoes_offline() -> None:
    """Gera o SQL das migrações sem conectar ao banco (alembic upgrade head --sql)."""
    context.configure(
        url=url_banco,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def executar_migracoes_online() -> None:
    engine = create_engine(url_banco, poolclass=pool.NullPool)
    with engine.connect() as conexao:
        context.configure(connection=conexao, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    executar_migracoes_offline()
else:
    executar_migracoes_online()
