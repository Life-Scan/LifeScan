from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
from app.models.exame import Exame, StatusExame
from app.models.jornada import Jornada
from app.models.solicitacao import TIPOS_ATENDIDOS_POR_ENVIO, Solicitacao, StatusSolicitacao
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.exame import ExameSaida, RevisaoEntrada
from app.services.armazenamento import confirmar_ou_remover, salvar_upload

router = APIRouter(tags=["Exames"])


def _validar_solicitacao_para_exame(sessao: Session, jornada: Jornada, solicitacao_id: int) -> Solicitacao:
    solicitacao = sessao.get(Solicitacao, solicitacao_id)
    if solicitacao is None or solicitacao.jornada_id != jornada.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitação não encontrada nesta jornada.")
    if solicitacao.tipo not in TIPOS_ATENDIDOS_POR_ENVIO:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Só é possível vincular o envio a solicitações de exame ou de orientação profissional.",
        )
    if solicitacao.status != StatusSolicitacao.pendente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta solicitação não está mais pendente.")
    return solicitacao


@router.post(
    "/journeys/{jornada_id}/exams",
    response_model=ExameSaida,
    status_code=status.HTTP_201_CREATED,
)
def enviar_exame(
    titulo: str = Form(..., min_length=3, max_length=150),
    solicitacao_id: int | None = Form(None),
    arquivo: UploadFile = File(...),
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Exame:
    """Médico, paciente ou parceiro atribuído envia um exame/documento.

    Se vinculado a uma solicitação de exame ou orientação profissional, ela é marcada como atendida.
    """
    garantir_jornada_editavel(jornada)
    if solicitacao_id is not None and usuario.tipo_usuario == TipoUsuario.parceiro:
        # O parceiro não enxerga as solicitações da jornada (isso muda quando
        # as solicitações passarem a ter destinatário)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Parceiros ainda não podem vincular o envio a uma solicitação.",
        )
    solicitacao = (
        _validar_solicitacao_para_exame(sessao, jornada, solicitacao_id)
        if solicitacao_id is not None
        else None
    )

    registro_arquivo = salvar_upload(arquivo, jornada.id, usuario.id)
    sessao.add(registro_arquivo)
    sessao.flush()

    exame = Exame(
        jornada_id=jornada.id,
        solicitacao_id=solicitacao.id if solicitacao else None,
        enviado_por_id=usuario.id,
        titulo=titulo.strip(),
        arquivo_id=registro_arquivo.id,
    )
    sessao.add(exame)
    if solicitacao is not None:
        solicitacao.marcar_atendida()

    confirmar_ou_remover(sessao, registro_arquivo)
    return exame


@router.get("/journeys/{jornada_id}/exams", response_model=list[ExameSaida])
def listar_exames(
    jornada: Jornada = Depends(obter_jornada_com_acesso_de_parceiro),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> list[Exame]:
    """Médico e paciente veem todos os envios; o parceiro vê apenas os próprios."""
    consulta = select(Exame).where(Exame.jornada_id == jornada.id)
    if usuario.tipo_usuario == TipoUsuario.parceiro:
        consulta = consulta.where(Exame.enviado_por_id == usuario.id)
    return list(sessao.scalars(consulta.order_by(Exame.criado_em.desc(), Exame.id.desc())).all())


@router.patch("/exams/{exame_id}/review", response_model=ExameSaida)
def revisar_exame(
    exame_id: int,
    dados: RevisaoEntrada,
    medico: Usuario = Depends(exigir_tipo(TipoUsuario.medico)),
    sessao: Session = Depends(obter_sessao),
) -> Exame:
    """O médico revisa o exame, com uma observação opcional (RF09). Pode revisar de novo para corrigir a observação."""
    exame = sessao.get(Exame, exame_id)
    if exame is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exame não encontrado.")
    jornada = carregar_jornada_com_acesso(sessao, medico, exame.jornada_id)
    garantir_jornada_editavel(jornada)

    exame.status = StatusExame.revisado
    exame.observacao_revisao = (dados.observacao_revisao or "").strip() or None
    exame.revisado_em = agora_utc()
    sessao.commit()
    return exame
