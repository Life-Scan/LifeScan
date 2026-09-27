import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.models.arquivo import Arquivo
from app.models.usuario import Usuario


class StatusExame(str, enum.Enum):
    enviado = "enviado"
    revisado = "revisado"


class Exame(Base):
    __tablename__ = "exames"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    solicitacao_id: Mapped[int | None] = mapped_column(ForeignKey("solicitacoes.id"))
    enviado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    titulo: Mapped[str] = mapped_column(String(150))
    arquivo_id: Mapped[int] = mapped_column(ForeignKey("arquivos.id"))
    status: Mapped[StatusExame] = mapped_column(
        coluna_enum(StatusExame, "status_exame"), default=StatusExame.enviado
    )
    observacao_revisao: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[datetime | None] = mapped_column(DataHora)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    enviado_por: Mapped[Usuario] = relationship()
    arquivo: Mapped[Arquivo] = relationship()
