"""Leitura das tabelas do Supabase pela API REST (PostgREST).

Só leitura. A chave secreta fica no back-end (RNF05); o front-end nunca acessa
o banco (RNF10). Os filtros vão como parâmetros da requisição, nunca montados
por concatenação de SQL.
"""

from functools import lru_cache

import httpx

from app.config import DOTENV, Configuracao, ErroConfiguracao, ErroFonteDados, carregar_configuracao

TAMANHO_PAGINA = 1000  # limite de linhas por resposta do Supabase


class ClienteSupabase:
    def __init__(self, url: str, chave: str, http: httpx.Client | None = None, tamanho_pagina: int = TAMANHO_PAGINA):
        self._base = url.rstrip("/") + "/rest/v1"
        self._http = http or httpx.Client(timeout=30)
        self._cabecalhos = {"apikey": chave}
        self._pagina = tamanho_pagina

    def selecionar(self, tabela: str, colunas: str, filtros: dict[str, str] | None = None) -> list[dict]:
        """Devolve todas as linhas, paginando de mil em mil."""
        linhas: list[dict] = []
        inicio = 0
        while True:
            cabecalhos = {**self._cabecalhos, "Range": f"{inicio}-{inicio + self._pagina - 1}"}
            parametros = {"select": colunas, **(filtros or {})}
            try:
                resposta = self._http.get(f"{self._base}/{tabela}", params=parametros, headers=cabecalhos)
            except httpx.HTTPError as erro:
                raise ErroFonteDados(f"falha ao consultar {tabela}") from erro
            if resposta.status_code >= 400:
                raise ErroFonteDados(f"{tabela} respondeu com o código {resposta.status_code}")
            pagina = resposta.json()
            linhas.extend(pagina)
            if len(pagina) < self._pagina:
                return linhas
            inicio += self._pagina


def criar_cliente(config: Configuracao) -> ClienteSupabase:
    if not config.supabase_url or not config.supabase_secret_key:
        raise ErroConfiguracao("SUPABASE_URL e SUPABASE_SECRET_KEY precisam estar configuradas")
    return ClienteSupabase(config.supabase_url, config.supabase_secret_key)


@lru_cache
def obter_cliente() -> ClienteSupabase:
    """Cliente único da aplicação, criado na primeira consulta."""
    return criar_cliente(carregar_configuracao(dotenv=DOTENV))
