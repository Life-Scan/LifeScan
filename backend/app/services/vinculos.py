from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vinculo import VinculoMedicoPaciente


def vinculo_ativo_entre(sessao: Session, medico_id: int, paciente_id: int) -> bool:
    return (
        sessao.scalar(
            select(VinculoMedicoPaciente.id).where(
                VinculoMedicoPaciente.medico_id == medico_id,
                VinculoMedicoPaciente.paciente_id == paciente_id,
                VinculoMedicoPaciente.ativo.is_(True),
            )
        )
        is not None
    )
