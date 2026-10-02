"""Monta a aplicação e registra os roteadores dos módulos."""

import logging
import threading
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import DOTENV, Configuracao, ErroConfiguracao, ErroFonteDados, carregar_configuracao
from app.modules import arranjos, estrutura_etaria, fontes, projecoes, simulador

log = logging.getLogger("proced")


async def _fonte_indisponivel(_: Request, erro: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Fonte de dados indisponível no momento"})


def aquecer(cargas: Iterable[Callable[[], object]]) -> int:
    """Executa as leituras iniciais do banco; uma falha não impede a API de subir.

    Devolve quantas cargas terminaram sem erro.
    """
    concluidas = 0
    for carga in cargas:
        try:
            carga()
            concluidas += 1
        except (ErroFonteDados, ErroConfiguracao) as erro:
            log.warning("pré-carga não concluída: %s", erro)
    return concluidas


def _cargas_iniciais() -> list[Callable[[], object]]:
    repo = projecoes.obter_repositorio()
    return [
        repo.domicilios,
        repo.populacao_por_idade,
        arranjos.obter_repositorio().coeficientes,
        estrutura_etaria.obter_repositorio().anos,
    ]


@asynccontextmanager
async def _ciclo_de_vida(_: FastAPI):
    # lê as tabelas em segundo plano para a primeira consulta do front-end não esperar
    threading.Thread(target=lambda: aquecer(_cargas_iniciais()), daemon=True).start()
    yield


def criar_app(config: Configuracao | None = None) -> FastAPI:
    config = config or carregar_configuracao(dotenv=DOTENV)
    app = FastAPI(
        title="PROCED API",
        description="Projeção de Consumo por Estrutura Demográfica (RF11, RNF09)",
        version="0.2.0",
        lifespan=_ciclo_de_vida,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.cors_origin],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.add_exception_handler(ErroFonteDados, _fonte_indisponivel)
    app.add_exception_handler(ErroConfiguracao, _fonte_indisponivel)
    for modulo in (projecoes, arranjos, estrutura_etaria, simulador, fontes):
        app.include_router(modulo.router)
    return app


app = criar_app()
