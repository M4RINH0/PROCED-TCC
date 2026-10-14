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


# ---------- localidades: Brasil, regiões e UFs (mesmos nomes da tabela de projeção) ----------

BRASIL = "Brasil"

REGIOES = {
    "Norte": ("AC", "AM", "AP", "PA", "RO", "RR", "TO"),
    "Nordeste": ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "Centro-Oeste": ("DF", "GO", "MS", "MT"),
    "Sudeste": ("ES", "MG", "RJ", "SP"),
    "Sul": ("PR", "RS", "SC"),
}

NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
    "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}

Localidade = Enum(
    "Localidade",
    {nome.replace("-", "_"): nome for nome in (BRASIL, *REGIOES, *NOMES_UF)},
    type=str,
)


def ufs_da_localidade(localidade: str) -> set[str] | None:
    """UFs que compõem a localidade; None para o Brasil inteiro (sem filtro)."""
    if localidade == BRASIL:
        return None
    if localidade in REGIOES:
        return set(REGIOES[localidade])
    if localidade in NOMES_UF:
        return {localidade}
    raise ValueError(f"localidade desconhecida: {localidade}")


def da_localidade(domicilios: Iterable, localidade: str) -> list:
    """Domicílios da POF que pertencem à localidade."""
    ufs = ufs_da_localidade(localidade)
    return list(domicilios) if ufs is None else [d for d in domicilios if d.uf in ufs]


UFS = tuple(sorted(NOMES_UF))  # as 27 siglas: a lista explícita que evita somar regiões e Brasil
SEXO_AMBOS = "Ambos"


def ufs_explicitas(localidade: str) -> tuple[str, ...]:
    """UFs da localidade, sempre por extenso (o Brasil são as 27 siglas)."""
    ufs = ufs_da_localidade(localidade)
    return UFS if ufs is None else tuple(sorted(ufs))


def somar_populacao(linhas: Iterable[dict], ufs: Iterable[str], sexo: str = SEXO_AMBOS) -> dict[int, dict[int, int]]:
    """Soma a projeção por ano e idade só nas UFs pedidas e num único sexo.

    Descarta as linhas de total (regiões, Brasil) e as do outro sexo, que
    duplicariam a contagem. Cada linha precisa de localidade, sexo, ano, idade e populacao.
    """
    ufs = set(ufs)
    desconhecidas = ufs - set(UFS)
    if desconhecidas:
        raise ValueError(f"siglas de UF desconhecidas: {sorted(desconhecidas)}")
    populacao: dict[int, dict[int, int]] = {}
    for l in linhas:
        if l["localidade"] not in ufs or l["sexo"] != sexo:
            continue
        ano = populacao.setdefault(int(l["ano"]), {})
        idade = int(l["idade"])
        ano[idade] = ano.get(idade, 0) + int(l["populacao"])
    return populacao


def faixa_do_chefe(idade: int) -> Faixa | None:
    return next((f for f in FAIXAS_CHEFE if f.contem(idade)), None)


def sem_repeticao(domicilios: Iterable) -> list:
    """Premissa P8: um id_domicilio repetido fica só com a linha do chefe de maior idade.

    As repetições vêm de domicílios com mais de uma unidade de consumo na POF.
    Linhas sem id_domicilio passam todas. A ordem de entrada é preservada.
    """
    escolhido: dict[object, int] = {}
    lista = list(domicilios)
    for i, d in enumerate(lista):
        chave = getattr(d, "id_domicilio", None)
        if chave is None:
            continue
        atual = escolhido.get(chave)
        if atual is None or d.idade_chefe > lista[atual].idade_chefe:
            escolhido[chave] = i
    manter = set(escolhido.values())
    return [d for i, d in enumerate(lista) if getattr(d, "id_domicilio", None) is None or i in manter]
