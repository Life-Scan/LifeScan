import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DataHora, agora_utc, coluna_enum
from app.db.cripta import TextoCriptografado


class Sexo(str, enum.Enum):
    masculino = "masculino"
    feminino = "feminino"
    outro = "outro"


class Anamnese(Base):
    """Resumo clínico do paciente, mantido pelo médico.

    É o que os parceiros atribuídos enxergam do paciente (eles não veem consultas,
    prescrições nem documentos de outras pessoas). Todos os campos são opcionais.
    """

    __tablename__ = "anamneses"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[Sexo | None] = mapped_column(coluna_enum(Sexo, "sexo"))
    altura_cm: Mapped[int | None] = mapped_column(Integer)
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    # Textos clínicos criptografados em repouso (LGPD, art. 46): o banco só vê tokens Fernet
    diagnosticos: Mapped[str | None] = mapped_column(TextoCriptografado)
    alergias: Mapped[str | None] = mapped_column(TextoCriptografado)
    medicamentos_em_uso: Mapped[str | None] = mapped_column(TextoCriptografado)
    restricoes: Mapped[str | None] = mapped_column(TextoCriptografado)
    objetivos: Mapped[str | None] = mapped_column(TextoCriptografado)
    observacoes: Mapped[str | None] = mapped_column(TextoCriptografado)
    atualizado_em: Mapped[datetime] = mapped_column(DataHora, default=agora_utc, onupdate=agora_utc)
