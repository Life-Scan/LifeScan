from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    carregar_jornada_com_acesso,
    exigir_tipo,
    garantir_jornada_editavel,
    obter_jornada_com_acesso,
    obter_jornada_do_medico,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.solicitacao import SolicitacaoEntrada, SolicitacaoSaida

router = APIRouter(tags=["Solicitações"])


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
    """Cria uma solicitação com prazo para o paciente (RF06)."""
    garantir_jornada_editavel(jornada)
    if dados.prazo <= agora_utc():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O prazo deve ser uma data futura.")

    solicitacao = Solicitacao(
        jornada_id=jornada.id,
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
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[Solicitacao]:
    consulta = select(Solicitacao).where(Solicitacao.jornada_id == jornada.id)
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
