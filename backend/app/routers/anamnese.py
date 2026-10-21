from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import obter_acompanhamento_com_acesso_de_parceiro, obter_acompanhamento_do_medico
from app.db.sessao import obter_sessao
from app.models.anamnese import Anamnese
from app.models.acompanhamento import Acompanhamento
from app.schemas.anamnese import AnamneseEntrada, AnamneseSaida
from app.schemas.usuario import UsuarioResumo

router = APIRouter(prefix="/follow-ups/{acompanhamento_id}/anamnesis", tags=["Anamnese do paciente"])

CAMPOS_DE_TEXTO = (
    "diagnosticos",
    "alergias",
    "medicamentos_em_uso",
    "restricoes",
    "objetivos",
    "observacoes",
)
CAMPOS = ("data_nascimento", "sexo", "altura_cm", "peso_kg", *CAMPOS_DE_TEXTO)


def _calcular_idade(nascimento: date | None) -> int | None:
    if nascimento is None:
        return None
    hoje = date.today()
    ainda_nao_fez_aniversario = (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
    return hoje.year - nascimento.year - ainda_nao_fez_aniversario


def _montar_saida(acompanhamento: Acompanhamento, anamnese: Anamnese | None) -> AnamneseSaida:
    paciente = UsuarioResumo.model_validate(acompanhamento.paciente)
    if anamnese is None:
        return AnamneseSaida(paciente=paciente, preenchida=False)
    return AnamneseSaida(
        paciente=paciente,
        preenchida=True,
        idade=_calcular_idade(anamnese.data_nascimento),
        atualizado_em=anamnese.atualizado_em,
        **{campo: getattr(anamnese, campo) for campo in CAMPOS},
    )


def _obter_anamnese(sessao: Session, acompanhamento: Acompanhamento) -> Anamnese | None:
    return sessao.scalar(select(Anamnese).where(Anamnese.paciente_id == acompanhamento.paciente_id))


@router.get("", response_model=AnamneseSaida)
def obter_anamnese(
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro),
    sessao: Session = Depends(obter_sessao),
) -> AnamneseSaida:
    """Anamnese do paciente: visível ao médico, ao próprio paciente e aos parceiros atribuídos."""
    return _montar_saida(acompanhamento, _obter_anamnese(sessao, acompanhamento))


@router.put("", response_model=AnamneseSaida)
def salvar_anamnese(
    dados: AnamneseEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> AnamneseSaida:
    """O médico cria ou substitui a anamnese inteira.

    Continua editável com o acompanhamento encerrado: a anamnese descreve o paciente, não o tratamento.
    """
    anamnese = _obter_anamnese(sessao, acompanhamento)
    if anamnese is None:
        anamnese = Anamnese(paciente_id=acompanhamento.paciente_id)
        sessao.add(anamnese)

    for campo in CAMPOS:
        valor = getattr(dados, campo)
        if campo in CAMPOS_DE_TEXTO:
            valor = valor or None
        setattr(anamnese, campo, valor)
    sessao.commit()
    return _montar_saida(acompanhamento, anamnese)
