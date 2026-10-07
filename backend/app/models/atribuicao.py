from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc
from app.models.usuario import Usuario


class AtribuicaoParceiro(Base):
    """Parceiro atribuído pelo médico à jornada de um paciente.

    A existência da linha é o que dá ao parceiro acesso à jornada; remover a
    atribuição apaga a linha (os documentos que ele enviou continuam na jornada).
    """

    __tablename__ = "jornada_parceiros"
    __table_args__ = (
        UniqueConstraint("jornada_id", "parceiro_id", name="uq_jornada_parceiros_jornada_parceiro"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    parceiro_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    parceiro: Mapped[Usuario] = relationship()
