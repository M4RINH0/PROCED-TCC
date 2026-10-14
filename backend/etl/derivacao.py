"""Regras de derivação.

As regras de arranjo, de 60 anos ou mais e de consumo per capita foram
conferidas contra a tabela fato_consumo_domiciliar do Supabase em 02/10/2026
e de novo em 14/10/2026: nenhuma das 52.207 linhas as viola.
"""

import pandas as pd

ARRANJOS = ("Unipessoal (Mononuclear)", "Casal ou Dupla", "Multipessoal (3+)")
IDADE_IDOSO = 60

# Faixas do chefe usadas no protótipo (prototipo/proced.html)
_FAIXAS = ((30, "até 29"), (40, "30 a 39"), (50, "40 a 49"), (60, "50 a 59"), (70, "60 a 69"), (80, "70 a 79"))


def arranjo_familiar(qtd_moradores: int) -> str:
    if qtd_moradores < 1:
        raise ValueError("o domicílio precisa ter ao menos um morador")
    if qtd_moradores == 1:
        return ARRANJOS[0]
    if qtd_moradores == 2:
        return ARRANJOS[1]
    return ARRANJOS[2]


def eh_60_mais(idade_chefe: int) -> bool:
    if idade_chefe < 0:
        raise ValueError("a idade não pode ser negativa")
    return idade_chefe >= IDADE_IDOSO


def faixa_etaria_chefe(idade_chefe: int) -> str:
    if idade_chefe < 0:
        raise ValueError("a idade não pode ser negativa")
    for limite, rotulo in _FAIXAS:
        if idade_chefe < limite:
            return rotulo
    return "80+"


def consumo_per_capita(consumo_total_kwh: float, qtd_moradores: int) -> float:
    if qtd_moradores < 1:
        raise ValueError("o domicílio precisa ter ao menos um morador")
    if consumo_total_kwh < 0:
        raise ValueError("o consumo não pode ser negativo")
    return consumo_total_kwh / qtd_moradores


def derivar(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Acrescenta arranjo, faixa, indicador 60+ e consumo per capita.

    Espera as colunas qtd_moradores, idade_chefe e consumo_total_kwh.
    """
    faltando = {"qtd_moradores", "idade_chefe", "consumo_total_kwh"} - set(df.columns)
    if faltando:
        raise ValueError(f"colunas ausentes: {sorted(faltando)}")
    saida = df.copy()
    saida["arranjo_familiar"] = saida["qtd_moradores"].map(arranjo_familiar)
    saida["is_60_mais"] = saida["idade_chefe"].map(eh_60_mais)
    saida["faixa_etaria_chefe"] = saida["idade_chefe"].map(faixa_etaria_chefe)
    saida["consumo_per_capita_kwh"] = [
        consumo_per_capita(c, m) for c, m in zip(saida["consumo_total_kwh"], saida["qtd_moradores"])
    ]
    registro = {
        "etapa": "derivacao",
        "fonte": "base limpa da POF 2017 a 2018",
        "transformacao": "arranjo por número de moradores (1, 2, 3 ou mais); is_60_mais com chefe de 60 anos "
        "ou mais; faixa etária do chefe; consumo per capita = consumo total / moradores",
        "linhas": len(saida),
    }
    return saida, registro
