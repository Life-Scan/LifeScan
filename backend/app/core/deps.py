"""Dependências reutilizáveis de autenticação e autorização."""

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.seguranca import decodificar_token
from app.db.sessao import obter_sessao
from app.models.atribuicao import AtribuicaoParceiro
from app.models.jornada import Jornada
from app.models.usuario import TipoUsuario, Usuario

esquema_bearer = HTTPBearer(auto_error=False)


def _nao_autenticado(mensagem: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=mensagem,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obter_usuario_autenticado(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    """Usuário do token, desde que a conta exista e esteja ativa.

    Não exige a troca da senha provisória: é usado justamente pelas rotas que a
    pessoa precisa alcançar para trocá-la (/auth/me e /auth/change-password).
    """
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
    if not usuario.ativo:
        raise _nao_autenticado("Sua conta está desativada. Procure o seu médico.")
    return usuario


def obter_usuario_atual(usuario: Usuario = Depends(obter_usuario_autenticado)) -> Usuario:
    """Usuário autenticado e que já trocou a senha provisória. Use nas rotas do sistema."""
    if usuario.deve_trocar_senha:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Defina uma nova senha para continuar usando o sistema.",
        )
    return usuario


def exigir_tipo(*tipos: TipoUsuario | str) -> Callable[..., Usuario]:
    """Cria uma dependência que só deixa passar usuários de um dos tipos informados."""
    permitidos = {TipoUsuario(tipo) for tipo in tipos}

    def verificar(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        if usuario.tipo_usuario not in permitidos:
            nomes = " ou ".join(sorted(tipo.value for tipo in permitidos))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Ação permitida apenas para: {nomes}.",
            )
        return usuario

    return verificar


def parceiro_atribuido(sessao: Session, jornada_id: int, parceiro_id: int) -> bool:
    return (
        sessao.scalar(
            select(AtribuicaoParceiro.id).where(
                AtribuicaoParceiro.jornada_id == jornada_id,
                AtribuicaoParceiro.parceiro_id == parceiro_id,
            )
        )
        is not None
    )


def carregar_jornada_com_acesso(
    sessao: Session, usuario: Usuario, jornada_id: int, permitir_parceiro: bool = False
) -> Jornada:
    """Carrega a jornada e garante que o usuário pode acessá-la.

    O médico e o paciente da jornada sempre podem. O parceiro só entra nas rotas que
    passam permitir_parceiro=True (ficha e os próprios envios), e apenas se estiver
    atribuído à jornada: ele não vê consultas, solicitações nem a linha do tempo.

    Versão sem Depends, para rotas que chegam à jornada a partir de outro recurso
    (solicitação, documento, arquivo).
    """
    jornada = sessao.get(Jornada, jornada_id)
    if jornada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jornada não encontrada.")
    if usuario.id in (jornada.medico_id, jornada.paciente_id):
        return jornada
    if usuario.tipo_usuario == TipoUsuario.parceiro and parceiro_atribuido(sessao, jornada.id, usuario.id):
        if permitir_parceiro:
            return jornada
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Parceiros têm acesso apenas à ficha do paciente e aos próprios envios.",
        )
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a esta jornada.")


def obter_jornada_com_acesso(
    jornada_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Jornada para o médico ou o paciente dela."""
    return carregar_jornada_com_acesso(sessao, usuario, jornada_id)


def obter_jornada_com_acesso_de_parceiro(
    jornada_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Jornada para o médico, o paciente ou um parceiro atribuído a ela."""
    return carregar_jornada_com_acesso(sessao, usuario, jornada_id, permitir_parceiro=True)


def obter_jornada_do_medico(
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
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
