import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.models.usuario import Usuario


class PassoAcompanhamento(str, enum.Enum):
    consulta = "consulta"
    exame = "exame"
    retorno = "retorno"


class StatusAcompanhamento(str, enum.Enum):
    ativo = "ativo"
    encerrado = "encerrado"


class Acompanhamento(Base):
    """Acompanhamento de tratamento. Cada paciente tem no máximo um acompanhamento (paciente_id é único)."""

    __tablename__ = "acompanhamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text)
    passo_atual: Mapped[PassoAcompanhamento] = mapped_column(
        coluna_enum(PassoAcompanhamento, "passo_acompanhamento"), default=PassoAcompanhamento.consulta
    )
    status: Mapped[StatusAcompanhamento] = mapped_column(
        coluna_enum(StatusAcompanhamento, "status_acompanhamento"), default=StatusAcompanhamento.ativo
    )
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)
    atualizado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc, onupdate=agora_utc)

    medico: Mapped[Usuario] = relationship(foreign_keys=[medico_id])
    paciente: Mapped[Usuario] = relationship(foreign_keys=[paciente_id])

    @property
    def encerrado(self) -> bool:
        return self.status == StatusAcompanhamento.encerrado
