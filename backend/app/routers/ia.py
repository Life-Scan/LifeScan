"""Rotas do componente de Inteligência Artificial (eixo de Computação Visual)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import obter_configuracoes
from app.core.deps import obter_usuario_atual
from app.models.usuario import Usuario
from app.schemas.qualidade_imagem import QualidadeImagemSaida
from app.services.armazenamento import erro_arquivo_grande
from app.services.qualidade_imagem import (
    ErroComponenteIndisponivel,
    ErroImagemInvalida,
    verificar_qualidade,
)

router = APIRouter(prefix="/ai", tags=["Inteligência artificial"])


def _ler_imagem(arquivo: UploadFile) -> bytes:
    """Lê o upload respeitando o mesmo limite de tamanho dos documentos (RNF01)."""
    limite = obter_configuracoes().tamanho_maximo_upload_bytes
    if arquivo.size is not None and arquivo.size > limite:
        raise erro_arquivo_grande()

    conteudo = arquivo.file.read(limite + 1)
    if len(conteudo) > limite:
        raise erro_arquivo_grande()
    if not conteudo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O arquivo enviado está vazio.")
    return conteudo


@router.post(
    "/verificar-qualidade",
    response_model=QualidadeImagemSaida,
    summary="Verifica se a foto de um documento está legível",
)
def verificar_qualidade_documento(
    arquivo: UploadFile = File(..., description="Foto do documento (JPG, PNG ou WEBP)."),
    _usuario: Usuario = Depends(obter_usuario_atual),
) -> QualidadeImagemSaida:
    """Avalia a qualidade da foto antes do envio e devolve o motivo quando não estiver legível.

    O resultado é **orientativo**: o frontend mostra o aviso, mas não bloqueia o
    envio do documento. A decisão de bloquear fica com quem chama a rota.
    """
    if arquivo.content_type and not arquivo.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Envie uma imagem (JPG, PNG ou WEBP) para a verificação de qualidade.",
        )

    try:
        resultado = verificar_qualidade(_ler_imagem(arquivo))
    except ErroImagemInvalida as erro:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(erro)) from erro
    except ErroComponenteIndisponivel as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro

    return QualidadeImagemSaida(**asdict(resultado))
