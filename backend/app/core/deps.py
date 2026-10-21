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
from app.models.acompanhamento import Acompanhamento
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
    pessoa precisa alcançar para defini-la (/auth/me e /auth/set-password).
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


def parceiro_atribuido(sessao: Session, acompanhamento_id: int, parceiro_id: int) -> bool:
    return (
        sessao.scalar(
            select(AtribuicaoParceiro.id).where(
                AtribuicaoParceiro.acompanhamento_id == acompanhamento_id,
                AtribuicaoParceiro.parceiro_id == parceiro_id,
            )
        )
        is not None
    )


def carregar_acompanhamento_com_acesso(
    sessao: Session, usuario: Usuario, acompanhamento_id: int, permitir_parceiro: bool = False
) -> Acompanhamento:
    """Carrega o acompanhamento e garante que o usuário pode acessá-lo.

    O médico e o paciente do acompanhamento sempre podem. O parceiro só entra nas rotas que
    passam permitir_parceiro=True (anamnese e os próprios envios), e apenas se estiver
    atribuído ao acompanhamento: ele não vê consultas, solicitações nem a linha do tempo.

    Versão sem Depends, para rotas que chegam ao acompanhamento a partir de outro recurso
    (solicitação, documento, arquivo).
    """
    acompanhamento = sessao.get(Acompanhamento, acompanhamento_id)
    if acompanhamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acompanhamento não encontrado.")
    if usuario.id in (acompanhamento.medico_id, acompanhamento.paciente_id):
        return acompanhamento
    if usuario.tipo_usuario == TipoUsuario.parceiro and parceiro_atribuido(sessao, acompanhamento.id, usuario.id):
        if permitir_parceiro:
            return acompanhamento
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Parceiros têm acesso apenas à anamnese do paciente e aos próprios envios.",
        )
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem acesso a este acompanhamento.")


def obter_acompanhamento_com_acesso(
    acompanhamento_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Acompanhamento:
    """Acompanhamento para o médico ou o paciente dele."""
    return carregar_acompanhamento_com_acesso(sessao, usuario, acompanhamento_id)


def obter_acompanhamento_com_acesso_de_parceiro(
    acompanhamento_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Acompanhamento:
    """Acompanhamento para o médico, o paciente ou um parceiro atribuído a ele."""
    return carregar_acompanhamento_com_acesso(sessao, usuario, acompanhamento_id, permitir_parceiro=True)


def obter_acompanhamento_do_medico(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
) -> Acompanhamento:
    """Como obter_acompanhamento_com_acesso, mas só para o médico do acompanhamento."""
    return acompanhamento


def garantir_acompanhamento_editavel(acompanhamento: Acompanhamento) -> None:
    """Acompanhamentos encerrados ficam somente leitura."""
    if acompanhamento.encerrado:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Este acompanhamento está encerrado e não pode ser alterado.",
        )
