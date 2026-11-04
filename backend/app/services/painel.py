"""Painel de pendências por tipo de usuário.

Considera apenas acompanhamentos ativos (não encerrados).
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.db.base import agora_utc
from app.models.atribuicao import AtribuicaoParceiro
from app.models.documento import Documento, StatusDocumento
from app.models.acompanhamento import Acompanhamento, StatusAcompanhamento
from app.models.solicitacao import Solicitacao, StatusSolicitacao, TipoSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.documento import DocumentoSaida
from app.schemas.painel import (
    DocumentoPendente,
    AcompanhamentoResumo,
    PainelMedico,
    PainelPaciente,
    PainelParceiro,
    SolicitacaoPendente,
)
from app.schemas.solicitacao import SolicitacaoSaida


def _acompanhamentos_em_andamento(sessao: Session, usuario: Usuario) -> dict[int, Acompanhamento]:
    consulta = select(Acompanhamento).where(Acompanhamento.status == StatusAcompanhamento.ativo)
    if usuario.tipo_usuario == TipoUsuario.medico:
        consulta = consulta.where(Acompanhamento.medico_id == usuario.id)
    elif usuario.tipo_usuario == TipoUsuario.paciente:
        consulta = consulta.where(Acompanhamento.paciente_id == usuario.id)
    else:
        consulta = consulta.join(
            AtribuicaoParceiro, AtribuicaoParceiro.acompanhamento_id == Acompanhamento.id
        ).where(AtribuicaoParceiro.parceiro_id == usuario.id)
    return {acompanhamento.id: acompanhamento for acompanhamento in sessao.scalars(consulta)}


def _solicitacoes_pendentes(
    sessao: Session, acompanhamentos: dict[int, Acompanhamento], destinatario_id: int | None = None
) -> list[Solicitacao]:
    """Pendentes dos acompanhamentos, por prazo. Com destinatario_id, só as destinadas a essa pessoa."""
    consulta = select(Solicitacao).where(
        Solicitacao.acompanhamento_id.in_(acompanhamentos),
        Solicitacao.status == StatusSolicitacao.pendente,
    )
    if destinatario_id is not None:
        consulta = consulta.where(Solicitacao.destinatario_id == destinatario_id)
    return list(sessao.scalars(consulta.order_by(Solicitacao.prazo, Solicitacao.id)))


def _item_solicitacao(solicitacao: Solicitacao, acompanhamentos: dict[int, Acompanhamento]) -> SolicitacaoPendente:
    return SolicitacaoPendente(
        **SolicitacaoSaida.model_validate(solicitacao).model_dump(),
        acompanhamento=AcompanhamentoResumo.model_validate(acompanhamentos[solicitacao.acompanhamento_id]),
    )


def montar_painel_medico(sessao: Session, medico: Usuario) -> PainelMedico:
    config = obter_configuracoes()
    acompanhamentos = _acompanhamentos_em_andamento(sessao, medico)
    agora = agora_utc()
    limite_proximo = agora + timedelta(days=config.dias_prazo_proximo)

    documentos = sessao.scalars(
        select(Documento)
        .where(
            Documento.acompanhamento_id.in_(acompanhamentos),
            Documento.status == StatusDocumento.enviado,
            # Arquivos que o próprio médico enviou não precisam da revisão dele
            Documento.enviado_por_id != medico.id,
        )
        .order_by(Documento.criado_em, Documento.id)
    )

    # O médico acompanha todas as solicitações, sejam para o paciente ou para parceiros
    pendentes = _solicitacoes_pendentes(sessao, acompanhamentos)
    vencidas = [s for s in pendentes if s.prazo < agora]
    proximas = [s for s in pendentes if agora <= s.prazo <= limite_proximo]

    return PainelMedico(
        dias_prazo_proximo=config.dias_prazo_proximo,
        documentos_aguardando_revisao=[
            DocumentoPendente(
                **DocumentoSaida.model_validate(documento).model_dump(),
                acompanhamento=AcompanhamentoResumo.model_validate(acompanhamentos[documento.acompanhamento_id]),
            )
            for documento in documentos
        ],
        solicitacoes_vencidas=[_item_solicitacao(s, acompanhamentos) for s in vencidas],
        solicitacoes_proximas_do_prazo=[_item_solicitacao(s, acompanhamentos) for s in proximas],
    )


def montar_painel_paciente(sessao: Session, paciente: Usuario) -> PainelPaciente:
    acompanhamentos = _acompanhamentos_em_andamento(sessao, paciente)
    # Só o que cabe ao paciente: as solicitações destinadas a parceiros não são pendências dele
    pendentes = _solicitacoes_pendentes(sessao, acompanhamentos, destinatario_id=paciente.id)
    # Ordenadas por prazo, as vencidas naturalmente aparecem primeiro
    return PainelPaciente(
        solicitacoes_pendentes=[
            _item_solicitacao(s, acompanhamentos) for s in pendentes if s.tipo != TipoSolicitacao.consulta_extra
        ],
        consultas_extras=[
            _item_solicitacao(s, acompanhamentos) for s in pendentes if s.tipo == TipoSolicitacao.consulta_extra
        ],
    )


def montar_painel_parceiro(sessao: Session, parceiro: Usuario) -> PainelParceiro:
    """Solicitações destinadas ao parceiro nos acompanhamentos a que ele está atribuído."""
    acompanhamentos = _acompanhamentos_em_andamento(sessao, parceiro)
    pendentes = _solicitacoes_pendentes(sessao, acompanhamentos, destinatario_id=parceiro.id)
    return PainelParceiro(solicitacoes_pendentes=[_item_solicitacao(s, acompanhamentos) for s in pendentes])
