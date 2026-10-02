import threading
from typing import Protocol

from app.core import ClienteSupabase

ANO_INICIAL = 2026


class RepositorioPiramide(Protocol):
    def populacao_por_sexo(self, ano: int) -> dict[str, dict[int, int]]:
        """Brasil no ano: {"Homem": {idade: pop}, "Mulher": {idade: pop}}; vazio se não houver o ano."""
        ...

    def anos(self) -> list[int]: ...


class RepositorioSupabase:
    """Lê de uma vez a população do Brasil por sexo e idade, de 2026 em diante."""

    def __init__(self, cliente: ClienteSupabase):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._dados: dict[int, dict[str, dict[int, int]]] | None = None

    def _carregar(self) -> dict[int, dict[str, dict[int, int]]]:
        with self._trava:
            if self._dados is None:
                linhas = self._cliente.selecionar(
                    "projecoes_populacao_idade",
                    "ano,sexo,idade,populacao",
                    {"localidade": "eq.Brasil", "sexo": "in.(Homem,Mulher)", "ano": f"gte.{ANO_INICIAL}", "order": "id.asc"},
                )
                dados: dict[int, dict[str, dict[int, int]]] = {}
                for l in linhas:
                    ano = dados.setdefault(int(l["ano"]), {"Homem": {}, "Mulher": {}})
                    ano[l["sexo"]][int(l["idade"])] = int(l["populacao"])
                self._dados = dados
            return self._dados

    def populacao_por_sexo(self, ano: int) -> dict[str, dict[int, int]]:
        return self._carregar().get(ano, {"Homem": {}, "Mulher": {}})

    def anos(self) -> list[int]:
        return sorted(self._carregar())
