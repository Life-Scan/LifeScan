from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import garantir_jornada_editavel, obter_jornada_com_acesso, obter_jornada_do_medico
from app.db.sessao import obter_sessao
from app.models.consulta import Consulta, Prescricao
from app.models.jornada import Jornada
from app.schemas.consulta import ConsultaEntrada, ConsultaSaida

router = APIRouter(prefix="/journeys/{jornada_id}/consultations", tags=["Consultas"])


@router.post("", response_model=ConsultaSaida, status_code=status.HTTP_201_CREATED)
def registrar_consulta(
    dados: ConsultaEntrada,
    jornada: Jornada = Depends(obter_jornada_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Consulta:
    """Registra uma consulta ou retorno, com as prescrições (RF10, RF13)."""
    garantir_jornada_editavel(jornada)
    consulta = Consulta(
        jornada_id=jornada.id,
        tipo=dados.tipo,
        data=dados.data,
        anotacoes=dados.anotacoes,
        prescricoes=[Prescricao(**prescricao.model_dump()) for prescricao in dados.prescricoes],
    )
    sessao.add(consulta)
    sessao.commit()
    return consulta


@router.get("", response_model=list[ConsultaSaida])
def listar_consultas(
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[Consulta]:
    consulta = (
        select(Consulta)
        .where(Consulta.jornada_id == jornada.id)
        .order_by(Consulta.data.desc(), Consulta.id.desc())
    )
    return list(sessao.scalars(consulta).all())
