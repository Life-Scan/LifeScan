"""criptografa textos clinicos da anamnese em repouso

Revision ID: e2a7c41d9f05
Revises: d5b9e3f07c11
Create Date: 2026-10-21 18:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from cryptography.fernet import Fernet, InvalidToken


from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2a7c41d9f05'
down_revision: Union[str, Sequence[str], None] = 'd5b9e3f07c11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CAMPOS_DE_TEXTO = (
    'diagnosticos',
    'alergias',
    'medicamentos_em_uso',
    'restricoes',
    'objetivos',
    'observacoes',
)


def _texto_fernet() -> Fernet:
    # Mesma chave da aplicação: dedicada (FERNET_KEY) ou derivada do segredo JWT
    from app.core.config import obter_configuracoes

    return Fernet(obter_configuracoes().chave_fernet)


def _atualizar(linha: dict, fernet: Fernet, cifrar: bool) -> None:
    mudancas = {}
    for campo in CAMPOS_DE_TEXTO:
        valor = linha[campo]
        if valor is None:
            continue
        try:
            fernet.decrypt(valor.encode('utf-8'))
            # Já é um token Fernet (criptografia aplicada antes da migração)
            if cifrar:
                continue
            mudancas[campo] = fernet.decrypt(valor.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            # Texto plano
            if cifrar:
                mudancas[campo] = fernet.encrypt(valor.encode('utf-8')).decode('ascii')
    if mudancas:
        pares = ', '.join(f'{campo} = :{campo}' for campo in mudancas)
        op.get_bind().execute(
            sa.text(f'UPDATE anamneses SET {pares} WHERE id = :id'),
            {**mudancas, 'id': linha['id']},
        )


def upgrade() -> None:
    """Cifra os textos clínicos já gravados (LGPD, art. 46).

    Idempotente: valores que já são tokens Fernet passam intocados.
    """
    colunas = ', '.join(('id', *CAMPOS_DE_TEXTO))
    linhas = op.get_bind().execute(sa.text(f'SELECT {colunas} FROM anamneses')).mappings().all()
    fernet = _texto_fernet()
    for linha in linhas:
        _atualizar(linha, fernet, cifrar=True)


def downgrade() -> None:
    """Reverte: decifra os textos de volta ao plano. Valores planos passam intocados."""
    colunas = ', '.join(('id', *CAMPOS_DE_TEXTO))
    linhas = op.get_bind().execute(sa.text(f'SELECT {colunas} FROM anamneses')).mappings().all()
    fernet = _texto_fernet()
    for linha in linhas:
        _atualizar(linha, fernet, cifrar=False)
