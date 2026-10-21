"""Importa todos os modelos para que fiquem registrados em Base.metadata (usado pelo Alembic)."""

from app.models.acompanhamento import Acompanhamento, PassoAcompanhamento, StatusAcompanhamento
from app.models.anamnese import Anamnese, Sexo
from app.models.arquivo import Arquivo
from app.models.atribuicao import AtribuicaoParceiro
from app.models.consentimento import Consentimento
from app.models.consulta import Consulta, Prescricao, TipoConsulta
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario

__all__ = [
    "Acompanhamento",
    "Anamnese",
    "Arquivo",
    "AtribuicaoParceiro",
    "CategoriaDocumento",
    "Consentimento",
    "Consulta",
    "Documento",
    "PassoAcompanhamento",
    "Prescricao",
    "Sexo",
    "Solicitacao",
    "StatusAcompanhamento",
    "StatusDocumento",
    "StatusSolicitacao",
    "TipoConsulta",
    "TipoSolicitacao",
    "TipoUsuario",
    "Usuario",
]
