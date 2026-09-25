"""Tipos e configurações compartilhados pelos schemas."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


def _marcar_utc(valor: datetime) -> datetime:
    # O banco guarda datas em UTC sem fuso; na saída deixamos o fuso explícito
    # para o frontend converter corretamente para o horário local.
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


DataHoraUTC = Annotated[datetime, AfterValidator(_marcar_utc)]


class SchemaSaida(BaseModel):
    """Base dos schemas de resposta: permite construir a partir de objetos ORM."""

    model_config = ConfigDict(from_attributes=True)
