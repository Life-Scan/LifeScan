import enum
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, agora_utc, coluna_enum


class PapelUsuario(str, enum.Enum):
    medico = "medico"
    paciente = "paciente"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[PapelUsuario] = mapped_column(coluna_enum(PapelUsuario, "papel_usuario"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)
