import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc, coluna_enum


class Sexo(str, enum.Enum):
    masculino = "masculino"
    feminino = "feminino"
    outro = "outro"


class FichaPaciente(Base):
    """Resumo clínico do paciente, mantido pelo médico.

    É o que os parceiros atribuídos enxergam do paciente (eles não veem consultas,
    prescrições nem documentos de outras pessoas). Todos os campos são opcionais.
    """

    __tablename__ = "fichas_paciente"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[Sexo | None] = mapped_column(coluna_enum(Sexo, "sexo"))
    altura_cm: Mapped[int | None] = mapped_column(Integer)
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    diagnosticos: Mapped[str | None] = mapped_column(Text)
    alergias: Mapped[str | None] = mapped_column(Text)
    medicamentos_em_uso: Mapped[str | None] = mapped_column(Text)
    restricoes: Mapped[str | None] = mapped_column(Text)
    objetivos: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc, onupdate=agora_utc)
