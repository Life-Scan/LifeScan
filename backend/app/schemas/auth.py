from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, StringConstraints

from app.models.usuario import PapelUsuario
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


class CadastroEntrada(BaseModel):
    nome: Nome
    email: Email
    senha: SenhaNova
    papel: PapelUsuario


class LoginEntrada(BaseModel):
    email: Email
    senha: str


class UsuarioSaida(SchemaSaida):
    id: int
    nome: str
    email: str
    papel: PapelUsuario
    criado_em: DataHoraUTC


class TokenSaida(BaseModel):
    token_acesso: str
    tipo_token: Literal["bearer"] = "bearer"
    usuario: UsuarioSaida
