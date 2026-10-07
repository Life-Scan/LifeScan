"""Importa todos os modelos para que fiquem registrados em Base.metadata (usado pelo Alembic)."""

from app.models.arquivo import Arquivo
from app.models.consulta import Consulta, Prescricao, TipoConsulta
from app.models.exame import Exame, StatusExame
from app.models.jornada import Jornada, PassoJornada, StatusJornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario

__all__ = [
    "Arquivo",
    "Consulta",
    "Exame",
    "Jornada",
    "PassoJornada",
    "Prescricao",
    "Solicitacao",
    "StatusExame",
    "StatusJornada",
    "StatusSolicitacao",
    "TipoConsulta",
    "TipoSolicitacao",
    "TipoUsuario",
    "Usuario",
]
