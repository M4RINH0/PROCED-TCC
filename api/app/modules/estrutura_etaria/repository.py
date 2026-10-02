import threading
from typing import Protocol

from app.core import ClienteSupabase


class RepositorioPiramide(Protocol):
    def populacao_por_sexo(self, ano: int) -> dict[str, dict[int, int]]:
        """Brasil no ano: {"Homem": {idade: pop}, "Mulher": {idade: pop}}."""
        ...


class RepositorioSupabase:
    def __init__(self, cliente: ClienteSupabase):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._cache: dict[int, dict[str, dict[int, int]]] = {}

    def populacao_por_sexo(self, ano: int) -> dict[str, dict[int, int]]:
        with self._trava:
            if ano not in self._cache:
                linhas = self._cliente.selecionar(
                    "projecoes_populacao_idade",
                    "sexo,idade,populacao",
                    {"localidade": "eq.Brasil", "sexo": "in.(Homem,Mulher)", "ano": f"eq.{int(ano)}", "order": "id.asc"},
                )
                por_sexo: dict[str, dict[int, int]] = {"Homem": {}, "Mulher": {}}
                for l in linhas:
                    por_sexo[l["sexo"]][int(l["idade"])] = int(l["populacao"])
                self._cache[ano] = por_sexo
            return self._cache[ano]
