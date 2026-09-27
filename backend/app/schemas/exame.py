from pydantic import BaseModel

from app.models.exame import StatusExame
from app.schemas.arquivo import ArquivoSaida
from app.schemas.base import DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo


class RevisaoEntrada(BaseModel):
    observacao_revisao: str | None = None


class ExameSaida(SchemaSaida):
    id: int
    jornada_id: int
    solicitacao_id: int | None
    titulo: str
    status: StatusExame
    observacao_revisao: str | None
    revisado_em: DataHoraUTC | None
    criado_em: DataHoraUTC
    enviado_por: UsuarioResumo
    arquivo: ArquivoSaida
