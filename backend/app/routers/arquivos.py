from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import carregar_jornada_com_acesso, obter_usuario_atual
from app.db.sessao import obter_sessao
from app.models.arquivo import Arquivo
from app.models.usuario import Usuario
from app.services.armazenamento import caminho_do_arquivo

router = APIRouter(prefix="/files", tags=["Arquivos"])


@router.get("/{arquivo_id}/download")
def baixar_arquivo(
    arquivo_id: int,
    inline: bool = Query(False, description="Exibir no navegador em vez de baixar"),
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> FileResponse:
    """Download autenticado: só quem tem acesso à jornada do arquivo consegue baixar."""
    arquivo = sessao.get(Arquivo, arquivo_id)
    if arquivo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado.")
    carregar_jornada_com_acesso(sessao, usuario, arquivo.jornada_id)

    caminho = caminho_do_arquivo(arquivo)
    if not caminho.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado no servidor.")

    return FileResponse(
        caminho,
        media_type=arquivo.tipo_mime,
        filename=arquivo.nome_original,
        content_disposition_type="inline" if inline else "attachment",
    )
