"""consentimento lgpd no primeiro acesso

Revision ID: c4f8a09d17b2
Revises: 315ca9f325c7
Create Date: 2026-10-21 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c4f8a09d17b2'
down_revision: Union[str, Sequence[str], None] = '315ca9f325c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_HORA = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')


def upgrade() -> None:
    """Cria a tabela de consentimentos (LGPD, art. 11: registro do aceite do titular).

    Sem linhas iniciais: o consentimento só passa a existir a partir do próximo
    primeiro acesso (ou redefinição de senha), que é quando ele é capturado.
    """
    op.create_table(
        'consentimentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('finalidade', sa.String(length=120), nullable=False),
        sa.Column('versao_termo', sa.String(length=20), nullable=False),
        sa.Column('revogado_em', _HORA, nullable=True),
        sa.Column('ip_aceite', sa.String(length=45), nullable=True),
        sa.Column('concedido_em', _HORA, nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id', ),
    )
    op.create_index(op.f('ix_consentimentos_usuario_id'), 'consentimentos', ['usuario_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consentimentos_usuario_id'), table_name='consentimentos')
    op.drop_table('consentimentos')
