from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import obter_configuracoes
from app.core.erros import registrar_tratadores_erro
from app.routers import (
    arquivos,
    atribuicoes,
    auth,
    consultas,
    exames,
    ficha,
    jornadas,
    linha_do_tempo,
    painel,
    solicitacoes,
    usuarios,
)

# Margem para os campos e delimitadores do multipart além do próprio arquivo
FOLGA_MULTIPART_BYTES = 1024 * 1024


def criar_app() -> FastAPI:
    config = obter_configuracoes()
    app = FastAPI(
        title="LifeScan API",
        description="Centraliza os dados do tratamento do paciente para o médico, o paciente e os parceiros.",
        version="0.2.0",
    )

    # Registrado antes do CORS para que o CORS fique por fora e a resposta 413
    # também leve os cabeçalhos CORS (senão o navegador mostraria só "erro de CORS").
    @app.middleware("http")
    async def limitar_tamanho_requisicao(request: Request, call_next):
        """Recusa de cara requisições maiores que o limite de upload, antes de ler o corpo.
        A validação exata do tamanho do arquivo é feita em services/armazenamento.py."""
        tamanho = request.headers.get("content-length", "")
        limite = obter_configuracoes().tamanho_maximo_upload_bytes + FOLGA_MULTIPART_BYTES
        if tamanho.isdigit() and int(tamanho) > limite:
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content={
                    "detail": "Arquivo muito grande. O tamanho máximo é "
                    f"{obter_configuracoes().tamanho_maximo_upload_mb} MB."
                },
            )
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origens_cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Necessário para o frontend ler o nome do arquivo nos downloads
        expose_headers=["Content-Disposition"],
    )

    registrar_tratadores_erro(app)
    for modulo in (
        auth,
        usuarios,
        jornadas,
        ficha,
        atribuicoes,
        consultas,
        solicitacoes,
        exames,
        arquivos,
        linha_do_tempo,
        painel,
    ):
        app.include_router(modulo.router)

    @app.get("/health", tags=["Sistema"])
    def verificar_saude() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = criar_app()
