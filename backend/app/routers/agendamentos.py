"""Agenda de consultas do médico, administrada pelo médico e pelos colaboradores."""

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import obter_configuracoes
from app.core.deps import exigir_tipo
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.acompanhamento import Acompanhamento, StatusAcompanhamento
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.consulta import Consulta
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.agendamento import (
    AgendamentoAtualizacao,
    AgendamentoEntrada,
    AgendamentoSaida,
    PacienteAgendavel,
    StatusAgendamentoEntrada,
)
from app.schemas.base import DataHoraEntrada
from app.schemas.paginacao import Pagina, Paginacao, paginar

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])

# Quem administra a agenda
exigir_equipe = exigir_tipo(TipoUsuario.medico, TipoUsuario.colaborador)

AGENDAMENTO_NAO_ENCONTRADO = "Agendamento não encontrado."


def _com_relacoes(consulta):
    return consulta.options(
        selectinload(Agendamento.acompanhamento).selectinload(Acompanhamento.paciente),
        selectinload(Agendamento.criado_por),
    )


def _ja_teve_primeira_consulta():
    """O acompanhamento tem ao menos uma consulta registrada pelo médico."""
    return exists().where(Consulta.acompanhamento_id == Acompanhamento.id)


def _acompanhamento_para_agendar(sessao: Session, paciente_id: int) -> Acompanhamento:
    """Acompanhamento do paciente, desde que ele possa ter consultas agendadas."""
    paciente = sessao.get(Usuario, paciente_id)
    if paciente is None or paciente.tipo_usuario != TipoUsuario.paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado.")
    if not paciente.ativo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A conta deste paciente está desativada.")
    acompanhamento = sessao.scalar(select(Acompanhamento).where(Acompanhamento.paciente_id == paciente_id))
    if acompanhamento is None or sessao.scalar(
        select(Consulta.id).where(Consulta.acompanhamento_id == acompanhamento.id).limit(1)
    ) is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Este paciente ainda não passou pela primeira consulta com o médico.",
        )
    _garantir_acompanhamento_ativo(acompanhamento)
    return acompanhamento


def _garantir_acompanhamento_ativo(acompanhamento: Acompanhamento) -> None:
    if acompanhamento.encerrado:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "O acompanhamento deste paciente está encerrado. Reabra-o para agendar consultas.",
        )


def _validar_horario(sessao: Session, data_hora: datetime, ignorar_id: int | None = None) -> None:
    """O horário precisa ser futuro e ficar a pelo menos o intervalo mínimo das outras consultas agendadas."""
    if data_hora <= agora_utc():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Escolha uma data e hora futuras.")
    horas = obter_configuracoes().horas_entre_agendamentos
    intervalo = timedelta(hours=horas)
    consulta = select(Agendamento.id).where(
        Agendamento.status == StatusAgendamento.agendada,
        # Estritamente dentro do intervalo: exatamente no limite é aceito
        Agendamento.data_hora > data_hora - intervalo,
        Agendamento.data_hora < data_hora + intervalo,
    )
    if ignorar_id is not None:
        consulta = consulta.where(Agendamento.id != ignorar_id)
    if sessao.scalar(consulta.limit(1)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Já existe uma consulta agendada a menos de {horas} horas deste horário. Escolha outro horário.",
        )


def _obter_agendamento(sessao: Session, agendamento_id: int) -> Agendamento:
    agendamento = sessao.scalar(_com_relacoes(select(Agendamento).where(Agendamento.id == agendamento_id)))
    if agendamento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, AGENDAMENTO_NAO_ENCONTRADO)
    return agendamento


def _garantir_agendada(agendamento: Agendamento) -> None:
    if agendamento.status != StatusAgendamento.agendada:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta consulta não está mais agendada.")


@router.get("/patients", response_model=Pagina[PacienteAgendavel] | list[PacienteAgendavel])
def listar_pacientes_agendaveis(
    busca: str | None = Query(None, max_length=255, description="Parte do nome ou email"),
    paginacao: Paginacao = Depends(),
    _: Usuario = Depends(exigir_equipe),
    sessao: Session = Depends(obter_sessao),
):
    """Pacientes ativos, com acompanhamento ativo e que já passaram pela primeira consulta."""
    consulta = (
        select(Usuario)
        .join(Acompanhamento, Acompanhamento.paciente_id == Usuario.id)
        .where(
            Usuario.tipo_usuario == TipoUsuario.paciente,
            Usuario.ativo.is_(True),
            Acompanhamento.status == StatusAcompanhamento.ativo,
            _ja_teve_primeira_consulta(),
        )
    )
    termo = busca.strip() if busca else ""
    if termo:
        consulta = consulta.where(or_(
            Usuario.nome.icontains(termo, autoescape=True),
            Usuario.email.icontains(termo, autoescape=True),
        ))
    return paginar(sessao, consulta.order_by(Usuario.nome, Usuario.id), paginacao)


@router.get("", response_model=Pagina[AgendamentoSaida] | list[AgendamentoSaida])
def listar_agendamentos(
    inicio: DataHoraEntrada | None = Query(None, description="A partir desta data e hora"),
    fim: DataHoraEntrada | None = Query(None, description="Antes desta data e hora"),
    status_filtro: StatusAgendamento | None = Query(None, alias="status"),
    ordem: Literal["asc", "desc"] = Query("asc", description="asc: mais cedo primeiro; desc: mais recente primeiro"),
    paginacao: Paginacao = Depends(),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.medico, TipoUsuario.colaborador, TipoUsuario.paciente)),
    sessao: Session = Depends(obter_sessao),
):
    """Médico e colaborador veem a agenda inteira; o paciente, só as próprias consultas."""
    consulta = _com_relacoes(select(Agendamento))
    if usuario.tipo_usuario == TipoUsuario.paciente:
        consulta = consulta.join(Acompanhamento, Acompanhamento.id == Agendamento.acompanhamento_id).where(
            Acompanhamento.paciente_id == usuario.id
        )
    if inicio is not None:
        consulta = consulta.where(Agendamento.data_hora >= inicio)
    if fim is not None:
        consulta = consulta.where(Agendamento.data_hora < fim)
    if status_filtro is not None:
        consulta = consulta.where(Agendamento.status == status_filtro)
    if ordem == "desc":
        consulta = consulta.order_by(Agendamento.data_hora.desc(), Agendamento.id.desc())
    else:
        consulta = consulta.order_by(Agendamento.data_hora, Agendamento.id)
    return paginar(sessao, consulta, paginacao)


@router.post("", response_model=AgendamentoSaida, status_code=status.HTTP_201_CREATED)
def agendar_consulta(
    dados: AgendamentoEntrada,
    usuario: Usuario = Depends(exigir_equipe),
    sessao: Session = Depends(obter_sessao),
) -> Agendamento:
    acompanhamento = _acompanhamento_para_agendar(sessao, dados.paciente_id)
    _validar_horario(sessao, dados.data_hora)
    agendamento = Agendamento(
        acompanhamento_id=acompanhamento.id,
        data_hora=dados.data_hora,
        observacao=dados.observacao or None,
        criado_por_id=usuario.id,
    )
    sessao.add(agendamento)
    sessao.commit()
    return _obter_agendamento(sessao, agendamento.id)


@router.patch("/{agendamento_id}", response_model=AgendamentoSaida)
def remarcar_consulta(
    agendamento_id: int,
    dados: AgendamentoAtualizacao,
    _: Usuario = Depends(exigir_equipe),
    sessao: Session = Depends(obter_sessao),
) -> Agendamento:
    """Muda a data e hora (remarcação) ou a observação de uma consulta ainda agendada."""
    agendamento = _obter_agendamento(sessao, agendamento_id)
    _garantir_agendada(agendamento)
    if dados.data_hora is not None and dados.data_hora != agendamento.data_hora:
        _garantir_acompanhamento_ativo(agendamento.acompanhamento)
        _validar_horario(sessao, dados.data_hora, ignorar_id=agendamento.id)
        agendamento.data_hora = dados.data_hora
    if "observacao" in dados.model_fields_set:
        agendamento.observacao = dados.observacao or None
    sessao.commit()
    return _obter_agendamento(sessao, agendamento.id)


@router.patch("/{agendamento_id}/status", response_model=AgendamentoSaida)
def alterar_status(
    agendamento_id: int,
    dados: StatusAgendamentoEntrada,
    _: Usuario = Depends(exigir_equipe),
    sessao: Session = Depends(obter_sessao),
) -> Agendamento:
    """Cancela a consulta a qualquer momento, ou registra, depois do horário, se ela foi realizada ou se o paciente faltou."""
    agendamento = _obter_agendamento(sessao, agendamento_id)
    _garantir_agendada(agendamento)
    if dados.status == StatusAgendamento.agendada:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A consulta já está agendada.")
    if dados.status in (StatusAgendamento.realizada, StatusAgendamento.faltou) and agendamento.data_hora > agora_utc():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Só é possível marcar a consulta como realizada ou falta depois do horário dela.",
        )
    agendamento.status = dados.status
    sessao.commit()
    return _obter_agendamento(sessao, agendamento.id)
