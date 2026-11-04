import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.models.acompanhamento import Acompanhamento
from app.models.usuario import Usuario


class StatusAgendamento(str, enum.Enum):
    agendada = "agendada"
    realizada = "realizada"
    cancelada = "cancelada"
    faltou = "faltou"


class Agendamento(Base):
    """Consulta marcada na agenda do médico, pelo médico ou por um colaborador.

    É diferente da Consulta, que é o registro clínico feito pelo médico depois do atendimento.
    Só pode ser marcada para quem já passou pela primeira consulta, ou seja, tem um
    acompanhamento com ao menos uma consulta registrada (o paciente não precisa ter entrado
    no sistema).
    """

    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    acompanhamento_id: Mapped[int] = mapped_column(ForeignKey("acompanhamentos.id"), index=True)
    data_hora: Mapped[datetime] = mapped_column(DataHora, index=True)
    status: Mapped[StatusAgendamento] = mapped_column(
        coluna_enum(StatusAgendamento, "status_agendamento"), default=StatusAgendamento.agendada
    )
    observacao: Mapped[str | None] = mapped_column(String(255))
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)
    atualizado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc, onupdate=agora_utc)

    acompanhamento: Mapped[Acompanhamento] = relationship()
    criado_por: Mapped[Usuario] = relationship()

    @property
    def paciente(self) -> Usuario:
        return self.acompanhamento.paciente
