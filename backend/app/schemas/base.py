"""Tipos e configurações compartilhados pelos schemas."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


def _marcar_utc(valor: datetime) -> datetime:
    # O banco guarda datas em UTC sem fuso; na saída deixamos o fuso explícito
    # para o frontend converter corretamente para o horário local.
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor


def _converter_para_utc_sem_fuso(valor: datetime) -> datetime:
    # Datas recebidas com fuso são convertidas para UTC; sem fuso, assumimos que já estão em UTC
    if valor.tzinfo is not None:
        valor = valor.astimezone(timezone.utc).replace(tzinfo=None)
    return valor


# Saída: data em UTC com fuso explícito
DataHoraUTC = Annotated[datetime, AfterValidator(_marcar_utc)]
# Entrada: normalizada para UTC sem fuso, como é gravada no banco
DataHoraEntrada = Annotated[datetime, AfterValidator(_converter_para_utc_sem_fuso)]


class SchemaSaida(BaseModel):
    """Base dos schemas de resposta: permite construir a partir de objetos ORM."""

    model_config = ConfigDict(from_attributes=True)
