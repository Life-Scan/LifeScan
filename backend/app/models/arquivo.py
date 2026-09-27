from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, agora_utc


class Arquivo(Base):
    """Metadados de um arquivo enviado. O conteúdo fica em disco, em UPLOAD_DIR/nome_armazenado."""

    __tablename__ = "arquivos"

    id: Mapped[int] = mapped_column(primary_key=True)
    # A jornada é guardada aqui para o download verificar o acesso diretamente
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    nome_original: Mapped[str] = mapped_column(String(255))
    nome_armazenado: Mapped[str] = mapped_column(String(64), unique=True)
    tipo_mime: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    enviado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)
