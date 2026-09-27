from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.consulta import TipoConsulta
from app.schemas.base import DataHoraEntrada, DataHoraUTC, SchemaSaida


class PrescricaoEntrada(BaseModel):
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    dosagem: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    instrucoes: str | None = None


class ConsultaEntrada(BaseModel):
    tipo: TipoConsulta
    data: DataHoraEntrada
    anotacoes: str | None = None
    prescricoes: list[PrescricaoEntrada] = Field(default_factory=list)


class PrescricaoSaida(SchemaSaida):
    id: int
    descricao: str
    dosagem: str | None
    instrucoes: str | None


class ConsultaSaida(SchemaSaida):
    id: int
    jornada_id: int
    tipo: TipoConsulta
    data: DataHoraUTC
    anotacoes: str | None
    criado_em: DataHoraUTC
    prescricoes: list[PrescricaoSaida]
