from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.solicitacao import StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario
from app.schemas.base import DataHoraEntrada, DataHoraUTC, SchemaSaida


class SolicitacaoEntrada(BaseModel):
    tipo: TipoSolicitacao
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3)]
    prazo: DataHoraEntrada
    # Se omitido, a solicitação vai para o paciente da jornada
    destinatario_id: int | None = None


class DestinatarioResumo(SchemaSaida):
    id: int
    nome: str
    tipo_usuario: TipoUsuario
    profissao: str | None


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
    destinatario: DestinatarioResumo
