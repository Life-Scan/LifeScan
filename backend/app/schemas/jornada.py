from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.jornada import PassoJornada, StatusJornada
from app.schemas.base import DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo

Titulo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=150)]


class JornadaEntrada(BaseModel):
    paciente_id: int
    titulo: Titulo
    descricao: str | None = None


class PassoEntrada(BaseModel):
    passo_atual: PassoJornada


class StatusEntrada(BaseModel):
    status: StatusJornada


class JornadaSaida(SchemaSaida):
    id: int
    titulo: str
    descricao: str | None
    passo_atual: PassoJornada
    status: StatusJornada
    criado_em: DataHoraUTC
    atualizado_em: DataHoraUTC
    medico: UsuarioResumo
    paciente: UsuarioResumo
