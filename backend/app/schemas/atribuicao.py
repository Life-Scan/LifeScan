from pydantic import BaseModel

from app.schemas.base import DataHoraUTC, SchemaSaida


class ParceiroResumo(SchemaSaida):
    id: int
    nome: str
    email: str
    profissao: str | None


class AtribuicaoEntrada(BaseModel):
    parceiro_id: int


class AtribuicaoSaida(SchemaSaida):
    id: int
    criado_em: DataHoraUTC
    parceiro: ParceiroResumo
