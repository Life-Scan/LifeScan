from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, StringConstraints

from app.models.usuario import TipoUsuario
from app.schemas.base import DataHoraUTC, SchemaSaida

# O bcrypt só considera os primeiros 72 bytes da senha
LIMITE_BYTES_SENHA = 72


def _validar_tamanho_senha(senha: str) -> str:
    if len(senha.encode("utf-8")) > LIMITE_BYTES_SENHA:
        raise ValueError("A senha é longa demais (máximo de 72 bytes).")
    return senha


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


Email = Annotated[EmailStr, AfterValidator(_normalizar_email)]
Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
SenhaNova = Annotated[str, StringConstraints(min_length=6), AfterValidator(_validar_tamanho_senha)]


class LoginEntrada(BaseModel):
    email: Email
    senha: str


class TrocaSenhaEntrada(BaseModel):
    senha_atual: str
    nova_senha: SenhaNova


class EsqueciSenhaEntrada(BaseModel):
    email: Email


class MensagemSaida(BaseModel):
    mensagem: str


class UsuarioSaida(SchemaSaida):
    id: int
    tipo_usuario: TipoUsuario
    nome: str
    email: str
    profissao: str | None
    # Verdadeiro logo após entrar com a senha provisória: o frontend leva à troca de senha
    deve_trocar_senha: bool
    criado_em: DataHoraUTC


class TokenSaida(BaseModel):
    token_acesso: str
    tipo_token: Literal["bearer"] = "bearer"
    usuario: UsuarioSaida
