"""Dependências reutilizáveis de autenticação e autorização."""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.seguranca import decodificar_token
from app.db.sessao import obter_sessao
from app.models.usuario import PapelUsuario, Usuario

esquema_bearer = HTTPBearer(auto_error=False)


def _nao_autenticado(mensagem: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=mensagem,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obter_usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    if credenciais is None:
        raise _nao_autenticado("Não autenticado. Faça login para continuar.")
    try:
        carga = decodificar_token(credenciais.credentials)
        usuario_id = int(carga["sub"])
    except jwt.ExpiredSignatureError:
        raise _nao_autenticado("Sessão expirada. Faça login novamente.")
    except (jwt.InvalidTokenError, ValueError):
        raise _nao_autenticado("Token de acesso inválido.")

    usuario = sessao.get(Usuario, usuario_id)
    if usuario is None:
        raise _nao_autenticado("Usuário do token não existe mais.")
    return usuario


def exigir_papel(*papeis: PapelUsuario | str) -> Callable[..., Usuario]:
    """Cria uma dependência que só deixa passar usuários com um dos papéis informados."""
    permitidos = {PapelUsuario(papel) for papel in papeis}

    def verificar(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        if usuario.papel not in permitidos:
            nomes = " ou ".join(sorted(p.value for p in permitidos))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Ação permitida apenas para: {nomes}.",
            )
        return usuario

    return verificar
