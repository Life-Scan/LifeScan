import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.models.arquivo import Arquivo
from app.models.usuario import Usuario


class CategoriaDocumento(str, enum.Enum):
    exame = "exame"
    laudo = "laudo"
    plano_alimentar = "plano_alimentar"
    plano_treino = "plano_treino"
    orientacao = "orientacao"
    outro = "outro"


class StatusDocumento(str, enum.Enum):
    enviado = "enviado"
    revisado = "revisado"


class Documento(Base):
    """Arquivo enviado para a jornada pelo médico, pelo paciente ou por um parceiro:
    exames, laudos, planos alimentares, planos de treino, orientações etc."""

    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    solicitacao_id: Mapped[int | None] = mapped_column(ForeignKey("solicitacoes.id"))
    enviado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    categoria: Mapped[CategoriaDocumento] = mapped_column(
        coluna_enum(CategoriaDocumento, "categoria_documento"), default=CategoriaDocumento.exame
    )
    titulo: Mapped[str] = mapped_column(String(150))
    arquivo_id: Mapped[int] = mapped_column(ForeignKey("arquivos.id"))
    status: Mapped[StatusDocumento] = mapped_column(
        coluna_enum(StatusDocumento, "status_documento"), default=StatusDocumento.enviado
    )
    observacao_revisao: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[datetime | None] = mapped_column(DataHora)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    enviado_por: Mapped[Usuario] = relationship()
    arquivo: Mapped[Arquivo] = relationship()
