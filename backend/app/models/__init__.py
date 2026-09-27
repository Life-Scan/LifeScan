"""Importa todos os modelos para que fiquem registrados em Base.metadata (usado pelo Alembic)."""

from app.models.jornada import Jornada, PassoJornada, StatusJornada
from app.models.usuario import PapelUsuario, Usuario
from app.models.vinculo import VinculoMedicoPaciente

__all__ = [
    "Jornada",
    "PapelUsuario",
    "PassoJornada",
    "StatusJornada",
    "Usuario",
    "VinculoMedicoPaciente",
]
