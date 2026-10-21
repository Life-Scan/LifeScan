"""trilha de auditoria de acesso a anamnese

Revision ID: d5b9e3f07c11
Revises: c4f8a09d17b2
Create Date: 2026-10-21 18:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd5b9e3f07c11'
down_revision: Union[str, Sequence[str], None] = 'c4f8a09d17b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_HORA = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')


def upgrade() -> None:
    """Cria a tabela de registros de acesso (LGPD, arts. 37 e 18, V).

    Sem chave estrangeira para usuarios: o log é pseudônimo (id + tipo de usuário)
    e precisa sobreviver à exclusão da conta do titular.
    """
    op.create_table(
        'registros_acesso',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('tipo_usuario', sa.String(length=12), nullable=False),
        sa.Column('acompanhamento_id', sa.Integer(), nullable=False),
        sa.Column('acao', sa.String(length=10), nullable=False),
        sa.Column('ocorreu_em', _HORA, nullable=False),
        sa.PrimaryKeyConstraint('id', ),
    )
    op.create_index(op.f('ix_registros_acesso_usuario_id'), 'registros_acesso', ['usuario_id'], unique=False)
    op.create_index(
        op.f('ix_registros_acesso_acompanhamento_id'), 'registros_acesso', ['acompanhamento_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_registros_acesso_acompanhamento_id'), table_name='registros_acesso')
    op.drop_index(op.f('ix_registros_acesso_usuario_id'), table_name='registros_acesso')
    op.drop_table('registros_acesso')
