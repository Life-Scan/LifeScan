import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, agora_utc, coluna_enum
from app.models.usuario import Usuario


class PassoJornada(str, enum.Enum):
    consulta = "consulta"
    exame = "exame"
    retorno = "retorno"


class StatusJornada(str, enum.Enum):
    ativa = "ativa"
    encerrada = "encerrada"


class Jornada(Base):
    """Jornada de tratamento. Cada paciente tem no máximo uma jornada (paciente_id é único)."""

    __tablename__ = "jornadas"

    id: Mapped[int] = mapped_column(primary_key=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text)
    passo_atual: Mapped[PassoJornada] = mapped_column(
        coluna_enum(PassoJornada, "passo_jornada"), default=PassoJornada.consulta
    )
    status: Mapped[StatusJornada] = mapped_column(
        coluna_enum(StatusJornada, "status_jornada"), default=StatusJornada.ativa
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc, onupdate=agora_utc)

    medico: Mapped[Usuario] = relationship(foreign_keys=[medico_id])
    paciente: Mapped[Usuario] = relationship(foreign_keys=[paciente_id])

    @property
    def encerrada(self) -> bool:
        return self.status == StatusJornada.encerrada
