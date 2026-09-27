from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    exigir_papel,
    garantir_jornada_editavel,
    obter_jornada_com_acesso,
    obter_jornada_do_medico,
    obter_usuario_atual,
)
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.usuario import PapelUsuario, Usuario
from app.models.vinculo import VinculoMedicoPaciente
from app.schemas.jornada import JornadaEntrada, JornadaSaida, PassoEntrada, StatusEntrada
from app.services.vinculos import vinculo_ativo_entre

router = APIRouter(prefix="/journeys", tags=["Jornadas"])


@router.post("", response_model=JornadaSaida, status_code=status.HTTP_201_CREATED)
def criar_jornada(
    dados: JornadaEntrada,
    medico: Usuario = Depends(exigir_papel(PapelUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Abre a jornada de um paciente vinculado ao médico (RF04)."""
    paciente = sessao.get(Usuario, dados.paciente_id)
    if paciente is None or paciente.papel != PapelUsuario.paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")
    if not vinculo_ativo_entre(sessao, medico.id, paciente.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Só é possível abrir jornada para um paciente com vínculo ativo com você.",
        )
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
    """Jornadas do usuário logado cujo vínculo está ativo."""
    consulta = select(Jornada).join(
        VinculoMedicoPaciente,
        (VinculoMedicoPaciente.medico_id == Jornada.medico_id)
        & (VinculoMedicoPaciente.paciente_id == Jornada.paciente_id)
        & VinculoMedicoPaciente.ativo.is_(True),
    )
    if usuario.papel == PapelUsuario.medico:
        consulta = consulta.where(Jornada.medico_id == usuario.id)
    else:
        consulta = consulta.where(Jornada.paciente_id == usuario.id)
    return list(sessao.scalars(consulta.order_by(Jornada.atualizado_em.desc())).all())


@router.get("/{jornada_id}", response_model=JornadaSaida)
def obter_jornada(jornada: Jornada = Depends(obter_jornada_com_acesso)) -> Jornada:
    return jornada


@router.patch("/{jornada_id}/step", response_model=JornadaSaida)
def alterar_passo(
    dados: PassoEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Jornada:
    """Altera o passo atual da jornada entre consulta, exame e retorno (RF05)."""
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
