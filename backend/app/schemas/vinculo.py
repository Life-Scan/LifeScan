from pydantic import BaseModel

from app.schemas.base import DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo


class PacienteBuscaSaida(SchemaSaida):
    id: int
    nome: str
    email: str
    # Situação do paciente em relação ao médico que buscou
    vinculado_a_mim: bool
    vinculado_a_outro_medico: bool


class VinculoEntrada(BaseModel):
    paciente_id: int


class VinculoAtualizacao(BaseModel):
    ativo: bool


class VinculoSaida(SchemaSaida):
    id: int
    ativo: bool
    criado_em: DataHoraUTC
    medico: UsuarioResumo
    paciente: UsuarioResumo
    jornada_id: int | None = None
