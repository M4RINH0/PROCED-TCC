"""Regras do domínio usadas por várias páginas: horizonte, recortes, arranjos e faixas etárias."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from app.calculo import Projecao, ajustar_envelhecimento, estimar_tendencia, parametros_celulas, proporcoes_arranjos

ANO_INICIAL = 2026
ANO_FINAL = 2070  # horizonte do estudo: o mesmo ano em que termina a projeção da população do IBGE
ANO_REFERENCIA_POF = 2018  # POF 2017 a 2018
IDADE_IDOSO = 60


class Recorte(str, Enum):
    todos_domicilios = "todos_domicilios"  # o único em que o efeito da idade aparece
    chefe_60_mais_todos = "chefe_60_mais_todos"  # chefe de 60 anos ou mais, todos os arranjos
    chefe_60_mais = "chefe_60_mais"  # mononucleares com chefe de 60 anos ou mais
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
    Recorte.todos_domicilios: FAIXAS_CHEFE,
    Recorte.chefe_60_mais_todos: FAIXAS_CHEFE[4:],
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


# ---------- células (faixa do chefe, arranjo) e projeção pelo método das taxas ----------

MINIMO_AMOSTRA = 30  # células com menos domicílios na amostra levam aviso de baixa confiabilidade
ARRANJOS = (UNIPESSOAL, CASAL_OU_DUPLA, MULTIPESSOAL)
MONONUCLEARES = (UNIPESSOAL, CASAL_OU_DUPLA)

ARRANJOS_DO_RECORTE = {
    Recorte.todos_domicilios: ARRANJOS,
    Recorte.chefe_60_mais_todos: ARRANJOS,
    Recorte.chefe_60_mais: MONONUCLEARES,
    Recorte.mononuclear_abaixo_60: MONONUCLEARES,
}
CELULAS_DO_RECORTE = {
    recorte: tuple((f.rotulo, a) for f in faixas for a in ARRANJOS_DO_RECORTE[recorte])
    for recorte, faixas in FAIXAS_DO_RECORTE.items()
}


def baixa_confiabilidade(amostra: int) -> bool:
    return amostra < MINIMO_AMOSTRA


def celula_do_domicilio(d) -> tuple[str, str] | None:
    faixa = faixa_do_chefe(d.idade_chefe)
    return None if faixa is None else (faixa.rotulo, d.arranjo)


def populacao_por_faixa(populacao: dict[int, dict[int, int]]) -> dict[int, dict[str, int]]:
    """Ano -> faixa do chefe -> população (a faixa "até 29" começa em 12 anos, P4)."""
    return {ano: {f.rotulo: populacao_da_faixa(idades, f) for f in FAIXAS_CHEFE} for ano, idades in populacao.items()}


def populacao_total(populacao: dict[int, dict[int, int]]) -> dict[int, int]:
    """Ano -> população de todas as idades, usada na calibração (P12)."""
    return {ano: sum(idades.values()) for ano, idades in populacao.items()}


# ---------- controles de simulação (RF02) e tendência dos arranjos (P13) ----------

# Intensidade padrão calibrada pela validação fora do tempo (P13): o mínimo do erro médio absoluto da
# previsão de 2017 é 0,56, arredondado a 0,6; 0,5 e 1 ficam como faixa de sensibilidade.
INTENSIDADE_PADRAO, INTENSIDADE_MINIMA, INTENSIDADE_MAXIMA = 0.6, 0.0, 1.5  # 0 congela os arranjos a partir de 2026
INTENSIDADES_SENSIBILIDADE = (0.5, 1.0)
K_PADRAO, K_MINIMO, K_MAXIMO = 1.0, 0.5, 1.5  # 1 = estrutura etária do IBGE
GRUPO_0_11 = "0 a 11"  # quem não chefia domicílio; entra só no controle k, para a população fechar
ANOS_MEDIOS_POF = {2002: 2002.5, 2008: 2008.5, 2017: 2017.5}


def em_simulacao(intensidade: float, k: float) -> bool:
    """Valor fora do padrão: a interface rotula o resultado como simulação."""
    return intensidade != INTENSIDADE_PADRAO or k != K_PADRAO


def populacao_por_grupo(populacao: dict[int, dict[int, int]]) -> dict[int, dict[str, int]]:
    """Faixas do chefe mais o grupo de 0 a 11 anos: cobrem todas as idades da projeção."""
    por_faixa = populacao_por_faixa(populacao)
    return {
        ano: {**por_faixa[ano], GRUPO_0_11: sum(p for i, p in idades.items() if i < IDADE_MINIMA_CHEFE)}
        for ano, idades in populacao.items()
    }


def proporcoes_por_edicao(historicos: Iterable, atuais: Iterable) -> dict[float, dict[str, dict[str, float]]]:
    """Proporção ponderada de cada arranjo por faixa do chefe em 2002,5, 2008,5 e 2017,5.

    A POF 2017 a 2018 não traz a forma de abastecimento: todos os domicílios dela contam como rede geral.
    """
    registros: dict[float, list] = {}
    for d in historicos:
        faixa = faixa_do_chefe(d.idade_chefe)
        if faixa is not None:
            registros.setdefault(ANOS_MEDIOS_POF[d.ano_pof], []).append((faixa.rotulo, d.arranjo, d.peso, d.rede_geral))
    for d in atuais:
        faixa = faixa_do_chefe(d.idade_chefe)
        if faixa is not None:
            registros.setdefault(ANOS_MEDIOS_POF[2017], []).append((faixa.rotulo, d.arranjo, d.peso, True))
    return {t: proporcoes_arranjos(r) for t, r in sorted(registros.items())}


def tendencia_nacional(historicos: Iterable, atuais: Iterable) -> dict[str, tuple[float, float]]:
    """Inclinações nacionais dos logs das razões por faixa (P13), aplicadas a qualquer localidade."""
    return estimar_tendencia(proporcoes_por_edicao(historicos, atuais), ARRANJOS)


@dataclass(frozen=True)
class BaseProjecao:
    """O que a projeção de uma localidade usa e não depende dos controles de simulação (RNF02):
    parâmetros das células medidos na POF e população por faixa e por grupo de idade."""

    celulas: dict
    por_faixa: dict[int, dict[str, int]]
    por_grupo: dict[int, dict[str, int]]
    total: dict[int, int]


def base_da_projecao(domicilios: Iterable, populacao: dict[int, dict[int, int]]) -> BaseProjecao:
    """Sem consumo total ou moradores informados (domicílios montados à mão nos testes),
    vale um morador e o consumo total igual ao per capita."""
    registros = []
    for d in domicilios:
        celula = celula_do_domicilio(d)
        if celula is None:
            continue
        moradores = getattr(d, "moradores", None) or 1
        consumo = getattr(d, "consumo_total_kwh", None)
        consumo = d.consumo_per_capita_kwh * moradores if consumo is None else consumo
        registros.append((celula, d.peso, consumo, d.consumo_per_capita_kwh, moradores))
    return BaseProjecao(
        parametros_celulas(registros), populacao_por_faixa(populacao), populacao_por_grupo(populacao), populacao_total(populacao)
    )


def projecao_da_base(
    base: BaseProjecao,
    tendencia: dict[str, tuple[float, float]] | None = None,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
):
    """A parte que depende dos controles: só monta a Projecao, sem percorrer os domicílios."""
    por_faixa = base.por_faixa
    if k != K_PADRAO and ANO_INICIAL in base.por_grupo:
        ajustada = ajustar_envelhecimento(base.por_grupo, k, ANO_INICIAL)
        por_faixa = {ano: {f: v for f, v in grupos.items() if f != GRUPO_0_11} for ano, grupos in ajustada.items()}
    return Projecao(
        base.celulas,
        por_faixa,
        ANO_REFERENCIA_POF,
        ANO_INICIAL,
        base.total,
        tendencia=tendencia,
        intensidade=intensidade,
        arranjos=ARRANJOS,
        intensidade_ate_base=INTENSIDADE_PADRAO,  # de 2017,5 a 2026 vale sempre o padrão
    )


def montar_projecao(
    domicilios: Iterable,
    populacao: dict[int, dict[int, int]],
    tendencia: dict[str, tuple[float, float]] | None = None,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
):
    """Projeção do método das taxas a partir dos domicílios da POF (com peso) e da população por idade.

    `tendencia` são as inclinações nacionais (P13); sem ela, os arranjos ficam congelados.
    De 2017,5 a 2026 vale sempre a intensidade padrão; `intensidade` só muda a evolução depois de 2026.
    `k` acelera ou freia o envelhecimento a partir de 2026, mantendo a população total do IBGE.
    """
    return projecao_da_base(base_da_projecao(domicilios, populacao), tendencia, intensidade, k)


# ---------- cache do que não depende dos controles (RNF02) ----------


def memorizado(fonte, chave: str, calcular):
    """Guarda `calcular()` no cache da fonte de dados (Dados.derivado); fontes sem cache,
    como as dos testes, calculam na hora."""
    derivado = getattr(fonte, "derivado", None)
    return derivado(chave, calcular) if derivado else calcular()


def tendencia_dos_dados(dados) -> dict[str, tuple[float, float]]:
    """Inclinações nacionais (P13): dependem só das tabelas, então são calculadas uma vez."""
    return memorizado(dados, "tendencia", lambda: tendencia_nacional(dados.domicilios_historicos(), dados.domicilios()))


def domicilios_da_localidade(dados, localidade: str) -> list:
    return memorizado(dados, f"domicilios:{localidade}", lambda: da_localidade(dados.domicilios(), localidade))


def base_da_localidade(dados, localidade: str) -> BaseProjecao | None:
    """Base da projeção da localidade, montada uma vez; None se a localidade não tiver domicílios na POF."""

    def calcular():
        domicilios = domicilios_da_localidade(dados, localidade)
        if not any(celula_do_domicilio(d) for d in domicilios):
            return None
        return base_da_projecao(domicilios, dados.populacao_por_idade(localidade))

    return memorizado(dados, f"base:{localidade}", calcular)


# Total de domicílios estimado pela POF 2017 a 2018 (IBGE): 68,9 milhões (Agência IBGE Notícias, notícia 28903).
# A base cobre os domicílios com kWh declarado (P9); a cobertura é a soma dos pesos dividida por este total.
TOTAL_DOMICILIOS_POF = 68_900_000
