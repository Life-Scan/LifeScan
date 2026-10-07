"""documentos com categoria e destinatario das solicitacoes

Revision ID: f825a73c9327
Revises: 31fff3580a16
Create Date: 2026-10-07 15:37:45.115891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f825a73c9327'
down_revision: Union[str, Sequence[str], None] = '31fff3580a16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIAS = ('exame', 'laudo', 'plano_alimentar', 'plano_treino', 'orientacao', 'outro')


def upgrade() -> None:
    """Aplica a migração.

    Escrita à mão: a tabela exames é renomeada (e não recriada) para preservar os dados,
    e as solicitações já existentes passam a ter o paciente da jornada como destinatário.
    """
    # exames -> documentos, com categoria
    op.rename_table('exames', 'documentos')
    op.execute('ALTER TABLE documentos RENAME INDEX ix_exames_jornada_id TO ix_documentos_jornada_id')
    op.add_column(
        'documentos',
        sa.Column(
            'categoria',
            sa.Enum(*CATEGORIAS, name='categoria_documento'),
            nullable=False,
            # Os envios anteriores a esta migração eram todos "exames"
            server_default='exame',
        ),
    )
    op.alter_column(
        'documentos',
        'categoria',
        existing_type=sa.Enum(*CATEGORIAS, name='categoria_documento'),
        existing_nullable=False,
        server_default=None,
    )

    # Destinatário das solicitações
    op.add_column('solicitacoes', sa.Column('destinatario_id', sa.Integer(), nullable=True))
    op.execute(
        'UPDATE solicitacoes s JOIN jornadas j ON j.id = s.jornada_id '
        'SET s.destinatario_id = j.paciente_id'
    )
    op.alter_column('solicitacoes', 'destinatario_id', existing_type=sa.Integer(), nullable=False)
    op.create_index(op.f('ix_solicitacoes_destinatario_id'), 'solicitacoes', ['destinatario_id'], unique=False)
    op.create_foreign_key(
        'fk_solicitacoes_destinatario_id_usuarios',
        'solicitacoes',
        'usuarios',
        ['destinatario_id'],
        ['id'],
    )


def downgrade() -> None:
    """Desfaz a migração."""
    op.drop_constraint('fk_solicitacoes_destinatario_id_usuarios', 'solicitacoes', type_='foreignkey')
    op.drop_index(op.f('ix_solicitacoes_destinatario_id'), table_name='solicitacoes')
    op.drop_column('solicitacoes', 'destinatario_id')

    op.drop_column('documentos', 'categoria')
    op.execute('ALTER TABLE documentos RENAME INDEX ix_documentos_jornada_id TO ix_exames_jornada_id')
    op.rename_table('documentos', 'exames')
