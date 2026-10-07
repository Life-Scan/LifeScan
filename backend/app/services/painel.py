"""Painel de pendências por tipo de usuário.

Considera apenas jornadas ativas (não encerradas).
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.db.base import agora_utc
from app.models.exame import Exame, StatusExame
from app.models.jornada import Jornada, StatusJornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.exame import ExameSaida
from app.schemas.painel import (
    ExamePendente,
    JornadaResumo,
    PainelMedico,
    PainelPaciente,
    PainelParceiro,
    SolicitacaoPendente,
)
from app.schemas.solicitacao import SolicitacaoSaida


def _jornadas_em_andamento(sessao: Session, usuario: Usuario) -> dict[int, Jornada]:
    consulta = select(Jornada).where(Jornada.status == StatusJornada.ativa)
    if usuario.tipo_usuario == TipoUsuario.medico:
        consulta = consulta.where(Jornada.medico_id == usuario.id)
    else:
        consulta = consulta.where(Jornada.paciente_id == usuario.id)
    return {jornada.id: jornada for jornada in sessao.scalars(consulta)}


def _solicitacoes_pendentes(sessao: Session, jornadas: dict[int, Jornada]) -> list[Solicitacao]:
    consulta = (
        select(Solicitacao)
        .where(
            Solicitacao.jornada_id.in_(jornadas),
            Solicitacao.status == StatusSolicitacao.pendente,
        )
        .order_by(Solicitacao.prazo, Solicitacao.id)
    )
    return list(sessao.scalars(consulta))


def _item_solicitacao(solicitacao: Solicitacao, jornadas: dict[int, Jornada]) -> SolicitacaoPendente:
    return SolicitacaoPendente(
        **SolicitacaoSaida.model_validate(solicitacao).model_dump(),
        jornada=JornadaResumo.model_validate(jornadas[solicitacao.jornada_id]),
    )


def montar_painel_medico(sessao: Session, medico: Usuario) -> PainelMedico:
    config = obter_configuracoes()
    jornadas = _jornadas_em_andamento(sessao, medico)
    agora = agora_utc()
    limite_proximo = agora + timedelta(days=config.dias_prazo_proximo)

    exames = sessao.scalars(
        select(Exame)
        .where(
            Exame.jornada_id.in_(jornadas),
            Exame.status == StatusExame.enviado,
            # Arquivos que o próprio médico enviou não precisam da revisão dele
            Exame.enviado_por_id != medico.id,
        )
        .order_by(Exame.criado_em, Exame.id)
    )

    pendentes = _solicitacoes_pendentes(sessao, jornadas)
    vencidas = [s for s in pendentes if s.prazo < agora]
    proximas = [s for s in pendentes if agora <= s.prazo <= limite_proximo]

    return PainelMedico(
        dias_prazo_proximo=config.dias_prazo_proximo,
        exames_aguardando_revisao=[
            ExamePendente(
                **ExameSaida.model_validate(exame).model_dump(),
                jornada=JornadaResumo.model_validate(jornadas[exame.jornada_id]),
            )
            for exame in exames
        ],
        solicitacoes_vencidas=[_item_solicitacao(s, jornadas) for s in vencidas],
        solicitacoes_proximas_do_prazo=[_item_solicitacao(s, jornadas) for s in proximas],
    )


def montar_painel_paciente(sessao: Session, paciente: Usuario) -> PainelPaciente:
    jornadas = _jornadas_em_andamento(sessao, paciente)
    pendentes = _solicitacoes_pendentes(sessao, jornadas)
    # Ordenadas por prazo, as vencidas naturalmente aparecem primeiro
    return PainelPaciente(
        solicitacoes_pendentes=[
            _item_solicitacao(s, jornadas) for s in pendentes if s.tipo != TipoSolicitacao.consulta_extra
        ],
        consultas_extras=[
            _item_solicitacao(s, jornadas) for s in pendentes if s.tipo == TipoSolicitacao.consulta_extra
        ],
    )


def montar_painel_parceiro(sessao: Session, parceiro: Usuario) -> PainelParceiro:
    # Ainda sem pendências: o parceiro passa a ter jornadas na fase de atribuição
    return PainelParceiro(solicitacoes_pendentes=[])
