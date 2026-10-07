from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, model_validator

from app.models.usuario import TipoUsuario
from app.schemas.auth import Email, Nome
from app.schemas.base import DataHoraUTC, SchemaSaida

Profissao = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class UsuarioResumo(SchemaSaida):
    """Dados públicos de um usuário, usados dentro de outras respostas."""

    id: int
    nome: str
    email: str


class ContaEntrada(BaseModel):
    """Conta criada pelo médico. Só existem contas novas de paciente e de parceiro."""

    tipo_usuario: Literal[TipoUsuario.paciente, TipoUsuario.parceiro]
    nome: Nome
    email: Email
    profissao: Profissao | None = None

    @model_validator(mode="after")
    def validar_profissao(self) -> "ContaEntrada":
        if self.tipo_usuario == TipoUsuario.parceiro and not self.profissao:
            raise ValueError("Informe a profissão do parceiro.")
        if self.tipo_usuario == TipoUsuario.paciente:
            self.profissao = None
        return self


class ContaAtualizacao(BaseModel):
    nome: Nome | None = None
    profissao: Profissao | None = None
    ativo: bool | None = None


class ContaSaida(SchemaSaida):
    """Visão do médico sobre uma conta de paciente ou parceiro."""

    id: int
    tipo_usuario: TipoUsuario
    nome: str
    email: str
    profissao: str | None
    ativo: bool
    # A pessoa ainda não entrou e definiu a própria senha
    primeiro_acesso_pendente: bool
    ultimo_login_em: DataHoraUTC | None
    criado_em: DataHoraUTC
    # Jornada do paciente, se já foi aberta (sempre nulo para parceiros)
    jornada_id: int | None = None
