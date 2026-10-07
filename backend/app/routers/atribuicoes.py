from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    garantir_jornada_editavel,
    obter_jornada_com_acesso,
    obter_jornada_do_medico,
    parceiro_atribuido,
)
from app.db.sessao import obter_sessao
from app.models.atribuicao import AtribuicaoParceiro
from app.models.jornada import Jornada
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.atribuicao import AtribuicaoEntrada, AtribuicaoSaida

router = APIRouter(prefix="/journeys/{jornada_id}/partners", tags=["Parceiros da jornada"])


@router.get("", response_model=list[AtribuicaoSaida])
def listar_parceiros(
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[AtribuicaoParceiro]:
    """Parceiros atribuídos à jornada (visível ao médico e ao paciente)."""
    consulta = (
        select(AtribuicaoParceiro)
        .where(AtribuicaoParceiro.jornada_id == jornada.id)
        .order_by(AtribuicaoParceiro.criado_em, AtribuicaoParceiro.id)
    )
    return list(sessao.scalars(consulta))


@router.post("", response_model=AtribuicaoSaida, status_code=status.HTTP_201_CREATED)
def atribuir_parceiro(
    dados: AtribuicaoEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> AtribuicaoParceiro:
    """O médico dá a um parceiro acesso à ficha do paciente e ao envio de documentos."""
    garantir_jornada_editavel(jornada)
    parceiro = sessao.get(Usuario, dados.parceiro_id)
    if parceiro is None or parceiro.tipo_usuario != TipoUsuario.parceiro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parceiro não encontrado.")
    if not parceiro.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "A conta deste parceiro está desativada.")
    if parceiro_atribuido(sessao, jornada.id, parceiro.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este parceiro já está atribuído a esta jornada.")

    atribuicao = AtribuicaoParceiro(jornada_id=jornada.id, parceiro_id=parceiro.id)
    sessao.add(atribuicao)
    sessao.commit()
    return atribuicao


@router.delete("/{parceiro_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_parceiro(
    parceiro_id: int,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Response:
    """Tira o acesso do parceiro à jornada. Os documentos que ele enviou permanecem."""
    atribuicao = sessao.scalar(
        select(AtribuicaoParceiro).where(
            AtribuicaoParceiro.jornada_id == jornada.id,
            AtribuicaoParceiro.parceiro_id == parceiro_id,
        )
    )
    if atribuicao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este parceiro não está atribuído a esta jornada.")
    sessao.delete(atribuicao)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
