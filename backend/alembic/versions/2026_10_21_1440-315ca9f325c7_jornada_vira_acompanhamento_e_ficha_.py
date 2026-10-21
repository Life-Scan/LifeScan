"""jornada vira acompanhamento e ficha vira anamnese

Revision ID: 315ca9f325c7
Revises: f825a73c9327
Create Date: 2026-10-21 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '315ca9f325c7'
down_revision: Union[str, Sequence[str], None] = 'f825a73c9327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tabelas que apontam para o acompanhamento pela coluna jornada_id / acompanhamento_id
TABELAS_FILHAS = ('arquivos', 'consultas', 'solicitacoes', 'documentos')


def _renomear_coluna(tabela: str, de: str, para: str) -> None:
    # RENAME COLUMN preserva tipo, índices e chaves estrangeiras (MySQL 8)
    op.execute(f'ALTER TABLE {tabela} RENAME COLUMN {de} TO {para}')


def _renomear_indice(tabela: str, de: str, para: str) -> None:
    op.execute(f'ALTER TABLE {tabela} RENAME INDEX {de} TO {para}')


def _trocar_status(tabela: str, antigos: tuple[str, str], novos: tuple[str, str]) -> None:
    """Troca os valores do enum de status sem perder dados: amplia o enum, converte e restringe."""
    todos = ', '.join(f"'{v}'" for v in (*antigos, *novos))
    op.execute(f'ALTER TABLE {tabela} MODIFY status ENUM({todos}) NOT NULL')
    for antigo, novo in zip(antigos, novos):
        op.execute(f"UPDATE {tabela} SET status = '{novo}' WHERE status = '{antigo}'")
    op.execute(f"ALTER TABLE {tabela} MODIFY status ENUM('{novos[0]}', '{novos[1]}') NOT NULL")


def upgrade() -> None:
    """Aplica a migração.

    Escrita à mão: só renomeia tabelas, colunas e índices, para preservar os dados. O status
    passa de ativa/encerrada para ativo/encerrado, concordando com "o acompanhamento".
    """
    op.rename_table('jornadas', 'acompanhamentos')
    _renomear_indice('acompanhamentos', 'ix_jornadas_medico_id', 'ix_acompanhamentos_medico_id')
    _trocar_status('acompanhamentos', ('ativa', 'encerrada'), ('ativo', 'encerrado'))

    op.rename_table('jornada_parceiros', 'acompanhamento_parceiros')
    _renomear_coluna('acompanhamento_parceiros', 'jornada_id', 'acompanhamento_id')
    _renomear_indice(
        'acompanhamento_parceiros',
        'ix_jornada_parceiros_jornada_id',
        'ix_acompanhamento_parceiros_acompanhamento_id',
    )
    _renomear_indice(
        'acompanhamento_parceiros', 'ix_jornada_parceiros_parceiro_id', 'ix_acompanhamento_parceiros_parceiro_id'
    )
    _renomear_indice(
        'acompanhamento_parceiros',
        'uq_jornada_parceiros_jornada_parceiro',
        'uq_acompanhamento_parceiros_acompanhamento_parceiro',
    )

    for tabela in TABELAS_FILHAS:
        _renomear_coluna(tabela, 'jornada_id', 'acompanhamento_id')
        _renomear_indice(tabela, f'ix_{tabela}_jornada_id', f'ix_{tabela}_acompanhamento_id')

    op.rename_table('fichas_paciente', 'anamneses')


def downgrade() -> None:
    """Desfaz a migração."""
    op.rename_table('anamneses', 'fichas_paciente')

    for tabela in TABELAS_FILHAS:
        _renomear_indice(tabela, f'ix_{tabela}_acompanhamento_id', f'ix_{tabela}_jornada_id')
        _renomear_coluna(tabela, 'acompanhamento_id', 'jornada_id')

    _renomear_indice(
        'acompanhamento_parceiros',
        'uq_acompanhamento_parceiros_acompanhamento_parceiro',
        'uq_jornada_parceiros_jornada_parceiro',
    )
    _renomear_indice(
        'acompanhamento_parceiros', 'ix_acompanhamento_parceiros_parceiro_id', 'ix_jornada_parceiros_parceiro_id'
    )
    _renomear_indice(
        'acompanhamento_parceiros',
        'ix_acompanhamento_parceiros_acompanhamento_id',
        'ix_jornada_parceiros_jornada_id',
    )
    _renomear_coluna('acompanhamento_parceiros', 'acompanhamento_id', 'jornada_id')
    op.rename_table('acompanhamento_parceiros', 'jornada_parceiros')

    _trocar_status('acompanhamentos', ('ativo', 'encerrado'), ('ativa', 'encerrada'))
    _renomear_indice('acompanhamentos', 'ix_acompanhamentos_medico_id', 'ix_jornadas_medico_id')
    op.rename_table('acompanhamentos', 'jornadas')
