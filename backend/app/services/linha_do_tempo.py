"""Monta a linha do tempo unificada da jornada."""

from collections.abc import Iterable

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.orm import Session, selectinload

from app.models.consulta import Consulta, TipoConsulta
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.jornada import Jornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.schemas.consulta import ConsultaSaida
from app.schemas.documento import DocumentoSaida
from app.schemas.linha_do_tempo import EventoLinhaDoTempo, TipoEvento
from app.schemas.solicitacao import SolicitacaoSaida
from app.schemas.paginacao import Paginacao, dados_pagina

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
    sessao: Session, jornada: Jornada, tipos: set[TipoEvento] | None = None,
    paginacao: Paginacao | None = None, recentes: bool = False,
):
    """Reúne consultas, solicitações e documentos em ordem cronológica.

    Datas usadas: consulta = data da consulta; demais = momento em que foram criados.
    """
    tipos = tipos or set(TipoEvento)
    eventos: list[EventoLinhaDoTempo] = []
    ids_por_tipo = None
    if paginacao is not None and paginacao.pagina is not None:
        # O banco ordena apenas identificadores e datas; carrega os registros completos
        # e os relacionamentos somente dos eventos que pertencem à página solicitada.
        modelos = {TipoEvento.consulta: (Consulta, Consulta.data), TipoEvento.solicitacao: (Solicitacao, Solicitacao.criado_em), TipoEvento.documento: (Documento, Documento.criado_em)}
        partes = [select(modelo.id.label("id"), data.label("data"), literal(ORDEM_TIPOS[tipo]).label("ordem")).where(modelo.jornada_id == jornada.id) for tipo, (modelo, data) in modelos.items() if tipo in tipos]
        uniao = union_all(*partes).subquery()
        total = sessao.scalar(select(func.count()).select_from(uniao))
        pagina = min(paginacao.pagina, max(1, (total + paginacao.tamanho - 1) // paginacao.tamanho))
        colunas = [uniao.c.data, uniao.c.ordem, uniao.c.id]
        ordem = [coluna.desc() if recentes else coluna.asc() for coluna in colunas]
        registros = sessao.execute(select(uniao).order_by(*ordem).limit(paginacao.tamanho).offset((pagina - 1) * paginacao.tamanho)).all()
        ids_por_tipo = {tipo: [registro.id for registro in registros if registro.ordem == ORDEM_TIPOS[tipo]] for tipo in tipos}

    if TipoEvento.consulta in tipos:
        consulta = select(Consulta).options(selectinload(Consulta.prescricoes)).where(Consulta.jornada_id == jornada.id)
        if ids_por_tipo is not None:
            consulta = consulta.where(Consulta.id.in_(ids_por_tipo[TipoEvento.consulta]))
        consultas = sessao.scalars(consulta)
        eventos += _eventos_de_consultas(consultas)
    if TipoEvento.solicitacao in tipos:
        consulta = select(Solicitacao).options(selectinload(Solicitacao.destinatario)).where(Solicitacao.jornada_id == jornada.id)
        if ids_por_tipo is not None:
            consulta = consulta.where(Solicitacao.id.in_(ids_por_tipo[TipoEvento.solicitacao]))
        solicitacoes = sessao.scalars(consulta)
        eventos += _eventos_de_solicitacoes(solicitacoes, jornada)
    if TipoEvento.documento in tipos:
        consulta = select(Documento).options(selectinload(Documento.enviado_por), selectinload(Documento.arquivo)).where(Documento.jornada_id == jornada.id)
        if ids_por_tipo is not None:
            consulta = consulta.where(Documento.id.in_(ids_por_tipo[TipoEvento.documento]))
        documentos = sessao.scalars(consulta)
        eventos += _eventos_de_documentos(documentos)

    eventos.sort(key=lambda evento: (evento.data, ORDEM_TIPOS[evento.tipo], evento.id), reverse=recentes)
    if ids_por_tipo is not None:
        return dados_pagina(eventos, pagina, paginacao.tamanho, total)
    return eventos
