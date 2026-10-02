"""Monta a aplicação e registra os roteadores dos módulos."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import Configuracao, carregar_configuracao
from app.modules import projecoes

DOTENV = Path(__file__).resolve().parent.parent / ".env"


def criar_app(config: Configuracao | None = None) -> FastAPI:
    config = config or carregar_configuracao(dotenv=DOTENV)
    app = FastAPI(
        title="PROCED API",
        description="Projeção de Consumo por Estrutura Demográfica (RF11, RNF09)",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.cors_origin],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(projecoes.router)
    return app


app = criar_app()
