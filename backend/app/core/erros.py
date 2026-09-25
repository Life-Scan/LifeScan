"""Tratamento de erros de validação com mensagens em português."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _traduzir_erro(erro: dict) -> str:
    tipo = erro.get("type", "")
    contexto = erro.get("ctx") or {}
    campo = str(erro["loc"][-1]) if erro.get("loc") else ""

    if tipo == "missing":
        return "Campo obrigatório."
    if tipo == "string_too_short":
        return f"Deve ter pelo menos {contexto.get('min_length')} caracteres."
    if tipo == "string_too_long":
        return f"Deve ter no máximo {contexto.get('max_length')} caracteres."
    if tipo == "enum" or tipo == "literal_error":
        return f"Valor inválido. Opções aceitas: {contexto.get('expected', '')}."
    if tipo in {"int_parsing", "int_type"}:
        return "Deve ser um número inteiro."
    if tipo.startswith("datetime") or tipo.startswith("date"):
        return "Data inválida."
    if tipo == "json_invalid":
        return "JSON inválido."
    if tipo == "value_error":
        if campo == "email":
            return "Email inválido."
        # Mensagens dos nossos validadores já estão em português
        return str(erro.get("msg", "")).removeprefix("Value error, ")
    return str(erro.get("msg", "Valor inválido."))


def registrar_tratadores_erro(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def tratar_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
        erros = [
            {
                "campo": ".".join(str(parte) for parte in erro.get("loc", ()) if parte != "body"),
                "mensagem": _traduzir_erro(erro),
            }
            for erro in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": "Dados inválidos.", "erros": erros},
        )
