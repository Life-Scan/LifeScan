from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.models.ficha import Sexo
from app.schemas.base import DataHoraUTC
from app.schemas.usuario import UsuarioResumo


def _validar_nascimento(valor: date | None) -> date | None:
    if valor is not None and valor > date.today():
        raise ValueError("A data de nascimento não pode estar no futuro.")
    return valor


# Texto livre: espaços nas pontas são removidos (texto vazio é gravado como nulo pela rota)
Texto = Annotated[str, StringConstraints(strip_whitespace=True)] | None


class FichaEntrada(BaseModel):
    """Ficha completa enviada pelo médico. Campos omitidos ou vazios ficam em branco."""

    data_nascimento: Annotated[date | None, AfterValidator(_validar_nascimento)] = None
    sexo: Sexo | None = None
    altura_cm: int | None = Field(None, ge=30, le=260)
    peso_kg: Decimal | None = Field(None, ge=1, le=500, max_digits=5, decimal_places=2)
    diagnosticos: Texto = None
    alergias: Texto = None
    medicamentos_em_uso: Texto = None
    restricoes: Texto = None
    objetivos: Texto = None
    observacoes: Texto = None


class FichaSaida(BaseModel):
    paciente: UsuarioResumo
    # Falso enquanto o médico ainda não salvou a ficha
    preenchida: bool
    data_nascimento: date | None = None
    # Calculada a partir da data de nascimento
    idade: int | None = None
    sexo: Sexo | None = None
    altura_cm: int | None = None
    peso_kg: float | None = None
    diagnosticos: str | None = None
    alergias: str | None = None
    medicamentos_em_uso: str | None = None
    restricoes: str | None = None
    objetivos: str | None = None
    observacoes: str | None = None
    atualizado_em: DataHoraUTC | None = None
