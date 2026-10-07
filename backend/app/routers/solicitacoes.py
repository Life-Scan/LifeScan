from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    carregar_jornada_com_acesso,
    exigir_tipo,
    garantir_jornada_editavel,
    obter_jornada_com_acesso_de_parceiro,
    obter_jornada_do_medico,
    obter_usuario_atual,
    parceiro_atribuido,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.solicitacao import SolicitacaoEntrada, SolicitacaoSaida

router = APIRouter(tags=["Solicitações"])


def _resolver_destinatario(sessao: Session, jornada: Jornada, dados: SolicitacaoEntrada) -> int:
    """Destinatário válido: o paciente da jornada (padrão) ou um parceiro atribuído a ela."""
    if dados.destinatario_id is None or dados.destinatario_id == jornada.paciente_id:
        return jornada.paciente_id

    if not parceiro_atribuido(sessao, jornada.id, dados.destinatario_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "O destinatário precisa ser o paciente ou um parceiro atribuído a esta jornada.",
        )
    if dados.tipo == TipoSolicitacao.consulta_extra:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A consulta extra é um lembrete para o paciente e não pode ser destinada a um parceiro.",
        )
    return dados.destinatario_id


@router.post(
    "/journeys/{jornada_id}/requests",
    response_model=SolicitacaoSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar_solicitacao(
    dados: SolicitacaoEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Solicitacao:
    """Cria uma solicitação com prazo para o paciente ou para um parceiro da jornada."""
    garantir_jornada_editavel(jornada)
    if dados.prazo <= agora_utc():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O prazo deve ser uma data futura.")

    solicitacao = Solicitacao(
        jornada_id=jornada.id,
        destinatario_id=_resolver_destinatario(sessao, jornada, dados),
        tipo=dados.tipo,
        descricao=dados.descricao,
        prazo=dados.prazo,
    )
    sessao.add(solicitacao)
    sessao.commit()
    return solicitacao


@router.get("/journeys/{jornada_id}/requests", response_model=list[SolicitacaoSaida])
def listar_solicitacoes(
    status_filtro: StatusSolicitacao | None = Query(None, alias="status"),
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Solicitacao]:
    """Médico e paciente veem todas as solicitações da jornada; o parceiro, só as destinadas a ele."""
    consulta = select(Solicitacao).where(Solicitacao.jornada_id == jornada.id)
    if usuario.tipo_usuario == TipoUsuario.parceiro:
        consulta = consulta.where(Solicitacao.destinatario_id == usuario.id)
    if status_filtro is not None:
        consulta = consulta.where(Solicitacao.status == status_filtro)
    return list(sessao.scalars(consulta.order_by(Solicitacao.prazo, Solicitacao.id)).all())


def _obter_solicitacao_pendente_do_medico(
    solicitacao_id: int, medico: Usuario, sessao: Session
) -> Solicitacao:
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação não encontrada.")
    jornada = carregar_jornada_com_acesso(sessao, medico, solicitacao.jornada_id)
    garantir_jornada_editavel(jornada)
    if solicitacao.status != StatusSolicitacao.pendente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta solicitação não está mais pendente.")
    return solicitacao


@router.patch("/requests/{solicitacao_id}/complete", response_model=SolicitacaoSaida)
def concluir_solicitacao(
    solicitacao_id: int,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Solicitacao:
    """O médico marca a solicitação como atendida (ex.: a consulta extra aconteceu)."""
    solicitacao = _obter_solicitacao_pendente_do_medico(solicitacao_id, medico, sessao)
    solicitacao.marcar_atendida()
    sessao.commit()
    return solicitacao


@router.patch("/requests/{solicitacao_id}/cancel", response_model=SolicitacaoSaida)
def cancelar_solicitacao(
    solicitacao_id: int,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Solicitacao:
    solicitacao = _obter_solicitacao_pendente_do_medico(solicitacao_id, medico, sessao)
    solicitacao.status = StatusSolicitacao.cancelada
    sessao.commit()
    return solicitacao
