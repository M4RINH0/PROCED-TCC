"""Acesso aos dados da projeção no Supabase (só leitura).

As tabelas são lidas uma vez e mantidas em memória: são estáticas e a API do
Supabase devolve no máximo mil linhas por consulta.
"""

import threading
from dataclasses import dataclass
from typing import Protocol

from app.core import ClienteSupabase


@dataclass(frozen=True)
class Domicilio:
    arranjo: str
    idade_chefe: int
    consumo_per_capita_kwh: float


class RepositorioProjecoes(Protocol):
    def domicilios(self) -> list[Domicilio]: ...

    def populacao_por_idade(self) -> dict[int, dict[int, int]]:
        """Brasil, ambos os sexos: ano -> idade -> população."""
        ...


class RepositorioSupabase:
    def __init__(self, cliente: ClienteSupabase):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._domicilios: list[Domicilio] | None = None
        self._populacao: dict[int, dict[int, int]] | None = None

    def domicilios(self) -> list[Domicilio]:
        with self._trava:
            if self._domicilios is None:
                linhas = self._cliente.selecionar(
                    "fato_consumo_domiciliar",
                    "arranjo_familiar,idade_chefe,consumo_per_capita_kwh",
                    {"order": "id_domicilio.asc"},
                )
                self._domicilios = [
                    Domicilio(l["arranjo_familiar"], int(l["idade_chefe"]), float(l["consumo_per_capita_kwh"]))
                    for l in linhas
                ]
            return self._domicilios

    def populacao_por_idade(self) -> dict[int, dict[int, int]]:
        with self._trava:
            if self._populacao is None:
                linhas = self._cliente.selecionar(
                    "projecoes_populacao_idade",
                    "ano,idade,populacao",
                    {"localidade": "eq.Brasil", "sexo": "eq.Ambos", "order": "id.asc"},
                )
                populacao: dict[int, dict[int, int]] = {}
                for l in linhas:
                    populacao.setdefault(int(l["ano"]), {})[int(l["idade"])] = int(l["populacao"])
                self._populacao = populacao
            return self._populacao
