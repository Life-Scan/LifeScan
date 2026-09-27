"""datas com microssegundos

Revision ID: 984e873d5e83
Revises: 8e44718c7b29
Create Date: 2026-09-27 17:43:54.177160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '984e873d5e83'
down_revision: Union[str, Sequence[str], None] = '8e44718c7b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabela, coluna, aceita nulo)
COLUNAS_DATA = [
    ("usuarios", "criado_em", False),
    ("vinculos_medico_paciente", "criado_em", False),
    ("jornadas", "criado_em", False),
    ("jornadas", "atualizado_em", False),
    ("consultas", "data", False),
    ("consultas", "criado_em", False),
    ("solicitacoes", "prazo", False),
    ("solicitacoes", "atendida_em", True),
    ("solicitacoes", "criado_em", False),
    ("arquivos", "criado_em", False),
    ("exames", "revisado_em", True),
    ("exames", "criado_em", False),
    ("mensagens", "criado_em", False),
]


def _alterar_precisao(de: int, para: int) -> None:
    # Só o MySQL tem precisão configurável no DATETIME
    if op.get_bind().dialect.name != "mysql":
        return
    for tabela, coluna, nulo in COLUNAS_DATA:
        op.alter_column(
            tabela,
            coluna,
            existing_type=mysql.DATETIME(fsp=de),
            type_=mysql.DATETIME(fsp=para),
            existing_nullable=nulo,
        )


def upgrade() -> None:
    """Aplica a migração: datas passam a guardar microssegundos."""
    _alterar_precisao(0, 6)


def downgrade() -> None:
    """Desfaz a migração."""
    _alterar_precisao(6, 0)
