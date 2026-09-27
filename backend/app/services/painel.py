"""Painel de pendências do médico e do paciente (RF14).

Considera apenas jornadas ativas (não encerradas) com vínculo ativo.
"""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.db.base import agora_utc
from app.models.exame import Exame, StatusExame
from app.models.jornada import Jornada, StatusJornada
from app.models.mensagem import Mensagem
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import PapelUsuario, Usuario
from app.models.vinculo import VinculoMedicoPaciente
from app.schemas.exame import ExameSaida
from app.schemas.mensagem import MensagemSaida
from app.schemas.painel import (
    ExamePendente,
    JornadaResumo,
    MensagemPendente,
    PainelMedico,
    PainelPaciente,
    SolicitacaoPendente,
)
from app.schemas.solicitacao import SolicitacaoSaida


def _jornadas_em_andamento(sessao: Session, usuario: Usuario) -> dict[int, Jornada]:
    consulta = (
        select(Jornada)
        .join(
            VinculoMedicoPaciente,
            (VinculoMedicoPaciente.medico_id == Jornada.medico_id)
            & (VinculoMedicoPaciente.paciente_id == Jornada.paciente_id)
            & VinculoMedicoPaciente.ativo.is_(True),
        )
        .where(Jornada.status == StatusJornada.ativa)
    )
    if usuario.papel == PapelUsuario.medico:
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

    # Uma conversa está "sem resposta" quando a última mensagem foi do paciente
    ultimas_ids = (
        select(func.max(Mensagem.id))
        .where(Mensagem.jornada_id.in_(jornadas))
        .group_by(Mensagem.jornada_id)
    )
    ultimas = sessao.scalars(
        select(Mensagem).where(Mensagem.id.in_(ultimas_ids)).order_by(Mensagem.criado_em)
    )
    sem_resposta = [m for m in ultimas if m.remetente_id == jornadas[m.jornada_id].paciente_id]

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
        mensagens_nao_respondidas=[
            MensagemPendente(
                jornada=JornadaResumo.model_validate(jornadas[mensagem.jornada_id]),
                ultima_mensagem=MensagemSaida.model_validate(mensagem),
            )
            for mensagem in sem_resposta
        ],
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
