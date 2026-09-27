import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, agora_utc, coluna_enum


class TipoSolicitacao(str, enum.Enum):
    exame = "exame"
    consulta_extra = "consulta_extra"
    orientacao_profissional = "orientacao_profissional"
    outro = "outro"


class StatusSolicitacao(str, enum.Enum):
    pendente = "pendente"
    atendida = "atendida"
    cancelada = "cancelada"


# Solicitações atendidas automaticamente quando o paciente envia o documento pedido
TIPOS_ATENDIDOS_POR_ENVIO = {TipoSolicitacao.exame, TipoSolicitacao.orientacao_profissional}


class Solicitacao(Base):
    """Pedido do médico com prazo. Consulta extra é apenas um lembrete para o paciente."""

    __tablename__ = "solicitacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    tipo: Mapped[TipoSolicitacao] = mapped_column(coluna_enum(TipoSolicitacao, "tipo_solicitacao"))
    descricao: Mapped[str] = mapped_column(Text)
    prazo: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[StatusSolicitacao] = mapped_column(
        coluna_enum(StatusSolicitacao, "status_solicitacao"), default=StatusSolicitacao.pendente
    )
    atendida_em: Mapped[datetime | None] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)

    @property
    def vencida(self) -> bool:
        """Calculado, nunca gravado: pendente com prazo no passado."""
        return self.status == StatusSolicitacao.pendente and self.prazo < agora_utc()

    def marcar_atendida(self) -> None:
        self.status = StatusSolicitacao.atendida
        self.atendida_em = agora_utc()
