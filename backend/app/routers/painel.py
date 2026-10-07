from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import obter_usuario_atual
from app.db.sessao import obter_sessao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.painel import PainelMedico, PainelPaciente, PainelParceiro
from app.services.painel import (
    montar_painel_medico,
    montar_painel_paciente,
    montar_painel_parceiro,
)

router = APIRouter(prefix="/dashboard", tags=["Painel"])


@router.get("/pending", response_model=PainelMedico | PainelPaciente | PainelParceiro)
def obter_pendencias(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> PainelMedico | PainelPaciente | PainelParceiro:
    """Pendências do usuário logado; o conteúdo depende do tipo de usuário."""
    if usuario.tipo_usuario == TipoUsuario.medico:
        return montar_painel_medico(sessao, usuario)
    if usuario.tipo_usuario == TipoUsuario.paciente:
        return montar_painel_paciente(sessao, usuario)
    return montar_painel_parceiro(sessao, usuario)
