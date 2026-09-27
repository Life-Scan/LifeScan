from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import obter_configuracoes
from app.core.erros import registrar_tratadores_erro
from app.routers import auth, jornadas, pacientes, vinculos


def criar_app() -> FastAPI:
    config = obter_configuracoes()
    app = FastAPI(
        title="LifeScan API",
        description="Acompanhamento contínuo do tratamento entre médico e paciente.",
        version="0.1.0",
    )

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
    app.include_router(auth.router)
    app.include_router(pacientes.router)
    app.include_router(vinculos.router)
    app.include_router(jornadas.router)

    @app.get("/health", tags=["Sistema"])
    def verificar_saude() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = criar_app()
