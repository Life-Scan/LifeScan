from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc


class RegistroAcesso(Base):
    """Trilha de auditoria de quem leu ou alterou a anamnese (LGPD, arts. 37 e 18, V).

    Grava id e tipo do usuário, nunca o nome: o log é pseudônimo e sobrevive à
    exclusão da conta, por isso não tem chave estrangeira para usuarios.
    """

    __tablename__ = "registros_acesso"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, index=True)
    tipo_usuario: Mapped[str] = mapped_column(String(12))
    acompanhamento_id: Mapped[int] = mapped_column(Integer, index=True)
    acao: Mapped[str] = mapped_column(String(10))  # "leitura" ou "escrita"
    ocorreu_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)
