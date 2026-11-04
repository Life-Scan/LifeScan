"""tipo de usuario colaborador

Revision ID: 633f73b9fc9d
Revises: e2a7c41d9f05
Create Date: 2026-11-04 16:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '633f73b9fc9d'
down_revision: Union[str, Sequence[str], None] = 'e2a7c41d9f05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESTRICAO_PROFISSAO = 'ck_usuarios_profissao_obrigatoria'


def _trocar_restricao_profissao(condicao: str) -> None:
    op.drop_constraint(RESTRICAO_PROFISSAO, 'usuarios', type_='check')
    op.create_check_constraint(RESTRICAO_PROFISSAO, 'usuarios', condicao)


def upgrade() -> None:
    """Adiciona o colaborador (equipe do consultório), que, como o paciente, não tem profissão."""
    op.execute(
        "ALTER TABLE usuarios MODIFY tipo_usuario "
        "ENUM('medico', 'paciente', 'parceiro', 'colaborador') NOT NULL"
    )
    _trocar_restricao_profissao("tipo_usuario IN ('paciente', 'colaborador') OR profissao IS NOT NULL")


def downgrade() -> None:
    """Desfaz a migração. Recusa se já existirem colaboradores, para não apagar contas."""
    conexao = op.get_bind()
    quantidade = conexao.scalar(sa.text("SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = 'colaborador'"))
    if quantidade:
        raise RuntimeError(
            f"Existem {quantidade} conta(s) de colaborador. Exclua-as antes de desfazer esta migração."
        )
    _trocar_restricao_profissao("tipo_usuario = 'paciente' OR profissao IS NOT NULL")
    op.execute("ALTER TABLE usuarios MODIFY tipo_usuario ENUM('medico', 'paciente', 'parceiro') NOT NULL")
