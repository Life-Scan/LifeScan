"""Monta a linha do tempo unificada da jornada."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consulta import Consulta, TipoConsulta
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.schemas.consulta import ConsultaSaida
from app.schemas.documento import DocumentoSaida
from app.schemas.linha_do_tempo import EventoLinhaDoTempo, TipoEvento
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

ROTULOS_CATEGORIA = {
    CategoriaDocumento.exame: "exame",
    CategoriaDocumento.laudo: "laudo",
    CategoriaDocumento.plano_alimentar: "plano alimentar",
    CategoriaDocumento.plano_treino: "plano de treino",
    CategoriaDocumento.orientacao: "orientação",
    CategoriaDocumento.outro: "documento",
}

# Desempate para eventos com a mesma data/hora
ORDEM_TIPOS = {
    TipoEvento.consulta: 0,
    TipoEvento.solicitacao: 1,
    TipoEvento.documento: 2,
}


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


def _eventos_de_solicitacoes(
    solicitacoes: Iterable[Solicitacao], jornada: Jornada
) -> list[EventoLinhaDoTempo]:
    eventos = []
    for solicitacao in solicitacoes:
        situacao = "vencida" if solicitacao.vencida else ROTULOS_STATUS_SOLICITACAO[solicitacao.status]
        # Só menciona o destinatário quando não é o próprio paciente
        para = (
            f" para {solicitacao.destinatario.nome}"
            if solicitacao.destinatario_id != jornada.paciente_id
            else ""
        )
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.solicitacao,
                id=solicitacao.id,
                data=solicitacao.criado_em,
                resumo=(
                    f"Solicitação de {ROTULOS_SOLICITACAO[solicitacao.tipo]}{para}: "
                    f"{_encurtar(solicitacao.descricao, 80)} ({situacao})"
                ),
                dados=SolicitacaoSaida.model_validate(solicitacao).model_dump(mode="json"),
            )
        )
    return eventos


def _eventos_de_documentos(documentos: Iterable[Documento]) -> list[EventoLinhaDoTempo]:
    eventos = []
    for documento in documentos:
        resumo = (
            f"{documento.enviado_por.nome} enviou {ROTULOS_CATEGORIA[documento.categoria]}: {documento.titulo}"
        )
        if documento.status == StatusDocumento.revisado:
            resumo += " (revisado)"
        eventos.append(
            EventoLinhaDoTempo(
                tipo=TipoEvento.documento,
                id=documento.id,
                data=documento.criado_em,
                resumo=resumo,
                dados=DocumentoSaida.model_validate(documento).model_dump(mode="json"),
            )
        )
    return eventos


def montar_linha_do_tempo(
    sessao: Session, jornada: Jornada, tipos: set[TipoEvento] | None = None
) -> list[EventoLinhaDoTempo]:
    """Reúne consultas, solicitações e documentos em ordem cronológica.

    Datas usadas: consulta = data da consulta; demais = momento em que foram criados.
    """
    tipos = tipos or set(TipoEvento)
    eventos: list[EventoLinhaDoTempo] = []

    if TipoEvento.consulta in tipos:
        consultas = sessao.scalars(select(Consulta).where(Consulta.jornada_id == jornada.id))
        eventos += _eventos_de_consultas(consultas)
    if TipoEvento.solicitacao in tipos:
        solicitacoes = sessao.scalars(select(Solicitacao).where(Solicitacao.jornada_id == jornada.id))
        eventos += _eventos_de_solicitacoes(solicitacoes, jornada)
    if TipoEvento.documento in tipos:
        documentos = sessao.scalars(select(Documento).where(Documento.jornada_id == jornada.id))
        eventos += _eventos_de_documentos(documentos)

    eventos.sort(key=lambda evento: (evento.data, ORDEM_TIPOS[evento.tipo], evento.id))
    return eventos
