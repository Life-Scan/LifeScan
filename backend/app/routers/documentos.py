from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    carregar_jornada_com_acesso,
    exigir_tipo,
    garantir_jornada_editavel,
    obter_jornada_com_acesso_de_parceiro,
    obter_usuario_atual,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.jornada import Jornada
from app.models.solicitacao import TIPOS_ATENDIDOS_POR_ENVIO, Solicitacao, StatusSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.documento import DocumentoSaida, RevisaoEntrada
from app.services.armazenamento import confirmar_ou_remover, salvar_upload

router = APIRouter(tags=["Documentos"])

SOLICITACAO_NAO_ENCONTRADA = "Solicitação não encontrada nesta jornada."


def _validar_solicitacao_para_envio(
    sessao: Session, jornada: Jornada, usuario: Usuario, solicitacao_id: int
) -> Solicitacao:
    """A solicitação precisa ser desta jornada, estar pendente, aceitar envio de documento
    e ser destinada a quem está enviando (o médico pode atender qualquer uma)."""
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    if solicitacao is None or solicitacao.jornada_id != jornada.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SOLICITACAO_NAO_ENCONTRADA)

    if usuario.tipo_usuario != TipoUsuario.medico and solicitacao.destinatario_id != usuario.id:
        if usuario.tipo_usuario == TipoUsuario.parceiro:
            # O parceiro nem enxerga as solicitações de outras pessoas
            raise HTTPException(status.HTTP_404_NOT_FOUND, SOLICITACAO_NAO_ENCONTRADA)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta solicitação é destinada a outra pessoa.")

    if solicitacao.tipo not in TIPOS_ATENDIDOS_POR_ENVIO:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Só é possível vincular o envio a solicitações de exame ou de orientação profissional.",
        )
    if solicitacao.status != StatusSolicitacao.pendente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta solicitação não está mais pendente.")
    return solicitacao


@router.post(
    "/journeys/{jornada_id}/documents",
    response_model=DocumentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def enviar_documento(
    titulo: str = Form(..., min_length=3, max_length=150),
    categoria: CategoriaDocumento = Form(CategoriaDocumento.exame),
    solicitacao_id: int | None = Form(None),
    arquivo: UploadFile = File(...),
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Documento:
    """Médico, paciente ou parceiro atribuído envia um documento.

    Se vinculado a uma solicitação de exame ou orientação profissional, ela é marcada como atendida.
    """
    garantir_jornada_editavel(jornada)
    solicitacao = (
        _validar_solicitacao_para_envio(sessao, jornada, usuario, solicitacao_id)
        if solicitacao_id is not None
        else None
    )

    registro_arquivo = salvar_upload(arquivo, jornada.id, usuario.id)
    sessao.add(registro_arquivo)
    sessao.flush()

    documento = Documento(
        jornada_id=jornada.id,
        solicitacao_id=solicitacao.id if solicitacao else None,
        enviado_por_id=usuario.id,
        categoria=categoria,
        titulo=titulo.strip(),
        arquivo_id=registro_arquivo.id,
    )
    sessao.add(documento)
    if solicitacao is not None:
        solicitacao.marcar_atendida()

    confirmar_ou_remover(sessao, registro_arquivo)
    return documento


@router.get("/journeys/{jornada_id}/documents", response_model=list[DocumentoSaida])
def listar_documentos(
    categoria: CategoriaDocumento | None = Query(None),
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Documento]:
    """Médico e paciente veem todos os documentos; o parceiro vê apenas os próprios envios."""
    consulta = select(Documento).where(Documento.jornada_id == jornada.id)
    if usuario.tipo_usuario == TipoUsuario.parceiro:
        consulta = consulta.where(Documento.enviado_por_id == usuario.id)
    if categoria is not None:
        consulta = consulta.where(Documento.categoria == categoria)
    return list(sessao.scalars(consulta.order_by(Documento.criado_em.desc(), Documento.id.desc())).all())


@router.patch("/documents/{documento_id}/review", response_model=DocumentoSaida)
def revisar_documento(
    documento_id: int,
    dados: RevisaoEntrada,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Documento:
    """O médico revisa o documento, com uma observação opcional. Pode revisar de novo para corrigi-la."""
    documento = sessao.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento não encontrado.")
    jornada = carregar_jornada_com_acesso(sessao, medico, documento.jornada_id)
    garantir_jornada_editavel(jornada)

    documento.status = StatusDocumento.revisado
    documento.observacao_revisao = (dados.observacao_revisao or "").strip() or None
    documento.revisado_em = agora_utc()
    sessao.commit()
    return documento
