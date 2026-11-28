from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    carregar_acompanhamento_com_acesso,
    exigir_tipo,
    garantir_acompanhamento_editavel,
    obter_acompanhamento_com_acesso_de_parceiro,
    obter_usuario_atual,
)
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.documento import CategoriaDocumento, Documento, StatusDocumento
from app.models.acompanhamento import Acompanhamento
from app.models.solicitacao import TIPOS_ATENDIDOS_POR_ENVIO, Solicitacao, StatusSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.documento import DocumentoEdicao, DocumentoSaida, RevisaoEntrada
from app.schemas.paginacao import Pagina, Paginacao, paginar
from sqlalchemy.orm import selectinload
from app.services.armazenamento import confirmar_ou_remover, remover_do_disco, salvar_upload

router = APIRouter(tags=["Documentos"])

SOLICITACAO_NAO_ENCONTRADA = "Solicitação não encontrada neste acompanhamento."
DOCUMENTO_NAO_ENCONTRADO = "Documento não encontrado."


def _validar_solicitacao_para_envio(
    sessao: Session, acompanhamento: Acompanhamento, usuario: Usuario, solicitacao_id: int
) -> Solicitacao:
    """A solicitação precisa ser deste acompanhamento, estar pendente, aceitar envio de documento
    e ser destinada a quem está enviando (o médico pode atender qualquer uma)."""
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    if solicitacao is None or solicitacao.acompanhamento_id != acompanhamento.id:
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
    "/follow-ups/{acompanhamento_id}/documents",
    response_model=DocumentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def enviar_documento(
    titulo: str = Form(..., min_length=3, max_length=150),
    categoria: CategoriaDocumento = Form(CategoriaDocumento.exame),
    solicitacao_id: int | None = Form(None),
    arquivo: UploadFile = File(...),
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Documento:
    """Médico, paciente ou parceiro atribuído envia um documento.

    Se vinculado a uma solicitação de exame ou orientação profissional, ela é marcada como atendida.
    """
    garantir_acompanhamento_editavel(acompanhamento)
    solicitacao = (
        _validar_solicitacao_para_envio(sessao, acompanhamento, usuario, solicitacao_id)
        if solicitacao_id is not None
        else None
    )

    registro_arquivo = salvar_upload(arquivo, acompanhamento.id, usuario.id)
    sessao.add(registro_arquivo)
    sessao.flush()

    documento = Documento(
        acompanhamento_id=acompanhamento.id,
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


@router.get("/follow-ups/{acompanhamento_id}/documents", response_model=Pagina[DocumentoSaida] | list[DocumentoSaida])
def listar_documentos(
    categoria: CategoriaDocumento | None = Query(None),
    paginacao: Paginacao = Depends(),
    acompanhamento: Acompanhamento = Depends(obter_acompanhamento_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    """Médico e paciente veem todos os documentos; o parceiro vê apenas os próprios envios."""
    consulta = select(Documento).options(selectinload(Documento.enviado_por), selectinload(Documento.arquivo)).where(Documento.acompanhamento_id == acompanhamento.id)
    if usuario.tipo_usuario == TipoUsuario.parceiro:
        consulta = consulta.where(Documento.enviado_por_id == usuario.id)
    if categoria is not None:
        consulta = consulta.where(Documento.categoria == categoria)
    return paginar(sessao, consulta.order_by(Documento.criado_em.desc(), Documento.id.desc()), paginacao)


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
    acompanhamento = carregar_acompanhamento_com_acesso(sessao, medico, documento.acompanhamento_id)
    garantir_acompanhamento_editavel(acompanhamento)

    documento.status = StatusDocumento.revisado
    documento.observacao_revisao = (dados.observacao_revisao or "").strip() or None
    documento.revisado_em = agora_utc()
    sessao.commit()
    return documento


def _carregar_documento_para_alterar(sessao: Session, usuario: Usuario, documento_id: int) -> Documento:
    """Documento que o usuário pode editar ou excluir, num acompanhamento ativo.

    O médico altera qualquer documento; o parceiro atribuído, só os que ele enviou. Paciente e
    colaborador não alteram documentos (o paciente só envia).
    """
    documento = sessao.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, DOCUMENTO_NAO_ENCONTRADO)
    acompanhamento = carregar_acompanhamento_com_acesso(
        sessao, usuario, documento.acompanhamento_id, permitir_parceiro=True
    )

    if usuario.tipo_usuario == TipoUsuario.parceiro and documento.enviado_por_id != usuario.id:
        # O parceiro nem enxerga os documentos de outras pessoas
        raise HTTPException(status.HTTP_404_NOT_FOUND, DOCUMENTO_NAO_ENCONTRADO)
    if usuario.tipo_usuario not in (TipoUsuario.medico, TipoUsuario.parceiro):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Somente o médico ou o parceiro que enviou pode alterar este documento."
        )

    garantir_acompanhamento_editavel(acompanhamento)
    return documento


@router.patch("/documents/{documento_id}", response_model=DocumentoSaida)
def editar_documento(
    documento_id: int,
    dados: DocumentoEdicao,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Documento:
    """Edita título e categoria. O arquivo, a revisão e a solicitação atendida não mudam."""
    documento = _carregar_documento_para_alterar(sessao, usuario, documento_id)
    if dados.titulo is not None:
        documento.titulo = dados.titulo
    if dados.categoria is not None:
        documento.categoria = dados.categoria
    sessao.commit()
    return documento


@router.delete("/documents/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_documento(
    documento_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> None:
    """Exclui o documento e o arquivo dele.

    Se ele atendia uma solicitação e nenhum outro documento a atende, ela volta a ficar pendente.
    """
    documento = _carregar_documento_para_alterar(sessao, usuario, documento_id)
    arquivo = documento.arquivo

    if documento.solicitacao_id is not None:
        solicitacao = sessao.get(Solicitacao, documento.solicitacao_id)
        outro_envio = sessao.scalar(
            select(Documento.id)
            .where(Documento.solicitacao_id == documento.solicitacao_id, Documento.id != documento.id)
            .limit(1)
        )
        if solicitacao is not None and solicitacao.status == StatusSolicitacao.atendida and outro_envio is None:
            solicitacao.reabrir()

    sessao.delete(documento)
    sessao.flush()  # o documento sai antes do arquivo, que ele referencia
    sessao.delete(arquivo)
    sessao.commit()
    # Só depois do commit: se ele falhar, o arquivo continua em disco junto com o registro
    remover_do_disco(arquivo)
