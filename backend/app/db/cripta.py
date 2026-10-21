"""Tipo de coluna que criptografa texto em repouso (LGPD, art. 46).

A criptografia é feita na aplicação: o banco só vê tokens Fernet. Escolhida assim
porque nenhum fluxo consulta os textos clínicos por igualdade/contém — só gravar
e reler pelo id do paciente.
"""

from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from cryptography.fernet import Fernet

from app.core.config import obter_configuracoes


def _fernet() -> Fernet:
    return Fernet(obter_configuracoes().chave_fernet)


class TextoCriptografado(TypeDecorator):
    """Text que grava um token Fernet e devolve o texto original na leitura."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, valor: Any | None, _dialeto: Any) -> str | None:
        if valor is None:
            return None
        return _fernet().encrypt(str(valor).encode("utf-8")).decode("ascii")

    def process_result_value(self, valor: str | None, _dialeto: Any) -> str | None:
        if valor is None:
            return None
        return _fernet().decrypt(valor.encode("utf-8")).decode("utf-8")
