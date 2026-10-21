from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    garantir_acompanhamento_editavel,
    obter_acompanhamento_com_acesso,
    obter_acompanhamento_do_medico,
    parceiro_atribuido,
)
from app.db.sessao import obter_sessao
from app.models.atribuicao import AtribuicaoParceiro
from app.models.acompanhamento import Acompanhamento
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.atribuicao import AtribuicaoEntrada, AtribuicaoSaida

router = APIRouter(prefix="/follow-ups/{acompanhamento_id}/partners", tags=["Parceiros do acompanhamento"])


@router.get("", response_model=list[AtribuicaoSaida])
def listar_parceiros(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[AtribuicaoParceiro]:
    """Parceiros atribuídos ao acompanhamento (visível ao médico e ao paciente)."""
    consulta = (
        select(AtribuicaoParceiro)
        .where(AtribuicaoParceiro.acompanhamento_id == acompanhamento.id)
        .order_by(AtribuicaoParceiro.criado_em, AtribuicaoParceiro.id)
    )
    return list(sessao.scalars(consulta))


@router.post("", response_model=AtribuicaoSaida, status_code=status.HTTP_201_CREATED)
def atribuir_parceiro(
    dados: AtribuicaoEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> AtribuicaoParceiro:
    """O médico dá a um parceiro acesso à anamnese do paciente e ao envio de documentos."""
    garantir_acompanhamento_editavel(acompanhamento)
    parceiro = sessao.get(Usuario, dados.parceiro_id)
    if parceiro is None or parceiro.tipo_usuario != TipoUsuario.parceiro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parceiro não encontrado.")
    if not parceiro.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "A conta deste parceiro está desativada.")
    if parceiro_atribuido(sessao, acompanhamento.id, parceiro.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este parceiro já está atribuído a este acompanhamento.")

    atribuicao = AtribuicaoParceiro(acompanhamento_id=acompanhamento.id, parceiro_id=parceiro.id)
    sessao.add(atribuicao)
    sessao.commit()
    return atribuicao


@router.delete("/{parceiro_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_parceiro(
    parceiro_id: int,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Response:
    """Tira o acesso do parceiro ao acompanhamento. Os documentos que ele enviou permanecem."""
    atribuicao = sessao.scalar(
        select(AtribuicaoParceiro).where(
            AtribuicaoParceiro.acompanhamento_id == acompanhamento.id,
            AtribuicaoParceiro.parceiro_id == parceiro_id,
        )
    )
    if atribuicao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este parceiro não está atribuído a este acompanhamento.")
    sessao.delete(atribuicao)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
