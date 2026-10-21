from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    exigir_tipo,
    garantir_acompanhamento_editavel,
    obter_acompanhamento_com_acesso_de_parceiro,
    obter_acompanhamento_do_medico,
    obter_usuario_atual,
)
from app.db.sessao import obter_sessao
from app.models.atribuicao import AtribuicaoParceiro
from app.models.acompanhamento import Acompanhamento
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.acompanhamento import AcompanhamentoEntrada, AcompanhamentoSaida, PassoEntrada, StatusEntrada

router = APIRouter(prefix="/follow-ups", tags=["Acompanhamentos"])


@router.post("", response_model=AcompanhamentoSaida, status_code=status.HTTP_201_CREATED)
def criar_acompanhamento(
    dados: AcompanhamentoEntrada,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Acompanhamento:
    """Abre o acompanhamento de um paciente. Não depende de o paciente já ter acessado o sistema."""
    paciente = sessao.get(Usuario, dados.paciente_id)
    if paciente is None or paciente.tipo_usuario != TipoUsuario.paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")
    if not paciente.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "A conta deste paciente está desativada.")
    if sessao.scalar(select(Acompanhamento.id).where(Acompanhamento.paciente_id == paciente.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este paciente já possui um acompanhamento.")

    acompanhamento = Acompanhamento(
        medico_id=medico.id,
        paciente_id=paciente.id,
        titulo=dados.titulo,
        descricao=dados.descricao,
    )
    sessao.add(acompanhamento)
    sessao.commit()
    return acompanhamento


@router.get("", response_model=list[AcompanhamentoSaida])
def listar_acompanhamentos(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Acompanhamento]:
    """Médico: os acompanhamentos que conduz. Paciente: o próprio. Parceiro: os que lhe foram atribuídos."""
    consulta = select(Acompanhamento)
    if usuario.tipo_usuario == TipoUsuario.medico:
        consulta = consulta.where(Acompanhamento.medico_id == usuario.id)
    elif usuario.tipo_usuario == TipoUsuario.paciente:
        consulta = consulta.where(Acompanhamento.paciente_id == usuario.id)
    else:
        consulta = consulta.join(
            AtribuicaoParceiro, AtribuicaoParceiro.acompanhamento_id == Acompanhamento.id
        ).where(AtribuicaoParceiro.parceiro_id == usuario.id)
    return list(sessao.scalars(consulta.order_by(Acompanhamento.atualizado_em.desc())).all())


@router.get("/{acompanhamento_id}", response_model=AcompanhamentoSaida)
def obter_acompanhamento(acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro)) -> Acompanhamento:
    return acompanhamento


@router.patch("/{acompanhamento_id}/step", response_model=AcompanhamentoSaida)
def alterar_passo(
    dados: PassoEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Acompanhamento:
    """Altera o passo atual do acompanhamento entre consulta, exame e retorno."""
    garantir_acompanhamento_editavel(acompanhamento)
    acompanhamento.passo_atual = dados.passo_atual
    sessao.commit()
    return acompanhamento


@router.patch("/{acompanhamento_id}/status", response_model=AcompanhamentoSaida)
def alterar_status(
    dados: StatusEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Acompanhamento:
    """Encerra ou reabre o acompanhamento. Encerrado, ele fica somente leitura."""
    acompanhamento.status = dados.status
    sessao.commit()
    return acompanhamento
