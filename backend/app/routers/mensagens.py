from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import garantir_jornada_editavel, obter_jornada_com_acesso, obter_usuario_atual
from app.db.sessao import obter_sessao
from app.models.jornada import Jornada
from app.models.mensagem import Mensagem
from app.models.usuario import Usuario
from app.schemas.mensagem import MensagemSaida
from app.services.armazenamento import confirmar_ou_remover, salvar_upload

router = APIRouter(prefix="/journeys/{jornada_id}/messages", tags=["Mensagens"])


@router.post("", response_model=MensagemSaida, status_code=status.HTTP_201_CREATED)
def enviar_mensagem(
    conteudo: str | None = Form(None),
    arquivo: UploadFile | None = File(None),
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Mensagem:
    """Envia uma mensagem com texto e/ou anexo (RF11)."""
    garantir_jornada_editavel(jornada)
    texto = (conteudo or "").strip() or None
    # Navegadores podem mandar o campo de arquivo vazio quando nada foi escolhido
    tem_anexo = arquivo is not None and bool(arquivo.filename)
    if texto is None and not tem_anexo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Escreva uma mensagem ou anexe um arquivo.")

    registro_arquivo = None
    if tem_anexo:
        registro_arquivo = salvar_upload(arquivo, jornada.id, usuario.id)
        sessao.add(registro_arquivo)
        sessao.flush()

    mensagem = Mensagem(
        jornada_id=jornada.id,
        remetente_id=usuario.id,
        conteudo=texto,
        arquivo_id=registro_arquivo.id if registro_arquivo else None,
    )
    sessao.add(mensagem)
    confirmar_ou_remover(sessao, registro_arquivo)
    return mensagem


@router.get("", response_model=list[MensagemSaida])
def listar_mensagens(
    jornada: Jornada = Depends(obter_jornada_com_acesso),
    sessao: Session = Depends(obter_sessao),
) -> list[Mensagem]:
    consulta = (
        select(Mensagem)
        .where(Mensagem.jornada_id == jornada.id)
        .order_by(Mensagem.criado_em, Mensagem.id)
    )
    return list(sessao.scalars(consulta).all())
