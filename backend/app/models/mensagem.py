from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc
from app.models.arquivo import Arquivo
from app.models.usuario import Usuario


class Mensagem(Base):
    __tablename__ = "mensagens"

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    remetente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Texto opcional quando a mensagem traz só um anexo
    conteudo: Mapped[str | None] = mapped_column(Text)
    arquivo_id: Mapped[int | None] = mapped_column(ForeignKey("arquivos.id"))
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc, index=True)

    remetente: Mapped[Usuario] = relationship()
    arquivo: Mapped[Arquivo | None] = relationship()
