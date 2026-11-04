"""agenda de consultas

Revision ID: 8b1d4c2e7a90
Revises: 633f73b9fc9d
Create Date: 2026-11-04 17:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8b1d4c2e7a90'
down_revision: Union[str, Sequence[str], None] = '633f73b9fc9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_HORA = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')


def upgrade() -> None:
    """Cria a tabela de consultas agendadas (agenda do médico)."""
    op.create_table(
        'agendamentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('acompanhamento_id', sa.Integer(), nullable=False),
        sa.Column('data_hora', _HORA, nullable=False),
        sa.Column(
            'status',
            sa.Enum('agendada', 'realizada', 'cancelada', 'faltou', name='status_agendamento'),
            nullable=False,
        ),
        sa.Column('observacao', sa.String(length=255), nullable=True),
        sa.Column('criado_por_id', sa.Integer(), nullable=False),
        sa.Column('criado_em', _HORA, nullable=False),
        sa.Column('atualizado_em', _HORA, nullable=False),
        sa.ForeignKeyConstraint(['acompanhamento_id'], ['acompanhamentos.id'], ),
        sa.ForeignKeyConstraint(['criado_por_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agendamentos_acompanhamento_id'), 'agendamentos', ['acompanhamento_id'], unique=False)
    op.create_index(op.f('ix_agendamentos_data_hora'), 'agendamentos', ['data_hora'], unique=False)


def downgrade() -> None:
    """Desfaz a migração."""
    op.drop_index(op.f('ix_agendamentos_data_hora'), table_name='agendamentos')
    op.drop_index(op.f('ix_agendamentos_acompanhamento_id'), table_name='agendamentos')
    op.drop_table('agendamentos')
