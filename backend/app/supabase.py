"""Leitura das tabelas do Supabase pela API REST (PostgREST).

Só leitura. A chave secreta fica no back-end (RNF05); o front-end nunca acessa
o banco (RNF10). Os filtros vão como parâmetros da requisição, nunca montados
por concatenação de SQL.
"""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import httpx

from app.config import DOTENV, Configuracao, ErroConfiguracao, ErroFonteDados, carregar_configuracao

TAMANHO_PAGINA = 1000  # limite de linhas por resposta do Supabase
PAGINAS_EM_PARALELO = 6  # páginas pedidas ao mesmo tempo depois da primeira (RNF02)


class ClienteSupabase:
    def __init__(
        self,
        url: str,
        chave: str,
        http: httpx.Client | None = None,
        tamanho_pagina: int = TAMANHO_PAGINA,
        paralelas: int = PAGINAS_EM_PARALELO,
    ):
        self._base = url.rstrip("/") + "/rest/v1"
        self._http = http or httpx.Client(timeout=30, limits=httpx.Limits(max_connections=paralelas + 2))
        self._cabecalhos = {"apikey": chave}
        self._pagina = tamanho_pagina
        self._paralelas = max(1, paralelas)

    def _get(self, tabela: str, parametros: dict, cabecalhos: dict) -> httpx.Response:
        try:
            resposta = self._http.get(f"{self._base}/{tabela}", params=parametros, headers={**self._cabecalhos, **cabecalhos})
        except httpx.HTTPError as erro:
            raise ErroFonteDados(f"falha ao consultar {tabela}") from erro
        if resposta.status_code >= 400:
            raise ErroFonteDados(f"{tabela} respondeu com o código {resposta.status_code}")
        return resposta

    def selecionar(self, tabela: str, colunas: str, filtros: dict[str, str] | None = None) -> list[dict]:
        """Devolve todas as linhas, na ordem pedida.

        A primeira página pede a contagem exata (Content-Range) e mostra quantas linhas o
        servidor devolve por página; as demais são pedidas em paralelo (RNF02). Se faltar
        alguma linha, levanta erro em vez de devolver a tabela pela metade. Sem a contagem,
        pagina em sequência até uma página vir incompleta.
        """
        parametros = {"select": colunas, **(filtros or {})}
        primeira = self._get(tabela, parametros, {"Range": f"0-{self._pagina - 1}", "Prefer": "count=exact"})
        linhas: list[dict] = list(primeira.json())
        total = total_do_intervalo(primeira.headers.get("content-range"))
        if total is None:
            return self._em_sequencia(tabela, parametros, linhas)
        if len(linhas) >= total:
            return linhas
        if not linhas:
            raise ErroFonteDados(f"{tabela}: foram lidas 0 de {total} linhas")
        passo = len(linhas)  # o servidor pode devolver menos linhas que o pedido

        def pagina(inicio: int) -> list[dict]:
            return self._get(tabela, parametros, {"Range": f"{inicio}-{inicio + passo - 1}"}).json()

        with ThreadPoolExecutor(max_workers=self._paralelas) as executor:
            for parte in executor.map(pagina, range(passo, total, passo)):  # map preserva a ordem
                linhas.extend(parte)
        if len(linhas) != total:
            raise ErroFonteDados(f"{tabela}: foram lidas {len(linhas)} de {total} linhas")
        return linhas

    def _em_sequencia(self, tabela: str, parametros: dict, linhas: list[dict]) -> list[dict]:
        pagina = linhas
        inicio = 0
        while len(pagina) == self._pagina:
            inicio += self._pagina
            pagina = self._get(tabela, parametros, {"Range": f"{inicio}-{inicio + self._pagina - 1}"}).json()
            linhas.extend(pagina)
        return linhas

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
