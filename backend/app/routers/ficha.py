from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import obter_jornada_com_acesso_de_parceiro, obter_jornada_do_medico
from app.db.sessao import obter_sessao
from app.models.ficha import FichaPaciente
from app.models.jornada import Jornada
from app.schemas.ficha import FichaEntrada, FichaSaida
from app.schemas.usuario import UsuarioResumo

router = APIRouter(prefix="/journeys/{jornada_id}/patient-record", tags=["Ficha do paciente"])

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


def _montar_saida(jornada: Jornada, ficha: FichaPaciente | None) -> FichaSaida:
    paciente = UsuarioResumo.model_validate(jornada.paciente)
    if ficha is None:
        return FichaSaida(paciente=paciente, preenchida=False)
    return FichaSaida(
        paciente=paciente,
        preenchida=True,
        idade=_calcular_idade(ficha.data_nascimento),
        atualizado_em=ficha.atualizado_em,
        **{campo: getattr(ficha, campo) for campo in CAMPOS},
    )


def _obter_ficha(sessao: Session, jornada: Jornada) -> FichaPaciente | None:
    return sessao.scalar(select(FichaPaciente).where(FichaPaciente.paciente_id == jornada.paciente_id))


@router.get("", response_model=FichaSaida)
def obter_ficha(
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    sessao: Session = Depends(obter_sessao),
) -> FichaSaida:
    """Ficha do paciente: visível ao médico, ao próprio paciente e aos parceiros atribuídos."""
    return _montar_saida(jornada, _obter_ficha(sessao, jornada))


@router.put("", response_model=FichaSaida)
def salvar_ficha(
    dados: FichaEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> FichaSaida:
    """O médico cria ou substitui a ficha inteira.

    Continua editável com a jornada encerrada: a ficha descreve o paciente, não o tratamento.
    """
    ficha = _obter_ficha(sessao, jornada)
    if ficha is None:
        ficha = FichaPaciente(paciente_id=jornada.paciente_id)
        sessao.add(ficha)

    for campo in CAMPOS:
        valor = getattr(dados, campo)
        if campo in CAMPOS_DE_TEXTO:
            valor = valor or None
        setattr(ficha, campo, valor)
    sessao.commit()
    return _montar_saida(jornada, ficha)
