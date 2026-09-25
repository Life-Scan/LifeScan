"""Classe base declarativa e utilitários comuns aos modelos."""

import enum
from datetime import datetime, timezone

from sqlalchemy import Enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def agora_utc() -> datetime:
    """Data/hora atual em UTC, sem fuso (é assim que gravamos no banco)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def coluna_enum(classe_enum: type[enum.Enum], nome: str) -> Enum:
    """Enum do SQLAlchemy que grava o *valor* do enum Python (e não o nome do membro)."""
    return Enum(
        classe_enum,
        name=nome,
        values_callable=lambda membros: [membro.value for membro in membros],
        validate_strings=True,
    )
