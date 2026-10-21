from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import garantir_acompanhamento_editavel, obter_acompanhamento_com_acesso, obter_acompanhamento_do_medico
from app.db.sessao import obter_sessao
from app.models.consulta import Consulta, Prescricao
from app.models.acompanhamento import Acompanhamento
from app.schemas.consulta import ConsultaEntrada, ConsultaSaida
from app.schemas.paginacao import Pagina, Paginacao, paginar
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/follow-ups/{acompanhamento_id}/consultations", tags=["Consultas"])


@router.post("", response_model=ConsultaSaida, status_code=status.HTTP_201_CREATED)
def registrar_consulta(
    dados: ConsultaEntrada,
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_do_medico),
    sessao: Session = Depends(obter_sessao),
) -> Consulta:
    """Registra uma consulta ou retorno, com as prescrições (RF10, RF13)."""
    garantir_acompanhamento_editavel(acompanhamento)
    consulta = Consulta(
        acompanhamento_id=acompanhamento.id,
        tipo=dados.tipo,
        data=dados.data,
        anotacoes=dados.anotacoes,
        prescricoes=[Prescricao(**prescricao.model_dump()) for prescricao in dados.prescricoes],
    )
    sessao.add(consulta)
    sessao.commit()
    return consulta


@router.get("", response_model=Pagina[ConsultaSaida] | list[ConsultaSaida])
def listar_consultas(
    paginacao: Paginacao = Depends(),
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso),
    sessao: Session = Depends(obter_sessao),
):
    consulta = (
        select(Consulta).options(selectinload(Consulta.prescricoes))
        .where(Consulta.acompanhamento_id == acompanhamento.id)
        .order_by(Consulta.data.desc(), Consulta.id.desc())
    )
    return paginar(sessao, consulta, paginacao)
