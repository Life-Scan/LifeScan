import enum
from typing import Any

from pydantic import BaseModel

from app.schemas.base import DataHoraUTC


class TipoEvento(str, enum.Enum):
    consulta = "consulta"
    documento = "documento"
    solicitacao = "solicitacao"


class EventoLinhaDoTempo(BaseModel):
    """Item da linha do tempo: {tipo, id, data, resumo, dados}."""

    tipo: TipoEvento
    id: int
    data: DataHoraUTC
    resumo: str
    # Registro completo, no mesmo formato das rotas específicas de cada tipo
    dados: dict[str, Any]
