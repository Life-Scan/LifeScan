from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    exigir_tipo,
    garantir_jornada_editavel,
    obter_jornada_com_acesso_de_parceiro,
    obter_jornada_do_medico,
    obter_usuario_atual,
)
from app.db.sessao import obter_sessao
from app.models.atribuicao import AtribuicaoParceiro
from app.models.jornada import Jornada
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.jornada import JornadaEntrada, JornadaSaida, PassoEntrada, StatusEntrada

router = APIRouter(prefix="/journeys", tags=["Jornadas"])


@router.post("", response_model=JornadaSaida, status_code=status.HTTP_201_CREATED)
def criar_jornada(
    dados: JornadaEntrada,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Abre a jornada de um paciente. Não depende de o paciente já ter acessado o sistema."""
    paciente = sessao.get(Usuario, dados.paciente_id)
    if paciente is None or paciente.tipo_usuario != TipoUsuario.paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")
    if not paciente.ativo:
        raise HTTPException(status.HTTP_409_CONFLICT, "A conta deste paciente está desativada.")
    if sessao.scalar(select(Jornada.id).where(Jornada.paciente_id == paciente.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este paciente já possui uma jornada.")

    jornada = Jornada(
        medico_id=medico.id,
        paciente_id=paciente.id,
        titulo=dados.titulo,
        descricao=dados.descricao,
    )
    sessao.add(jornada)
    sessao.commit()
    return jornada


@router.get("", response_model=list[JornadaSaida])
def listar_jornadas(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Jornada]:
    """Médico: as jornadas que conduz. Paciente: a própria. Parceiro: as que lhe foram atribuídas."""
    consulta = select(Jornada)
    if usuario.tipo_usuario == TipoUsuario.medico:
        consulta = consulta.where(Jornada.medico_id == usuario.id)
    elif usuario.tipo_usuario == TipoUsuario.paciente:
        consulta = consulta.where(Jornada.paciente_id == usuario.id)
    else:
        consulta = consulta.join(
            AtribuicaoParceiro, AtribuicaoParceiro.jornada_id == Jornada.id
        ).where(AtribuicaoParceiro.parceiro_id == usuario.id)
    return list(sessao.scalars(consulta.order_by(Jornada.atualizado_em.desc())).all())


@router.get("/{jornada_id}", response_model=JornadaSaida)
def obter_jornada(jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro)) -> Jornada:
    return jornada


@router.patch("/{jornada_id}/step", response_model=JornadaSaida)
def alterar_passo(
    dados: PassoEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Altera o passo atual da jornada entre consulta, exame e retorno."""
    garantir_jornada_editavel(jornada)
    jornada.passo_atual = dados.passo_atual
    sessao.commit()
    return jornada


@router.patch("/{jornada_id}/status", response_model=JornadaSaida)
def alterar_status(
    dados: StatusEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Encerra ou reabre a jornada. Encerrada, ela fica somente leitura."""
    jornada.status = dados.status
    sessao.commit()
    return jornada
