"""Dependências reutilizáveis de autenticação e autorização."""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.seguranca import decodificar_token
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.usuario import PapelUsuario, Usuario
from app.services.vinculos import vinculo_ativo_entre

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


def obter_jornada_com_acesso(
    jornada_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Carrega a jornada e garante que o usuário é o médico ou o paciente dela
    e que o vínculo entre os dois está ativo (RNF10)."""
    return carregar_jornada_com_acesso(sessao, usuario, jornada_id)


def carregar_jornada_com_acesso(sessao: Session, usuario: Usuario, jornada_id: int) -> Jornada:
    """Versão sem Depends, para rotas que chegam à jornada a partir de outro recurso
    (solicitação, exame, arquivo)."""
    jornada = sessao.get(Jornada, jornada_id)
    if jornada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jornada não encontrada.")
    if usuario.id not in (jornada.medico_id, jornada.paciente_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a esta jornada.")
    if not vinculo_ativo_entre(sessao, jornada.medico_id, jornada.paciente_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "O vínculo entre médico e paciente está inativo. A jornada não pode ser acessada.",
        )
    return jornada


def obter_jornada_do_medico(
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    usuario: Usuario = Depends(exigir_papel(PapelUsuario.medico)),
) -> Jornada:
    """Como obter_jornada_com_acesso, mas só para o médico da jornada."""
    return jornada


def garantir_jornada_editavel(jornada: Jornada) -> None:
    """Jornadas encerradas ficam somente leitura."""
    if jornada.encerrada:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Esta jornada está encerrada e não pode ser alterada.",
        )
