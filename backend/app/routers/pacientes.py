from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import exigir_papel
from app.db.sessao import obter_sessao
from app.models.usuario import PapelUsuario, Usuario
from app.models.vinculo import VinculoMedicoPaciente
from app.schemas.vinculo import PacienteBuscaSaida

router = APIRouter(prefix="/patients", tags=["Pacientes"])


@router.get("/search", response_model=PacienteBuscaSaida)
def buscar_paciente(
    email: str = Query(..., min_length=3),
    medico: Usuario = Depends(exigir_papel(PapelUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> PacienteBuscaSaida:
    """Busca um paciente cadastrado pelo email exato (RF03)."""
    paciente = sessao.scalar(
        select(Usuario).where(
            Usuario.email == email.strip().lower(),
            Usuario.papel == PapelUsuario.paciente,
        )
    )
    if paciente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhum paciente encontrado com este email.")

    vinculo = sessao.scalar(
        select(VinculoMedicoPaciente).where(VinculoMedicoPaciente.paciente_id == paciente.id)
    )
    return PacienteBuscaSaida(
        id=paciente.id,
        nome=paciente.nome,
        email=paciente.email,
        vinculado_a_mim=vinculo is not None and vinculo.medico_id == medico.id,
        vinculado_a_outro_medico=vinculo is not None and vinculo.medico_id != medico.id,
    )
