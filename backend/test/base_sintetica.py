"""Base sintética para os testes de consistência: a classe Dados real lendo um cliente falso que
imita a REST do Supabase (filtros in, eq e gte), com quatro UFs de duas regiões, as 21 células
em cada UF, POFs anteriores com outra divisão de arranjos (para a tendência agir) e a projeção
da população com linhas de total e os três sexos, como na tabela real."""

import random

from app.dados import Dados
from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL

UFS_SINTETICAS = ("DF", "GO", "SP", "RJ")  # Centro-Oeste e Sudeste
IDADES_CHEFE = (22, 27, 33, 38, 44, 47, 52, 57, 63, 67, 72, 76, 83, 91)
ANOS_POP = (2018, *range(2026, 2071))
MORADORES = {UNIPESSOAL: (1,), CASAL_OU_DUPLA: (2,), MULTIPESSOAL: (3, 4, 5)}


def _domicilios():
    rng = random.Random(42)
    linhas, n = [], 0
    for uf in UFS_SINTETICAS:
        for idade in IDADES_CHEFE:
            for arranjo, moradores in MORADORES.items():
                for _ in range(3):
                    n += 1
                    m = rng.choice(moradores)
                    consumo = round(60 + 35 * m + 0.6 * idade + rng.uniform(0, 80), 1)
                    linhas.append(
                        {
                            "id_domicilio": n,
                            "sigla_uf": uf,
                            "qtd_moradores": m,
                            "arranjo_familiar": arranjo,
                            "idade_chefe": idade,
                            "consumo_total_kwh": consumo,
                            "consumo_per_capita_kwh": consumo / m,
                            "peso_final": round(rng.uniform(200, 4000), 2),
                            "gasto_total_rs": None,
                        }
                    )
    return linhas


def _historica():
    """2002 e 2008 com mais multipessoais que 2017: a tendência aumenta uni e casal."""
    rng = random.Random(7)
    linhas, n = [], 0
    for ano, (p_uni, p_cas) in ((2002, (0.10, 0.18)), (2008, (0.13, 0.21))):
        for idade in IDADES_CHEFE:
            for _ in range(60):
                n += 1
                sorteio = rng.random()
                arranjo = UNIPESSOAL if sorteio < p_uni else CASAL_OU_DUPLA if sorteio < p_uni + p_cas else MULTIPESSOAL
                linhas.append(
                    {"ano_pof": ano, "id_domicilio": n, "arranjo_familiar": arranjo, "idade_chefe": idade,
                     "peso_final": round(rng.uniform(500, 3000), 2), "energia_rede_geral": rng.random() > 0.05}
                )
    return linhas


def _populacao():
    """Por UF, ano, sexo e idade (0 a 90); os idosos crescem ao longo do horizonte. "Ambos" é a soma
    exata de Homem e Mulher, e há linhas de total (região e Brasil) que nunca podem entrar na conta."""
    linhas, n = [], 0
    for i, uf in enumerate(UFS_SINTETICAS):
        for ano in ANOS_POP:
            t = ano - 2018
            for idade in range(0, 91):
                base = 1000 + 37 * i + 5 * (idade % 7)
                fator = 1 + (0.012 * t if idade >= 60 else -0.002 * t)
                homem = round(base * fator * 0.97)
                mulher = round(base * fator * 1.03)
                for sexo, valor in (("Homem", homem), ("Mulher", mulher), ("Ambos", homem + mulher)):
                    n += 1
                    linhas.append({"id": n, "localidade": uf, "sexo": sexo, "ano": ano, "idade": idade, "populacao": valor})
    totais = [{**l, "localidade": nome, "populacao": l["populacao"] * 9} for l in linhas[:5000] for nome in ("Brasil", "Centro-Oeste")]
    return linhas + totais


class ClienteSintetico:
    def __init__(self):
        self.tabelas = {
            "fato_consumo_domiciliar": _domicilios(),
            "fato_consumo_pof_historica": _historica(),
            "projecoes_populacao_idade": _populacao(),
        }

    @staticmethod
    def _passa(linha, campo, filtro):
        operador, valor = filtro.split(".", 1)
        if operador == "eq":
            return str(linha[campo]) == valor
        if operador == "in":
            return str(linha[campo]) in valor.strip("()").split(",")
        if operador == "gte":
            return float(linha[campo]) >= float(valor)
        raise ValueError(f"filtro não imitado: {filtro}")

    def selecionar(self, tabela, colunas, filtros=None):
        if tabela == "cenario_salvo":
            return []
        filtros = {k: v for k, v in (filtros or {}).items() if k != "order"}
        return [l for l in self.tabelas[tabela] if all(self._passa(l, c, f) for c, f in filtros.items())]

    def gravar(self, tabela, linhas, conflito):
        return None  # cenário salvo (RF09) não interessa aqui


def dados_sinteticos() -> Dados:
    return Dados(ClienteSintetico())
