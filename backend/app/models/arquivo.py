from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc


class Arquivo(Base):
    """Metadados de um arquivo enviado. O conteúdo fica em disco, em UPLOAD_DIR/nome_armazenado."""

    __tablename__ = "arquivos"

    id: Mapped[int] = mapped_column(primary_key=True)
    # O acompanhamento é guardado aqui para o download verificar o acesso diretamente
    acompanhamento_id: Mapped[int] = mapped_column(ForeignKey("acompanhamentos.id"), index=True)
    nome_original: Mapped[str] = mapped_column(String(255))
    nome_armazenado: Mapped[str] = mapped_column(String(64), unique=True)
    tipo_mime: Mapped[str] = mapped_column(String(100))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    enviado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)
