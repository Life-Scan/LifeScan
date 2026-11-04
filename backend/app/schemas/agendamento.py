from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.agendamento import StatusAgendamento
from app.schemas.base import DataHoraEntrada, DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo

Observacao = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class AgendamentoEntrada(BaseModel):
    paciente_id: int
    data_hora: DataHoraEntrada
    observacao: Observacao | None = None


class AgendamentoAtualizacao(BaseModel):
    """Remarcação (nova data e hora) ou troca da observação de uma consulta ainda agendada."""

    data_hora: DataHoraEntrada | None = None
    observacao: Observacao | None = None


class StatusAgendamentoEntrada(BaseModel):
    status: StatusAgendamento


class AgendamentoSaida(SchemaSaida):
    id: int
    data_hora: DataHoraUTC
    status: StatusAgendamento
    observacao: str | None
    # Só nome e email: o colaborador não acessa os dados clínicos
    paciente: UsuarioResumo
    criado_por: UsuarioResumo
    criado_em: DataHoraUTC
    atualizado_em: DataHoraUTC


class PacienteAgendavel(SchemaSaida):
    """Paciente que já passou pela primeira consulta e pode ter consultas agendadas."""

    id: int
    nome: str
    email: str
