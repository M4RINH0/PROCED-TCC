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

    def _get(self, tabela: str, parametros: dict, cabecalhos: dict) -> httpx.Response:
        try:
            resposta = self._http.get(f"{self._base}/{tabela}", params=parametros, headers={**self._cabecalhos, **cabecalhos})
        except httpx.HTTPError as erro:
            raise ErroFonteDados(f"falha ao consultar {tabela}") from erro
        if resposta.status_code >= 400:
            raise ErroFonteDados(f"{tabela} respondeu com o código {resposta.status_code}")
        return resposta

    def selecionar(self, tabela: str, colunas: str, filtros: dict[str, str] | None = None) -> list[dict]:
        """Devolve todas as linhas, paginando de mil em mil.

        A primeira página pede a contagem exata (Content-Range). Com ela, a leitura
        só termina quando todas as linhas chegaram, mesmo que o servidor devolva
        páginas menores que o pedido; se faltar alguma, levanta erro em vez de
        devolver a tabela pela metade.
        """
        linhas: list[dict] = []
        parametros = {"select": colunas, **(filtros or {})}
        total: int | None = None
        inicio = 0
        while True:
            cabecalhos = {"Range": f"{inicio}-{inicio + self._pagina - 1}"}
            if inicio == 0:
                cabecalhos["Prefer"] = "count=exact"
            resposta = self._get(tabela, parametros, cabecalhos)
            pagina = resposta.json()
            if inicio == 0:
                total = total_do_intervalo(resposta.headers.get("content-range"))
            linhas.extend(pagina)
            if total is None:
                if len(pagina) < self._pagina:
                    return linhas
                inicio += self._pagina
                continue
            if len(linhas) >= total:
                return linhas
            if not pagina:
                raise ErroFonteDados(f"{tabela}: foram lidas {len(linhas)} de {total} linhas")
            inicio += len(pagina)

    def contar(self, tabela: str, filtros: dict[str, str] | None = None) -> int:
        """Número de linhas que a consulta devolveria (count exato no banco)."""
        resposta = self._get(tabela, {"select": "*", **(filtros or {})}, {"Range": "0-0", "Prefer": "count=exact"})
        total = total_do_intervalo(resposta.headers.get("content-range"))
        if total is None:
            raise ErroFonteDados(f"{tabela} não informou a contagem de linhas")
        return total


def total_do_intervalo(content_range: str | None) -> int | None:
    """Total de um cabeçalho Content-Range como "0-999/52207" ou "*/0"; None se não houver."""
    if not content_range or "/" not in content_range:
        return None
    total = content_range.rsplit("/", 1)[1]
    return int(total) if total.isdigit() else None


def criar_cliente(config: Configuracao) -> ClienteSupabase:
    if not config.supabase_url or not config.supabase_secret_key:
        raise ErroConfiguracao("SUPABASE_URL e SUPABASE_SECRET_KEY precisam estar configuradas")
    return ClienteSupabase(config.supabase_url, config.supabase_secret_key)


@lru_cache
def obter_cliente() -> ClienteSupabase:
    """Cliente único da aplicação, criado na primeira consulta."""
    return criar_cliente(carregar_configuracao(dotenv=DOTENV))
