"""Gravação dos arquivos enviados em disco, com validação de extensão e tamanho (RNF01)."""

import uuid
from pathlib import Path, PurePath

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.models.arquivo import Arquivo

# Extensão -> tipo MIME gravado nos metadados e usado no download
EXTENSOES_PERMITIDAS: dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "dcm": "application/dicom",
    "txt": "text/plain",
}

TAMANHO_BLOCO = 1024 * 1024


def _mensagem_formatos() -> str:
    return ", ".join(EXTENSOES_PERMITIDAS)


def extrair_extensao(nome_arquivo: str) -> str:
    return PurePath(nome_arquivo).suffix.lower().lstrip(".")


def erro_arquivo_grande() -> HTTPException:
    limite = obter_configuracoes().tamanho_maximo_upload_mb
    return HTTPException(
        status.HTTP_413_CONTENT_TOO_LARGE,
        f"Arquivo muito grande. O tamanho máximo é {limite} MB.",
    )


def caminho_do_arquivo(arquivo: Arquivo) -> Path:
    return obter_configuracoes().pasta_uploads / arquivo.nome_armazenado


def salvar_upload(upload: UploadFile, jornada_id: int, usuario_id: int) -> Arquivo:
    """Valida e grava o upload em disco com nome gerado (UUID).

    Devolve o objeto Arquivo ainda não adicionado à sessão. Se o commit falhar,
    quem chamou deve apagar o arquivo com remover_do_disco().
    """
    config = obter_configuracoes()
    # Só o nome, sem caminhos que o navegador possa ter enviado
    nome_original = PurePath((upload.filename or "").replace("\\", "/")).name.strip()[:255]
    extensao = extrair_extensao(nome_original)

    if extensao not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Formato de arquivo não permitido. Use: {_mensagem_formatos()}.",
        )
    if upload.size is not None and upload.size > config.tamanho_maximo_upload_bytes:
        raise erro_arquivo_grande()

    config.pasta_uploads.mkdir(parents=True, exist_ok=True)
    nome_armazenado = f"{uuid.uuid4().hex}.{extensao}"
    destino = config.pasta_uploads / nome_armazenado

    tamanho = 0
    try:
        with destino.open("wb") as saida:
            while bloco := upload.file.read(TAMANHO_BLOCO):
                tamanho += len(bloco)
                if tamanho > config.tamanho_maximo_upload_bytes:
                    raise erro_arquivo_grande()
                saida.write(bloco)
    except BaseException:
        destino.unlink(missing_ok=True)
        raise

    if tamanho == 0:
        destino.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O arquivo enviado está vazio.")

    return Arquivo(
        jornada_id=jornada_id,
        nome_original=nome_original,
        nome_armazenado=nome_armazenado,
        tipo_mime=EXTENSOES_PERMITIDAS[extensao],
        tamanho_bytes=tamanho,
        enviado_por_id=usuario_id,
    )


def remover_do_disco(arquivo: Arquivo) -> None:
    caminho_do_arquivo(arquivo).unlink(missing_ok=True)


def confirmar_ou_remover(sessao: Session, arquivo: Arquivo | None) -> None:
    """Faz o commit; se falhar, desfaz a transação e apaga o arquivo já gravado em disco."""
    try:
        sessao.commit()
    except Exception:
        sessao.rollback()
        if arquivo is not None:
            remover_do_disco(arquivo)
        raise
