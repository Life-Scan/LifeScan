from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.solicitacao import StatusSolicitacao, TipoSolicitacao
from app.schemas.base import DataHoraEntrada, DataHoraUTC, SchemaSaida


class SolicitacaoEntrada(BaseModel):
    tipo: TipoSolicitacao
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3)]
    prazo: DataHoraEntrada


class SolicitacaoSaida(SchemaSaida):
    id: int
    jornada_id: int
    tipo: TipoSolicitacao
    descricao: str
    prazo: DataHoraUTC
    status: StatusSolicitacao
    vencida: bool
    atendida_em: DataHoraUTC | None
    criado_em: DataHoraUTC
