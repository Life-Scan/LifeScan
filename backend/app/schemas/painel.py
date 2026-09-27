from typing import Literal

from pydantic import BaseModel

from app.schemas.base import SchemaSaida
from app.schemas.exame import ExameSaida
from app.schemas.mensagem import MensagemSaida
from app.schemas.solicitacao import SolicitacaoSaida
from app.schemas.usuario import UsuarioResumo


class JornadaResumo(SchemaSaida):
    id: int
    titulo: str
    paciente: UsuarioResumo


class ExamePendente(ExameSaida):
    jornada: JornadaResumo


class SolicitacaoPendente(SolicitacaoSaida):
    jornada: JornadaResumo


class MensagemPendente(BaseModel):
    jornada: JornadaResumo
    ultima_mensagem: MensagemSaida


class PainelMedico(BaseModel):
    papel: Literal["medico"] = "medico"
    dias_prazo_proximo: int
    exames_aguardando_revisao: list[ExamePendente]
    solicitacoes_vencidas: list[SolicitacaoPendente]
    solicitacoes_proximas_do_prazo: list[SolicitacaoPendente]
    mensagens_nao_respondidas: list[MensagemPendente]


class PainelPaciente(BaseModel):
    papel: Literal["paciente"] = "paciente"
    # Pendências do paciente (exames, orientações etc.), vencidas primeiro
    solicitacoes_pendentes: list[SolicitacaoPendente]
    # Lembretes de consultas extras marcadas pelo médico
    consultas_extras: list[SolicitacaoPendente]
