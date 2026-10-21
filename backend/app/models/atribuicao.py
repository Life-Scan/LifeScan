from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, DataHora, agora_utc
from app.models.usuario import Usuario


class AtribuicaoParceiro(Base):
    """Parceiro atribuído pelo médico ao acompanhamento de um paciente.

    A existência da linha é o que dá ao parceiro acesso ao acompanhamento; remover a
    atribuição apaga a linha (os documentos que ele enviou continuam no acompanhamento).
    """

    __tablename__ = "acompanhamento_parceiros"
    __table_args__ = (
        UniqueConstraint("acompanhamento_id", "parceiro_id", name="uq_acompanhamento_parceiros_acompanhamento_parceiro"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    acompanhamento_id: Mapped[int] = mapped_column(ForeignKey("acompanhamentos.id"), index=True)
    parceiro_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc)

    parceiro: Mapped[Usuario] = relationship()
