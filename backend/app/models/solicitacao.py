import enum
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.models.usuario import Usuario


class TipoSolicitacao(str, enum.Enum):
    exame = "exame"
    consulta_extra = "consulta_extra"
    orientacao_profissional = "orientacao_profissional"
    outro = "outro"


class StatusSolicitacao(str, enum.Enum):
    pendente = "pendente"
    atendida = "atendida"
    cancelada = "cancelada"


# Solicitações atendidas automaticamente quando o destinatário envia o documento pedido
TIPOS_ATENDIDOS_POR_ENVIO = {TipoSolicitacao.exame, TipoSolicitacao.orientacao_profissional}


class Solicitacao(Base):
    """Pedido do médico com prazo, destinado ao paciente ou a um parceiro da jornada.

    Consulta extra é apenas um lembrete para o paciente.
    """

    __tablename__ = "solicitacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    # Quem deve atender: o paciente da jornada ou um parceiro atribuído a ela
    destinatario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    tipo: Mapped[TipoSolicitacao] = mapped_column(coluna_enum(TipoSolicitacao, "tipo_solicitacao"))
    descricao: Mapped[str] = mapped_column(Text)
    prazo: Mapped[datetime] = mapped_column(DataHora, index=True)
    status: Mapped[StatusSolicitacao] = mapped_column(
        coluna_enum(StatusSolicitacao, "status_solicitacao"), default=StatusSolicitacao.pendente
    )
    atendida_em: Mapped[datetime | None] = mapped_column(DataHora)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    destinatario: Mapped[Usuario] = relationship()

    @property
    def vencida(self) -> bool:
        """Calculado, nunca gravado: pendente com prazo no passado."""
        return self.status == StatusSolicitacao.pendente and self.prazo < agora_utc()

    def marcar_atendida(self) -> None:
        self.status = StatusSolicitacao.atendida
        self.atendida_em = agora_utc()
