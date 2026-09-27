import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum


class TipoConsulta(str, enum.Enum):
    consulta = "consulta"
    retorno = "retorno"


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    tipo: Mapped[TipoConsulta] = mapped_column(coluna_enum(TipoConsulta, "tipo_consulta"))
    data: Mapped[datetime] = mapped_column(DataHora)
    anotacoes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    prescricoes: Mapped[list["Prescricao"]] = relationship(
        back_populates="consulta",
        cascade="all, delete-orphan",
        order_by="Prescricao.id",
    )


class Prescricao(Base):
    __tablename__ = "prescricoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    consulta_id: Mapped[int] = mapped_column(ForeignKey("consultas.id"), index=True)
    descricao: Mapped[str] = mapped_column(String(255))
    dosagem: Mapped[str | None] = mapped_column(String(120))
    instrucoes: Mapped[str | None] = mapped_column(Text)

    consulta: Mapped[Consulta] = relationship(back_populates="prescricoes")
