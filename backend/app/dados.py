"""Leitura das tabelas do Supabase (só leitura).

Cada consulta é feita uma vez e mantida em memória: os dados são estáticos e a API
do Supabase devolve no máximo mil linhas por consulta. A projeção populacional é
lida por localidade (Brasil, região ou UF) na primeira vez em que é pedida.
"""

import threading
from dataclasses import dataclass
from functools import lru_cache

from app.dominio import ANO_INICIAL, ANO_REFERENCIA_POF, BRASIL
from app.supabase import ClienteSupabase, obter_cliente

COLUNAS_COEFICIENTES = (
    "sigla_uf,arranjo_familiar,is_60_mais,total_domicilios_amostra,"
    "media_consumo_total_kwh,media_consumo_per_capita_kwh,media_gasto_rs"
)


@dataclass(frozen=True)
class Domicilio:
    arranjo: str
    idade_chefe: int
    consumo_per_capita_kwh: float
    uf: str = ""


class Dados:
    """Acesso às tabelas usadas pela API. Nos testes, qualquer objeto com os mesmos
    métodos serve no lugar desta classe."""

    def __init__(self, cliente: ClienteSupabase):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._cache: dict[str, object] = {}

    def _uma_vez(self, chave: str, carregar):
        with self._trava:
            if chave not in self._cache:
                self._cache[chave] = carregar()
            return self._cache[chave]

    def domicilios(self) -> list[Domicilio]:
        """fato_consumo_domiciliar: um domicílio da POF por linha, com a UF."""

        def carregar():
            linhas = self._cliente.selecionar(
                "fato_consumo_domiciliar",
                "sigla_uf,arranjo_familiar,idade_chefe,consumo_per_capita_kwh",
                {"order": "id_domicilio.asc"},
            )
            return [
                Domicilio(l["arranjo_familiar"], int(l["idade_chefe"]), float(l["consumo_per_capita_kwh"]), l["sigla_uf"])
                for l in linhas
            ]

        return self._uma_vez("domicilios", carregar)

    def populacao_por_idade(self, localidade: str = BRASIL) -> dict[int, dict[int, int]]:
        """Ambos os sexos na localidade: ano -> idade -> população (2018 e o horizonte)."""

        def carregar():
            linhas = self._cliente.selecionar(
                "projecoes_populacao_idade",
                "ano,idade,populacao",
                {
                    "localidade": f"eq.{localidade}",
                    "sexo": "eq.Ambos",
                    "ano": f"gte.{ANO_REFERENCIA_POF}",
                    "order": "id.asc",
                },
            )
            populacao: dict[int, dict[int, int]] = {}
            for l in linhas:
                populacao.setdefault(int(l["ano"]), {})[int(l["idade"])] = int(l["populacao"])
            return populacao

        return self._uma_vez(f"populacao:{localidade}", carregar)

    def coeficientes(self) -> list[dict]:
        """dim_coeficiente_consumo: uma linha por UF, arranjo e indicador 60+."""
        return self._uma_vez(
            "coeficientes",
            lambda: self._cliente.selecionar("dim_coeficiente_consumo", COLUNAS_COEFICIENTES, {"order": "id.asc"}),
        )

    def _por_sexo(self, localidade: str) -> dict[int, dict[str, dict[int, int]]]:
        def carregar():
            linhas = self._cliente.selecionar(
                "projecoes_populacao_idade",
                "ano,sexo,idade,populacao",
                {
                    "localidade": f"eq.{localidade}",
                    "sexo": "in.(Homem,Mulher)",
                    "ano": f"gte.{ANO_INICIAL}",
                    "order": "id.asc",
                },
            )
            dados: dict[int, dict[str, dict[int, int]]] = {}
            for l in linhas:
                ano = dados.setdefault(int(l["ano"]), {"Homem": {}, "Mulher": {}})
                ano[l["sexo"]][int(l["idade"])] = int(l["populacao"])
            return dados

        return self._uma_vez(f"por_sexo:{localidade}", carregar)

    def populacao_por_sexo(self, ano: int, localidade: str = BRASIL) -> dict[str, dict[int, int]]:
        """Localidade no ano: {"Homem": {idade: pop}, "Mulher": {idade: pop}}; vazio se não houver o ano."""
        return self._por_sexo(localidade).get(ano, {"Homem": {}, "Mulher": {}})

    def anos_piramide(self, localidade: str = BRASIL) -> list[int]:
        return sorted(self._por_sexo(localidade))


@lru_cache
def obter_dados() -> Dados:
    """Dependência das rotas: uma instância para a aplicação inteira."""
    return Dados(obter_cliente())
