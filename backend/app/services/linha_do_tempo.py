"""Monta a linha do tempo unificada da jornada (RF12)."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consulta import Consulta, TipoConsulta
from app.models.exame import Exame, StatusExame
from app.models.jornada import Jornada
from app.models.mensagem import Mensagem
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.schemas.consulta import ConsultaSaida
from app.schemas.exame import ExameSaida
from app.schemas.linha_do_tempo import EventoLinhaDoTempo, TipoEvento
from app.schemas.mensagem import MensagemSaida
from app.schemas.solicitacao import SolicitacaoSaida

ROTULOS_SOLICITACAO = {
    TipoSolicitacao.exame: "exame",
    TipoSolicitacao.consulta_extra: "consulta extra",
    TipoSolicitacao.orientacao_profissional: "orientação de outro profissional",
    TipoSolicitacao.outro: "outro",
}

ROTULOS_STATUS_SOLICITACAO = {
    StatusSolicitacao.pendente: "pendente",
    StatusSolicitacao.atendida: "atendida",
    StatusSolicitacao.cancelada: "cancelada",
}

# Desempate para eventos com a mesma data/hora
ORDEM_TIPOS = {
    TipoEvento.consulta: 0,
    TipoEvento.solicitacao: 1,
    TipoEvento.exame: 2,
    TipoEvento.mensagem: 3,
}

TAMANHO_MAXIMO_RESUMO_MENSAGEM = 80


def _encurtar(texto: str, limite: int) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def _eventos_de_consultas(consultas: Iterable[Consulta]) -> list[EventoLinhaDoTempo]:
    eventos = []
    for consulta in consultas:
        rotulo = "Consulta realizada" if consulta.tipo == TipoConsulta.consulta else "Retorno realizado"
        quantidade = len(consulta.prescricoes)
        if quantidade:
            rotulo += f" ({quantidade} {'prescrição' if quantidade == 1 else 'prescrições'})"
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.consulta,
                id=consulta.id,
                data=consulta.data,
                resumo=rotulo,
                dados=ConsultaSaida.model_validate(consulta).model_dump(mode="json"),
            )
        )
    return eventos


def _eventos_de_solicitacoes(solicitacoes: Iterable[Solicitacao]) -> list[EventoLinhaDoTempo]:
    eventos = []
    for solicitacao in solicitacoes:
        situacao = "vencida" if solicitacao.vencida else ROTULOS_STATUS_SOLICITACAO[solicitacao.status]
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.solicitacao,
                id=solicitacao.id,
                data=solicitacao.criado_em,
                resumo=(
                    f"Solicitação de {ROTULOS_SOLICITACAO[solicitacao.tipo]}: "
                    f"{_encurtar(solicitacao.descricao, 80)} ({situacao})"
                ),
                dados=SolicitacaoSaida.model_validate(solicitacao).model_dump(mode="json"),
            )
        )
    return eventos


def _eventos_de_exames(exames: Iterable[Exame]) -> list[EventoLinhaDoTempo]:
    eventos = []
    for exame in exames:
        resumo = f"{exame.enviado_por.nome} enviou: {exame.titulo}"
        if exame.status == StatusExame.revisado:
            resumo += " (revisado)"
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.exame,
                id=exame.id,
                data=exame.criado_em,
                resumo=resumo,
                dados=ExameSaida.model_validate(exame).model_dump(mode="json"),
            )
        )
    return eventos


def _eventos_de_mensagens(mensagens: Iterable[Mensagem]) -> list[EventoLinhaDoTempo]:
    eventos = []
    for mensagem in mensagens:
        nome = mensagem.remetente.nome
        if mensagem.conteudo:
            resumo = f"{nome}: {_encurtar(mensagem.conteudo, TAMANHO_MAXIMO_RESUMO_MENSAGEM)}"
            if mensagem.arquivo is not None:
                resumo += " (com anexo)"
        else:
            resumo = f"{nome} enviou um anexo: {mensagem.arquivo.nome_original}"
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.mensagem,
                id=mensagem.id,
                data=mensagem.criado_em,
                resumo=resumo,
                dados=MensagemSaida.model_validate(mensagem).model_dump(mode="json"),
            )
        )
    return eventos


def montar_linha_do_tempo(
    sessao: Session, jornada: Jornada, tipos: set[TipoEvento] | None = None
) -> list[EventoLinhaDoTempo]:
    """Reúne consultas, solicitações, exames e mensagens em ordem cronológica.

    Datas usadas: consulta = data da consulta; demais = momento em que foram criadas.
    """
    tipos = tipos or set(TipoEvento)
    eventos: list[EventoLinhaDoTempo] = []

    if TipoEvento.consulta in tipos:
        consultas = sessao.scalars(select(Consulta).where(Consulta.jornada_id == jornada.id))
        eventos += _eventos_de_consultas(consultas)
    if TipoEvento.solicitacao in tipos:
        solicitacoes = sessao.scalars(select(Solicitacao).where(Solicitacao.jornada_id == jornada.id))
        eventos += _eventos_de_solicitacoes(solicitacoes)
    if TipoEvento.exame in tipos:
        exames = sessao.scalars(select(Exame).where(Exame.jornada_id == jornada.id))
        eventos += _eventos_de_exames(exames)
    if TipoEvento.mensagem in tipos:
        mensagens = sessao.scalars(select(Mensagem).where(Mensagem.jornada_id == jornada.id))
        eventos += _eventos_de_mensagens(mensagens)

    eventos.sort(key=lambda evento: (evento.data, ORDEM_TIPOS[evento.tipo], evento.id))
    return eventos
