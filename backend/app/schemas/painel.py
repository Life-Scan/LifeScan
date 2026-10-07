from typing import Literal

from pydantic import BaseModel

from app.schemas.base import SchemaSaida
from app.schemas.documento import DocumentoSaida
from app.schemas.solicitacao import SolicitacaoSaida
from app.schemas.usuario import UsuarioResumo


class JornadaResumo(SchemaSaida):
    id: int
    titulo: str
    paciente: UsuarioResumo


class DocumentoPendente(DocumentoSaida):
    jornada: JornadaResumo


class SolicitacaoPendente(SolicitacaoSaida):
    jornada: JornadaResumo


class PainelMedico(BaseModel):
    tipo_usuario: Literal["medico"] = "medico"
    dias_prazo_proximo: int
    documentos_aguardando_revisao: list[DocumentoPendente]
    # Todas as solicitações pendentes, do paciente e dos parceiros
    solicitacoes_vencidas: list[SolicitacaoPendente]
    solicitacoes_proximas_do_prazo: list[SolicitacaoPendente]


class PainelPaciente(BaseModel):
    tipo_usuario: Literal["paciente"] = "paciente"
    # Pendências do paciente (exames, orientações etc.), vencidas primeiro
    solicitacoes_pendentes: list[SolicitacaoPendente]
    # Lembretes de consultas extras marcadas pelo médico
    consultas_extras: list[SolicitacaoPendente]


class PainelParceiro(BaseModel):
    tipo_usuario: Literal["parceiro"] = "parceiro"
    # Solicitações destinadas ao parceiro, vencidas primeiro
    solicitacoes_pendentes: list[SolicitacaoPendente]
