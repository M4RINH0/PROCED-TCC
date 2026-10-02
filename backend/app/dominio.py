"""Regras do domínio usadas por várias páginas: horizonte, recortes, arranjos e faixas etárias."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

ANO_INICIAL = 2026
ANO_FINAL = 2070  # horizonte do estudo: o mesmo ano em que termina a projeção oficial do IBGE
ANO_REFERENCIA_POF = 2018  # POF 2017 a 2018
IDADE_IDOSO = 60


class Recorte(str, Enum):
    chefe_60_mais = "chefe_60_mais"
    mononuclear_abaixo_60 = "mononuclear_abaixo_60"


class FiltroArranjo(str, Enum):
    mononucleares = "mononucleares"  # unipessoal e casal ou dupla
    unipessoal = "unipessoal"
    casal_ou_dupla = "casal_ou_dupla"
    multipessoal = "multipessoal"
    todos = "todos"


UNIPESSOAL = "Unipessoal (Mononuclear)"
CASAL_OU_DUPLA = "Casal ou Dupla"
MULTIPESSOAL = "Multipessoal (3+)"

# Mononuclear = unipessoal ou casal; casal de idosos = dois moradores com chefe de 60 anos ou mais
ARRANJOS_DO_FILTRO = {
    FiltroArranjo.mononucleares: {UNIPESSOAL, CASAL_OU_DUPLA},
    FiltroArranjo.unipessoal: {UNIPESSOAL},
    FiltroArranjo.casal_ou_dupla: {CASAL_OU_DUPLA},
    FiltroArranjo.multipessoal: {MULTIPESSOAL},
    FiltroArranjo.todos: {UNIPESSOAL, CASAL_OU_DUPLA, MULTIPESSOAL},
}

IDADE_MINIMA_CHEFE = 12  # menor idade de chefe na POF carregada no banco


@dataclass(frozen=True)
class Faixa:
    rotulo: str
    minima: int
    maxima: int | None  # None: sem limite superior (a idade 90 da projeção agrega 90 ou mais)

    def contem(self, idade: int) -> bool:
        return idade >= self.minima and (self.maxima is None or idade <= self.maxima)


FAIXAS_CHEFE = (
    Faixa("até 29", IDADE_MINIMA_CHEFE, 29),
    Faixa("30 a 39", 30, 39),
    Faixa("40 a 49", 40, 49),
    Faixa("50 a 59", 50, 59),
    Faixa("60 a 69", 60, 69),
    Faixa("70 a 79", 70, 79),
    Faixa("80+", 80, None),
)

FAIXAS_DO_RECORTE = {
    Recorte.chefe_60_mais: FAIXAS_CHEFE[4:],
    Recorte.mononuclear_abaixo_60: FAIXAS_CHEFE[:4],
}


def filtrar(domicilios: Iterable, filtro: FiltroArranjo) -> list:
    arranjos = ARRANJOS_DO_FILTRO[filtro]
    return [d for d in domicilios if d.arranjo in arranjos]


def da_faixa(domicilios: Iterable, faixa: Faixa) -> list:
    return [d for d in domicilios if faixa.contem(d.idade_chefe)]


def populacao_da_faixa(populacao_do_ano: dict[int, int], faixa: Faixa) -> int:
    return sum(p for idade, p in populacao_do_ano.items() if faixa.contem(idade))
