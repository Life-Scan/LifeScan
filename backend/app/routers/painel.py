from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import obter_usuario_atual
from app.db.sessao import obter_sessao
from app.models.usuario import PapelUsuario, Usuario
from app.schemas.painel import PainelMedico, PainelPaciente
from app.services.painel import montar_painel_medico, montar_painel_paciente

router = APIRouter(prefix="/dashboard", tags=["Painel"])


@router.get("/pending", response_model=PainelMedico | PainelPaciente)
def obter_pendencias(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> PainelMedico | PainelPaciente:
    """Pendências do usuário logado; o conteúdo depende do papel (RF14)."""
    if usuario.papel == PapelUsuario.medico:
        return montar_painel_medico(sessao, usuario)
    return montar_painel_paciente(sessao, usuario)
