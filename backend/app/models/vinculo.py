from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, agora_utc
from app.models.usuario import Usuario


class VinculoMedicoPaciente(Base):
    """Vínculo entre médico e paciente. Cada paciente tem um único médico (paciente_id é único)."""

    __tablename__ = "vinculos_medico_paciente"

    id: Mapped[int] = mapped_column(primary_key=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora_utc)

    medico: Mapped[Usuario] = relationship(foreign_keys=[medico_id])
    paciente: Mapped[Usuario] = relationship(foreign_keys=[paciente_id])
