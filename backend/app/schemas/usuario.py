from app.schemas.base import SchemaSaida


class UsuarioResumo(SchemaSaida):
    """Dados públicos de um usuário, usados dentro de outras respostas."""

    id: int
    nome: str
    email: str
