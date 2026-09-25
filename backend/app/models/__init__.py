"""Importa todos os modelos para que fiquem registrados em Base.metadata (usado pelo Alembic)."""

from app.models.usuario import PapelUsuario, Usuario

__all__ = ["PapelUsuario", "Usuario"]
