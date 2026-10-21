from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.core.deps import (
    carregar_acompanhamento_com_acesso,
    exigir_tipo,
    garantir_acompanhamento_editavel,
    obter_acompanhamento_com_acesso_de_parceiro,
    obter_acompanhamento_do_medico,
    obter_usuario_atual,
    parceiro_atribuido,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.acompanhamento import Acompanhamento
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.solicitacao import SolicitacaoEntrada, SolicitacaoSaida
from app.schemas.paginacao import Pagina, Paginacao, paginar
from sqlalchemy.orm import selectinload

router = APIRouter(tags=["Solicitações"])


def _resolver_destinatario(sessao: Session, acompanhamento: Acompanhamento, dados: SolicitacaoEntrada) -> int:
    """Destinatário válido: o paciente do acompanhamento (padrão) ou um parceiro atribuído a ela."""
    if dados.destinatario_id is None or dados.destinatario_id == acompanhamento.paciente_id:
        return acompanhamento.paciente_id

    if not parceiro_atribuido(sessao, acompanhamento.id, dados.destinatario_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "O destinatário precisa ser o paciente ou um parceiro atribuído a este acompanhamento.",
        )
    if dados.tipo == TipoSolicitacao.consulta_extra:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A consulta extra é um lembrete para o paciente e não pode ser destinada a um parceiro.",
        )
    return dados.destinatario_id


@router.post(
    "/follow-ups/{acompanhamento_id}/requests",
    response_model=SolicitacaoSaida,
    status_code=status.HTTP_201_CREATED,
)
def criar_solicitacao(
    dados: SolicitacaoEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Solicitacao:
    """Cria uma solicitação com prazo para o paciente ou para um parceiro do acompanhamento."""
    garantir_acompanhamento_editavel(acompanhamento)
    if dados.prazo <= agora_utc():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O prazo deve ser uma data futura.")

    solicitacao = Solicitacao(
        acompanhamento_id=acompanhamento.id,
        destinatario_id=_resolver_destinatario(sessao, acompanhamento, dados),
        tipo=dados.tipo,
        descricao=dados.descricao,
        prazo=dados.prazo,
    )
    sessao.add(solicitacao)
    sessao.commit()
    return solicitacao


@router.get("/follow-ups/{acompanhamento_id}/requests", response_model=Pagina[SolicitacaoSaida] | list[SolicitacaoSaida])
def listar_solicitacoes(
    status_filtro: StatusSolicitacao | None = Query(None, alias="status"),
    paginacao: Paginacao = Depends(),
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    """Médico e paciente veem todas as solicitações do acompanhamento; o parceiro, só as destinadas a ele."""
    consulta = select(Solicitacao).options(selectinload(Solicitacao.destinatario)).where(Solicitacao.acompanhamento_id == acompanhamento.id)
    if usuario.tipo_usuario == TipoUsuario.parceiro:
        consulta = consulta.where(Solicitacao.destinatario_id == usuario.id)
    if status_filtro is not None:
        consulta = consulta.where(Solicitacao.status == status_filtro)
    if paginacao.pagina is not None:
        consulta = consulta.order_by(case((Solicitacao.status == StatusSolicitacao.pendente, 0), (Solicitacao.status == StatusSolicitacao.atendida, 1), else_=2))
    return paginar(sessao, consulta.order_by(Solicitacao.prazo, Solicitacao.id), paginacao)


def _obter_solicitacao_pendente_do_medico(
    solicitacao_id: int, medico: Usuario, sessao: Session
) -> Solicitacao:
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação não encontrada.")
    acompanhamento = carregar_acompanhamento_com_acesso(sessao, medico, solicitacao.acompanhamento_id)
    garantir_acompanhamento_editavel(acompanhamento)
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
