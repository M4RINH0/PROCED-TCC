"""Leitura das tabelas do Supabase (só leitura).

Cada consulta é feita uma vez e mantida em memória: os dados são estáticos. A projeção
populacional é lida uma vez para as 27 UFs (por idade e por sexo), e o Brasil e as regiões
são somados em memória pela lista explícita de siglas (RNF02). O cache também guarda o
que deriva só dos dados (`derivado`), como a tendência dos arranjos e a base da projeção
de cada localidade; só a parte que depende dos controles de simulação é recalculada.
"""

import json
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.dominio import ANO_INICIAL, ANO_REFERENCIA_POF, BRASIL, SEXO_AMBOS, UFS, sem_repeticao, ufs_explicitas
from app.supabase import ClienteSupabase, obter_cliente

COLUNAS_DOMICILIOS = (
    "id_domicilio,sigla_uf,arranjo_familiar,idade_chefe,qtd_moradores,"
    "consumo_total_kwh,consumo_per_capita_kwh,gasto_total_rs,peso_final"
)


@dataclass(frozen=True)
class Domicilio:
    arranjo: str
    idade_chefe: int
    consumo_per_capita_kwh: float
    uf: str = ""
    peso: float = 1.0  # peso_final da POF; 1 nos testes que contam domicílios da amostra
    consumo_total_kwh: float | None = None
    moradores: int | None = None
    id_domicilio: int | None = None
    gasto_rs: float | None = None


@dataclass(frozen=True)
class DomicilioHistorico:
    """POF 2002 a 2003 ou 2008 a 2009: só o que a tendência dos arranjos usa (P13)."""

    ano_pof: int
    arranjo: str
    idade_chefe: int
    peso: float
    rede_geral: bool = True


class Dados:
    """Acesso às tabelas usadas pela API. Nos testes, qualquer objeto com os mesmos
    métodos serve no lugar desta classe."""

    def __init__(self, cliente: ClienteSupabase, arquivo_cenarios: Path | None = None):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._travas: dict[str, threading.Lock] = {}
        self._cache: dict[str, object] = {}
        self._arquivo_cenarios = arquivo_cenarios
        self._cenarios: dict[str, dict] = self._ler_arquivo_cenarios()

    def _ler_arquivo_cenarios(self) -> dict[str, dict]:
        if not self._arquivo_cenarios or not self._arquivo_cenarios.exists():
            return {}
        return json.loads(self._arquivo_cenarios.read_text(encoding="utf-8"))

    def obter_cenario(self, chave: str) -> dict | None:
        with self._trava:
            salvo = self._cenarios.get(chave)
            return None if salvo is None else dict(salvo)

    def salvar_cenario(self, chave: str, cenario: dict) -> None:
        with self._trava:
            self._cenarios[chave] = dict(cenario)
            if self._arquivo_cenarios:
                self._arquivo_cenarios.parent.mkdir(parents=True, exist_ok=True)
                self._arquivo_cenarios.write_text(
                    json.dumps(self._cenarios, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    def _uma_vez(self, chave: str, carregar):
        """Carrega uma vez por chave. Cada chave tem a sua trava: uma leitura longa não
        bloqueia as outras, e duas requisições da mesma chave não leem o banco duas vezes."""
        if chave in self._cache:
            return self._cache[chave]
        with self._trava:
            trava = self._travas.setdefault(chave, threading.Lock())
        with trava:
            if chave not in self._cache:
                self._cache[chave] = carregar()
        return self._cache[chave]

    def derivado(self, chave: str, calcular):
        """Guarda um valor calculado só a partir das tabelas (não depende dos controles)."""
        return self._uma_vez(f"derivado:{chave}", calcular)

    def domicilios(self) -> list[Domicilio]:
        """fato_consumo_domiciliar: um domicílio da POF por linha, com a UF e o peso,
        já sem as linhas repetidas (premissa P8)."""

        def carregar():
            linhas = self._cliente.selecionar(
                "fato_consumo_domiciliar", COLUNAS_DOMICILIOS, {"order": "id_domicilio.asc"}
            )
            return sem_repeticao(
                Domicilio(
                    l["arranjo_familiar"],
                    int(l["idade_chefe"]),
                    float(l["consumo_per_capita_kwh"]),
                    l["sigla_uf"],
                    float(l["peso_final"]),
                    float(l["consumo_total_kwh"]),
                    int(l["qtd_moradores"]),
                    int(l["id_domicilio"]),
                    None if l.get("gasto_total_rs") is None else float(l["gasto_total_rs"]),
                )
                for l in linhas
            )

        return self._uma_vez("domicilios", carregar)

    def domicilios_historicos(self) -> list[DomicilioHistorico]:
        """fato_consumo_pof_historica: POFs 2002 a 2003 e 2008 a 2009, todos os registros.

        O filtro da rede geral fica no cálculo (P13).
        """

        def carregar():
            linhas = self._cliente.selecionar(
                "fato_consumo_pof_historica",
                "ano_pof,arranjo_familiar,idade_chefe,peso_final,energia_rede_geral",
                {"order": "ano_pof.asc,id_domicilio.asc"},
            )
            return [
                DomicilioHistorico(
                    int(l["ano_pof"]), l["arranjo_familiar"], int(l["idade_chefe"]), float(l["peso_final"]), bool(l["energia_rede_geral"])
                )
                for l in linhas
            ]

        return self._uma_vez("domicilios_historicos", carregar)

    def _populacao_das_ufs(self) -> dict[str, dict[int, dict[int, int]]]:
        """As 27 UFs, ambos os sexos, de 2018 em diante: UF -> ano -> idade -> população.

        Uma leitura só; as linhas de total da tabela (regiões e Brasil) nunca são lidas.
        """

        def carregar():
            linhas = self._cliente.selecionar(
                "projecoes_populacao_idade",
                "localidade,ano,idade,populacao",
                {
                    "localidade": f"in.({','.join(UFS)})",
                    "sexo": f"eq.{SEXO_AMBOS}",
                    "ano": f"gte.{ANO_REFERENCIA_POF}",
                    "order": "id.asc",
                },
            )
            por_uf: dict[str, dict[int, dict[int, int]]] = {}
            for l in linhas:
                por_uf.setdefault(l["localidade"], {}).setdefault(int(l["ano"]), {})[int(l["idade"])] = int(l["populacao"])
            return por_uf

        return self._uma_vez("populacao_ufs", carregar)

    def populacao_por_idade(self, localidade: str = BRASIL) -> dict[int, dict[int, int]]:
        """Ambos os sexos na localidade: ano -> idade -> população (2018 e o horizonte),
        somando as UFs da localidade pela lista explícita de siglas (o Brasil são as 27)."""

        def somar():
            por_uf = self._populacao_das_ufs()
            populacao: dict[int, dict[int, int]] = {}
            for uf in ufs_explicitas(localidade):
                for ano, idades in por_uf.get(uf, {}).items():
                    destino = populacao.setdefault(ano, {})
                    for idade, p in idades.items():
                        destino[idade] = destino.get(idade, 0) + p
            return populacao

        return self._uma_vez(f"populacao:{localidade}", somar)

    def _por_sexo_das_ufs(self) -> dict[str, dict[int, dict[str, dict[int, int]]]]:
        """As 27 UFs, homens e mulheres, de 2026 em diante: UF -> ano -> sexo -> idade -> população."""

        def carregar():
            linhas = self._cliente.selecionar(
                "projecoes_populacao_idade",
                "localidade,ano,sexo,idade,populacao",
                {
                    "localidade": f"in.({','.join(UFS)})",
                    "sexo": "in.(Homem,Mulher)",
                    "ano": f"gte.{ANO_INICIAL}",
                    "order": "id.asc",
                },
            )
            por_uf: dict[str, dict[int, dict[str, dict[int, int]]]] = {}
            for l in linhas:
                ano = por_uf.setdefault(l["localidade"], {}).setdefault(int(l["ano"]), {"Homem": {}, "Mulher": {}})
                ano[l["sexo"]][int(l["idade"])] = int(l["populacao"])
            return por_uf

        return self._uma_vez("por_sexo_ufs", carregar)

    def _por_sexo(self, localidade: str) -> dict[int, dict[str, dict[int, int]]]:
        def somar():
            por_uf = self._por_sexo_das_ufs()
            dados: dict[int, dict[str, dict[int, int]]] = {}
            for uf in ufs_explicitas(localidade):
                for ano, sexos in por_uf.get(uf, {}).items():
                    destino = dados.setdefault(ano, {"Homem": {}, "Mulher": {}})
                    for sexo, idades in sexos.items():
                        for idade, p in idades.items():
                            destino[sexo][idade] = destino[sexo].get(idade, 0) + p
            return dados

        return self._uma_vez(f"por_sexo:{localidade}", somar)

    def populacao_por_sexo(self, ano: int, localidade: str = BRASIL) -> dict[str, dict[int, int]]:
        """Localidade no ano: {"Homem": {idade: pop}, "Mulher": {idade: pop}}; vazio se não houver o ano."""
        return self._por_sexo(localidade).get(ano, {"Homem": {}, "Mulher": {}})

    def anos_piramide(self, localidade: str = BRASIL) -> list[int]:
        return sorted(self._por_sexo(localidade))


@lru_cache
def obter_dados() -> Dados:
    """Dependência das rotas: uma instância para a aplicação inteira."""
    return Dados(obter_cliente())
