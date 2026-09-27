from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import exigir_papel, obter_usuario_atual
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.usuario import PapelUsuario, Usuario
from app.models.vinculo import VinculoMedicoPaciente
from app.schemas.vinculo import VinculoAtualizacao, VinculoEntrada, VinculoSaida

router = APIRouter(prefix="/links", tags=["Vínculos"])


def _montar_saida(sessao: Session, vinculo: VinculoMedicoPaciente) -> VinculoSaida:
    saida = VinculoSaida.model_validate(vinculo)
    saida.jornada_id = sessao.scalar(
        select(Jornada.id).where(Jornada.paciente_id == vinculo.paciente_id)
    )
    return saida


@router.post("", response_model=VinculoSaida, status_code=status.HTTP_201_CREATED)
def criar_vinculo(
    dados: VinculoEntrada,
    medico: Usuario = Depends(exigir_papel(PapelUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> VinculoSaida:
    """Vincula um paciente cadastrado ao médico logado (RF03)."""
    paciente = sessao.get(Usuario, dados.paciente_id)
    if paciente is None or paciente.papel != PapelUsuario.paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")

    existente = sessao.scalar(
        select(VinculoMedicoPaciente).where(VinculoMedicoPaciente.paciente_id == paciente.id)
    )
    if existente is not None:
        if existente.medico_id == medico.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Este paciente já está vinculado a você.")
        raise HTTPException(status.HTTP_409_CONFLICT, "Este paciente já está vinculado a outro médico.")

    vinculo = VinculoMedicoPaciente(medico_id=medico.id, paciente_id=paciente.id)
    sessao.add(vinculo)
    sessao.commit()
    return _montar_saida(sessao, vinculo)


@router.get("", response_model=list[VinculoSaida])
def listar_vinculos(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[VinculoSaida]:
    """Médico: seus pacientes. Paciente: o vínculo com seu médico."""
    consulta = select(VinculoMedicoPaciente)
    if usuario.papel == PapelUsuario.medico:
        consulta = consulta.where(VinculoMedicoPaciente.medico_id == usuario.id)
    else:
        consulta = consulta.where(VinculoMedicoPaciente.paciente_id == usuario.id)
    vinculos = sessao.scalars(consulta.order_by(VinculoMedicoPaciente.criado_em.desc())).all()
    return [_montar_saida(sessao, vinculo) for vinculo in vinculos]


@router.patch("/{vinculo_id}", response_model=VinculoSaida)
def atualizar_vinculo(
    vinculo_id: int,
    dados: VinculoAtualizacao,
    medico: Usuario = Depends(exigir_papel(PapelUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> VinculoSaida:
    """Ativa ou desativa o vínculo. Sem vínculo ativo, a jornada fica inacessível (RNF10)."""
    vinculo = sessao.get(VinculoMedicoPaciente, vinculo_id)
    if vinculo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vínculo não encontrado.")
    if vinculo.medico_id != medico.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Este vínculo pertence a outro médico.")

    vinculo.ativo = dados.ativo
    sessao.commit()
    return _montar_saida(sessao, vinculo)
