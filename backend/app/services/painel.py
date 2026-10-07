"""Painel de pendências por tipo de usuário.

Considera apenas jornadas ativas (não encerradas).
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.db.base import agora_utc
from app.models.atribuicao import AtribuicaoParceiro
from app.models.documento import Documento, StatusDocumento
from app.models.jornada import Jornada, StatusJornada
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.documento import DocumentoSaida
from app.schemas.painel import (
    DocumentoPendente,
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
    elif usuario.tipo_usuario == TipoUsuario.paciente:
        consulta = consulta.where(Jornada.paciente_id == usuario.id)
    else:
        consulta = consulta.join(
            AtribuicaoParceiro, AtribuicaoParceiro.jornada_id == Jornada.id
        ).where(AtribuicaoParceiro.parceiro_id == usuario.id)
    return {jornada.id: jornada for jornada in sessao.scalars(consulta)}


def _solicitacoes_pendentes(
    sessao: Session, jornadas: dict[int, Jornada], destinatario_id: int | None = None
) -> list[Solicitacao]:
    """Pendentes das jornadas, por prazo. Com destinatario_id, só as destinadas a essa pessoa."""
    consulta = select(Solicitacao).where(
        Solicitacao.jornada_id.in_(jornadas),
        Solicitacao.status == StatusSolicitacao.pendente,
    )
    if destinatario_id is not None:
        consulta = consulta.where(Solicitacao.destinatario_id == destinatario_id)
    return list(sessao.scalars(consulta.order_by(Solicitacao.prazo, Solicitacao.id)))


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

    documentos = sessao.scalars(
        select(Documento)
        .where(
            Documento.jornada_id.in_(jornadas),
            Documento.status == StatusDocumento.enviado,
            # Arquivos que o próprio médico enviou não precisam da revisão dele
            Documento.enviado_por_id != medico.id,
        )
        .order_by(Documento.criado_em, Documento.id)
    )

    # O médico acompanha todas as solicitações, sejam para o paciente ou para parceiros
    pendentes = _solicitacoes_pendentes(sessao, jornadas)
    vencidas = [s for s in pendentes if s.prazo < agora]
    proximas = [s for s in pendentes if agora <= s.prazo <= limite_proximo]

    return PainelMedico(
        dias_prazo_proximo=config.dias_prazo_proximo,
        documentos_aguardando_revisao=[
            DocumentoPendente(
                **DocumentoSaida.model_validate(documento).model_dump(),
                jornada=JornadaResumo.model_validate(jornadas[documento.jornada_id]),
            )
            for documento in documentos
        ],
        solicitacoes_vencidas=[_item_solicitacao(s, jornadas) for s in vencidas],
        solicitacoes_proximas_do_prazo=[_item_solicitacao(s, jornadas) for s in proximas],
    )


def montar_painel_paciente(sessao: Session, paciente: Usuario) -> PainelPaciente:
    jornadas = _jornadas_em_andamento(sessao, paciente)
    # Só o que cabe ao paciente: as solicitações destinadas a parceiros não são pendências dele
    pendentes = _solicitacoes_pendentes(sessao, jornadas, destinatario_id=paciente.id)
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
    """Solicitações destinadas ao parceiro nas jornadas a que ele está atribuído."""
    jornadas = _jornadas_em_andamento(sessao, parceiro)
    pendentes = _solicitacoes_pendentes(sessao, jornadas, destinatario_id=parceiro.id)
    return PainelParceiro(solicitacoes_pendentes=[_item_solicitacao(s, jornadas) for s in pendentes])
