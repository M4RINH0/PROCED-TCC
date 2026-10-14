"""Núcleo metodológico do TCC: equações eq:tec, eq:tbc e eq:tbc-pd, ponte de
domicílios pelas taxas de chefia (premissa P2) e reponderação da amostra.

Funções puras, sem banco nem rede. Toda média usa o peso amostral da POF
(`peso_final`); com peso 1 em todos os domicílios, vira a média simples.

    TEC_x   = soma(peso * consumo per capita) / soma(peso)    faixa x do chefe
    TBC     = a mesma média, sem distinção de faixa
    TBC_pd  = soma_x (TEC_x * nDom_x,s) / soma_x nDom_x,s
    chefia_c       = soma(peso da célula c) / Pop_x,2018      c = (faixa x, arranjo)
    nDom_c,s       = chefia_c * Pop_x,s
    consumo total  = soma_c nDom_c,s * consumo médio por domicílio_c
    calibrado      = consumo por pessoa * população do IBGE no ano (P12)

Tendência dos arranjos (P13): em cada faixa x, log(unipessoal / multipessoal) e
log(casal / multipessoal) variam linearmente no tempo; a taxa de chefia total da
faixa fica constante e só a divisão entre os arranjos muda.
"""

import math
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass


def _validar_razao(consumo: float, domicilios: float) -> None:
    if consumo < 0:
        raise ValueError("o consumo não pode ser negativo")
    if domicilios <= 0:
        raise ValueError("o número de domicílios precisa ser maior que zero")


def tec(cedpercap_x: float, dom_x: float) -> float:
    """Taxa específica de consumo da faixa x: soma ponderada do consumo per capita
    dividida pela soma dos pesos (com peso 1, pela contagem de domicílios)."""
    _validar_razao(cedpercap_x, dom_x)
    return cedpercap_x / dom_x


def tbc(cedpercap: float, dom: float) -> float:
    """Taxa bruta de consumo, sem distinção de idade."""
    _validar_razao(cedpercap, dom)
    return cedpercap / dom


def media_ponderada(valores: Iterable[float], pesos: Iterable[float]) -> float:
    """soma(peso * valor) / soma(peso). Serve para a TEC, a TBC e o consumo médio por domicílio."""
    valores, pesos = list(valores), list(pesos)
    if len(valores) != len(pesos):
        raise ValueError("valores e pesos precisam ter o mesmo tamanho")
    if any(p < 0 for p in pesos):
        raise ValueError("o peso não pode ser negativo")
    total = sum(pesos)
    if total <= 0:
        raise ValueError("a soma dos pesos precisa ser maior que zero")
    return sum(v * p for v, p in zip(valores, pesos)) / total


def tbc_pd(tec_por_faixa: Mapping[Hashable, float], ndom_por_faixa: Mapping[Hashable, float]) -> float:
    """Taxa bruta padronizada pela estrutura de domicílios do cenário s.

    As duas entradas precisam ter exatamente as mesmas chaves (faixas, ou células
    de faixa e arranjo).
    """
    if set(tec_por_faixa) != set(ndom_por_faixa):
        raise ValueError("as faixas de TEC e de domicílios do cenário precisam ser as mesmas")
    if not tec_por_faixa:
        raise ValueError("informe ao menos uma faixa etária")
    if any(v < 0 for v in tec_por_faixa.values()):
        raise ValueError("a TEC não pode ser negativa")
    if any(n < 0 for n in ndom_por_faixa.values()):
        raise ValueError("o número de domicílios não pode ser negativo")
    total = sum(ndom_por_faixa.values())
    if total <= 0:
        raise ValueError("o total de domicílios do cenário precisa ser maior que zero")
    return sum(tec_por_faixa[x] * ndom_por_faixa[x] for x in tec_por_faixa) / total


def taxas_chefia(
    pesos_por_celula: Mapping[tuple[str, str], float], populacao_ref_por_faixa: Mapping[str, float]
) -> dict[tuple[str, str], float]:
    """Premissa P2: domicílios ponderados da célula (faixa, arranjo) / população da faixa no ano de referência."""
    chefia = {}
    for (faixa, arranjo), peso in pesos_por_celula.items():
        if peso < 0:
            raise ValueError("a soma dos pesos não pode ser negativa")
        populacao = populacao_ref_por_faixa.get(faixa, 0)
        if populacao <= 0:
            raise ValueError(f"falta a população da faixa {faixa} no ano de referência")
        chefia[(faixa, arranjo)] = peso / populacao
    return chefia


def domicilios_projetados(
    chefia: Mapping[tuple[str, str], float], populacao_ano_por_faixa: Mapping[str, float]
) -> dict[tuple[str, str], float]:
    """nDom_c,s = taxa de chefia da célula * população da faixa no ano s."""
    if any(p < 0 for p in populacao_ano_por_faixa.values()):
        raise ValueError("a população não pode ser negativa")
    return {celula: taxa * populacao_ano_por_faixa.get(celula[0], 0) for celula, taxa in chefia.items()}


def consumo_total(ndom: Mapping[Hashable, float], consumo_medio_domicilio: Mapping[Hashable, float]) -> float:
    """Domicílios projetados vezes o consumo médio por domicílio de cada célula.

    Nunca população vezes consumo per capita.
    """
    if set(ndom) != set(consumo_medio_domicilio):
        raise ValueError("as células de domicílios e de consumo precisam ser as mesmas")
    if any(n < 0 for n in ndom.values()) or any(c < 0 for c in consumo_medio_domicilio.values()):
        raise ValueError("domicílios e consumo não podem ser negativos")
    return sum(ndom[c] * consumo_medio_domicilio[c] for c in ndom)


def moradores_projetados(ndom: Mapping[Hashable, float], moradores_medios: Mapping[Hashable, float]) -> float:
    """Domicílios projetados vezes a média ponderada de moradores de cada célula."""
    return consumo_total(ndom, moradores_medios)


def consumo_por_pessoa(consumo: float, moradores: float) -> float:
    """Consumo total dividido pelos moradores projetados."""
    _validar_razao(consumo, moradores)
    return consumo / moradores


def reponderar(
    pesos: Iterable[float], celulas: Iterable[Hashable], alvo_por_celula: Mapping[Hashable, float]
) -> list[float]:
    """Ajusta o peso de cada domicílio para que a soma da sua célula seja o alvo:

        peso'_i = peso_i * alvo_c / soma_{j em c} peso_j
    """
    pesos, celulas = list(pesos), list(celulas)
    if len(pesos) != len(celulas):
        raise ValueError("pesos e células precisam ter o mesmo tamanho")
    if any(p < 0 for p in pesos):
        raise ValueError("o peso não pode ser negativo")
    soma: dict[Hashable, float] = {}
    for p, c in zip(pesos, celulas):
        soma[c] = soma.get(c, 0.0) + p
    sem_alvo = set(soma) - set(alvo_por_celula)
    if sem_alvo:
        raise ValueError(f"células sem alvo: {sorted(map(str, sem_alvo))}")
    vazias = [c for c, s in soma.items() if s <= 0 and alvo_por_celula[c] > 0]
    if vazias:
        raise ValueError(f"células com alvo e sem peso na amostra: {sorted(map(str, vazias))}")
    return [p * alvo_por_celula[c] / soma[c] if soma[c] > 0 else 0.0 for p, c in zip(pesos, celulas)]


def fator_calibracao(populacao: float, moradores: float) -> float:
    """Premissa P12: população do IBGE no ano dividida pelos moradores projetados de todas as células.

    É um fator único para todas as células: corrige o nível, mas não a composição.
    """
    if populacao < 0:
        raise ValueError("a população não pode ser negativa")
    if moradores <= 0:
        raise ValueError("os moradores projetados precisam ser maiores que zero")
    return populacao / moradores


# ---------- projeção por células (método das taxas e contrafactual) ----------


@dataclass(frozen=True)
class Celula:
    """Parâmetros de uma célula (faixa do chefe, arranjo) medidos na POF, fixos no horizonte."""

    amostra: int
    peso: float  # domicílios ponderados no ano de referência
    tec: float  # consumo per capita médio ponderado
    consumo_domicilio: float  # consumo médio ponderado por domicílio
    moradores: float  # moradores médios ponderados


def parametros_celulas(registros: Iterable[tuple[Hashable, float, float, float, float]]) -> dict[Hashable, Celula]:
    """Agrupa (célula, peso, consumo do domicílio, consumo per capita, moradores) em médias ponderadas."""
    somas: dict[Hashable, list[float]] = {}
    for chave, peso, consumo, per_capita, moradores in registros:
        if peso <= 0:
            raise ValueError("o peso de cada domicílio precisa ser maior que zero")
        acc = somas.setdefault(chave, [0, 0.0, 0.0, 0.0, 0.0])
        acc[0] += 1
        acc[1] += peso
        acc[2] += peso * per_capita
        acc[3] += peso * consumo
        acc[4] += peso * moradores
    return {c: Celula(int(n), w, sp / w, sc / w, sm / w) for c, (n, w, sp, sc, sm) in somas.items()}


@dataclass(frozen=True)
class Resumo:
    domicilios: float
    moradores: float
    consumo_total: float  # bruto: diagnóstico, fora da API
    tbc_padronizada: float
    consumo_por_pessoa: float
    consumo_total_calibrado: float | None  # None sem população total do ano


TAXAS = "taxas"
TAXAS_ARRANJOS_FIXOS = "taxas_arranjos_fixos"
CONTRAFACTUAL = "contrafactual"
CENARIOS = (TAXAS, TAXAS_ARRANJOS_FIXOS, CONTRAFACTUAL)
ANO_MEDIO_POF = 2017.5  # ponto médio da POF 2017 a 2018, âncora da tendência (P13)


class Projecao:
    """Ponte comum (P2 e P13) e cenários do método das taxas.

    chefia_x                = soma dos pesos da faixa x / Pop_x,2018         (constante)
    proporção_x,a(s)        = proporção observada em 2017,5 movida pela tendência (P13)
    taxas:                  nDom_x,a,s = chefia_x * Pop_x,s * proporção_x,a(s)
    taxas_arranjos_fixos:   o mesmo, com as proporções de arranjo do ano-base (2026)
    contrafactual:          o total de domicílios do ano segue a projeção, e a distribuição
                            entre as células fica congelada na de taxas no ano-base (P10)

    Sem tendência, ou com intensidade 0, as proporções ficam nas de 2017,5 e os três
    cenários coincidem no ano-base: é o modelo anterior, com os arranjos congelados.
    `arranjos` diz quais rótulos são (unipessoal, casal ou dupla, multipessoal).
    """

    def __init__(
        self,
        celulas: Mapping[tuple[str, str], Celula],
        populacao_por_faixa: Mapping[int, Mapping[str, float]],
        ano_referencia: int,
        ano_base: int,
        populacao_total: Mapping[int, float] | None = None,
        tendencia: Mapping[str, tuple[float, float]] | None = None,
        intensidade: float = 1.0,
        arranjos: tuple[str, str, str] | None = None,
        ano_tendencia: float = ANO_MEDIO_POF,
    ):
        if ano_referencia not in populacao_por_faixa:
            raise ValueError(f"falta a população de {ano_referencia}, ano de referência")
        if not celulas:
            raise ValueError("informe ao menos uma célula")
        if intensidade < 0:
            raise ValueError("a intensidade da tendência não pode ser negativa")
        if tendencia and arranjos is None:
            raise ValueError("informe os rótulos dos arranjos para aplicar a tendência")
        self.celulas = dict(celulas)
        self.populacao_por_faixa = populacao_por_faixa
        self.populacao_total = populacao_total or {}
        self.ano_base = ano_base
        self.tendencia = dict(tendencia or {})
        self.intensidade = intensidade
        self.arranjos = arranjos
        self.ano_tendencia = ano_tendencia
        self.chefia = taxas_chefia({c: p.peso for c, p in self.celulas.items()}, populacao_por_faixa[ano_referencia])
        pesos_faixa: dict[str, float] = {}
        for (faixa, _), p in self.celulas.items():
            pesos_faixa[faixa] = pesos_faixa.get(faixa, 0.0) + p.peso
        # a taxa de chefia total da faixa fica constante; só a divisão entre os arranjos muda (P13)
        self.chefia_faixa = {f: c for (f, _), c in taxas_chefia({(f, ""): w for f, w in pesos_faixa.items()}, populacao_por_faixa[ano_referencia]).items()}
        self.proporcoes_base = {
            f: {a: p.peso / pesos_faixa[f] for (g, a), p in self.celulas.items() if g == f} for f in pesos_faixa
        }

    @property
    def com_tendencia(self) -> bool:
        return bool(self.tendencia) and self.intensidade > 0

    def proporcoes(self, ano: float) -> dict[str, dict[str, float]]:
        """Proporção de cada arranjo em cada faixa no ano (P13)."""
        if not self.com_tendencia:
            return {f: dict(p) for f, p in self.proporcoes_base.items()}
        return {
            f: projetar_proporcoes(p, self.tendencia.get(f), ano - self.ano_tendencia, self.intensidade, self.arranjos)
            for f, p in self.proporcoes_base.items()
        }

    def _com_proporcoes(self, ano: int, proporcoes: Mapping[str, Mapping[str, float]]) -> dict[tuple[str, str], float]:
        populacao = self.populacao_por_faixa[ano]
        return {
            (f, a): self.chefia_faixa[f] * populacao.get(f, 0) * proporcoes[f].get(a, 0.0) for (f, a) in self.celulas
        }

    def domicilios(self, ano: int, cenario: str = TAXAS) -> dict[tuple[str, str], float]:
        if ano not in self.populacao_por_faixa:
            raise KeyError(ano)
        if cenario == TAXAS:
            if not self.com_tendencia:
                return domicilios_projetados(self.chefia, self.populacao_por_faixa[ano])
            return self._com_proporcoes(ano, self.proporcoes(ano))
        if cenario == TAXAS_ARRANJOS_FIXOS:
            if not self.com_tendencia:
                return self.domicilios(ano, TAXAS)
            return self._com_proporcoes(ano, self.proporcoes(self.ano_base))
        if cenario == CONTRAFACTUAL:
            total = sum(self.domicilios(ano, TAXAS).values())
            return congelar_composicao(self.domicilios(self.ano_base, TAXAS), total)
        raise ValueError(f"cenário desconhecido: {cenario}")

    def resumo(self, ano: int, cenario: str = TAXAS, chaves: Iterable[tuple[str, str]] | None = None) -> Resumo | None:
        """Indicadores do ano no conjunto de células `chaves` (todas, se None); None se ele não tiver domicílios.

        O fator de calibração usa os moradores de todas as células, para o recorte
        somar exatamente o total calibrado do país.
        """
        todos = self.domicilios(ano, cenario)
        sub = {c: todos[c] for c in (self.celulas if chaves is None else chaves) if c in todos}
        if sum(sub.values()) <= 0:
            return None
        consumo = consumo_total(sub, {c: self.celulas[c].consumo_domicilio for c in sub})
        moradores = moradores_projetados(sub, {c: self.celulas[c].moradores for c in sub})
        por_pessoa = consumo_por_pessoa(consumo, moradores)
        calibrado = None
        if ano in self.populacao_total:
            moradores_todos = moradores_projetados(todos, {c: self.celulas[c].moradores for c in todos})
            calibrado = consumo * fator_calibracao(self.populacao_total[ano], moradores_todos)
        return Resumo(
            domicilios=sum(sub.values()),
            moradores=moradores,
            consumo_total=consumo,
            tbc_padronizada=tbc_pd({c: self.celulas[c].tec for c in sub}, sub),
            consumo_por_pessoa=por_pessoa,
            consumo_total_calibrado=calibrado,
        )


def congelar_composicao(base: Mapping[Hashable, float], total: float) -> dict[Hashable, float]:
    """Distribui `total` entre as células na proporção de `base` (contrafactual, P10)."""
    soma = sum(base.values())
    if soma <= 0:
        raise ValueError("a composição de base precisa ter domicílios")
    if total < 0:
        raise ValueError("o total de domicílios não pode ser negativo")
    return {c: n / soma * total for c, n in base.items()}


# ---------- tendência dos arranjos (P13) ----------


def proporcoes_arranjos(registros: Iterable[tuple[Hashable, str, float, bool]]) -> dict[Hashable, dict[str, float]]:
    """Proporção ponderada de cada arranjo em cada faixa, a partir de (faixa, arranjo, peso, rede geral).

    Domicílios fora da rede geral de energia ficam de fora (P13).
    """
    somas: dict[Hashable, dict[str, float]] = {}
    for faixa, arranjo, peso, rede_geral in registros:
        if peso <= 0:
            raise ValueError("o peso de cada domicílio precisa ser maior que zero")
        if not rede_geral:
            continue
        acc = somas.setdefault(faixa, {})
        acc[arranjo] = acc.get(arranjo, 0.0) + peso
    return {f: {a: w / sum(acc.values()) for a, w in acc.items()} for f, acc in somas.items()}


def logs_razoes(proporcoes: Mapping[str, float], arranjos: tuple[str, str, str]) -> tuple[float, float] | None:
    """(log(unipessoal / multipessoal), log(casal / multipessoal)); None se algum arranjo tiver proporção zero."""
    uni, casal, multi = (proporcoes.get(a, 0.0) for a in arranjos)
    if min(uni, casal, multi) <= 0:
        return None
    return math.log(uni / multi), math.log(casal / multi)


def proporcoes_dos_logs(log_uni: float, log_casal: float, arranjos: tuple[str, str, str]) -> dict[str, float]:
    """Inverte os logs das razões: as proporções ficam entre 0 e 1 e somam 1."""
    u, c = math.exp(log_uni), math.exp(log_casal)
    total = 1 + u + c
    return {arranjos[0]: u / total, arranjos[1]: c / total, arranjos[2]: 1 / total}


def inclinacao(pontos: Iterable[tuple[float, float]]) -> float:
    """Inclinação da reta de mínimos quadrados nos pontos (tempo, valor)."""
    pontos = list(pontos)
    if len({t for t, _ in pontos}) < 2:
        raise ValueError("a reta precisa de ao menos dois anos diferentes")
    mt = sum(t for t, _ in pontos) / len(pontos)
    my = sum(y for _, y in pontos) / len(pontos)
    return sum((t - mt) * (y - my) for t, y in pontos) / sum((t - mt) ** 2 for t, _ in pontos)


def estimar_tendencia(
    proporcoes_por_ano: Mapping[float, Mapping[Hashable, Mapping[str, float]]], arranjos: tuple[str, str, str]
) -> dict[Hashable, tuple[float, float]]:
    """Inclinações (por ano) dos dois logs das razões em cada faixa, ajustadas nas edições disponíveis.

    Faixa sem os três arranjos em ao menos duas edições fica sem tendência.
    """
    faixas = {f for props in proporcoes_por_ano.values() for f in props}
    tendencia = {}
    for faixa in faixas:
        pontos = [(t, logs_razoes(props[faixa], arranjos)) for t, props in proporcoes_por_ano.items() if faixa in props]
        pontos = [(t, l) for t, l in pontos if l is not None]
        if len({t for t, _ in pontos}) < 2:
            continue
        tendencia[faixa] = (inclinacao((t, l[0]) for t, l in pontos), inclinacao((t, l[1]) for t, l in pontos))
    return tendencia


def projetar_proporcoes(
    base: Mapping[str, float],
    inclinacoes: tuple[float, float] | None,
    anos: float,
    intensidade: float,
    arranjos: tuple[str, str, str],
) -> dict[str, float]:
    """Proporções `anos` depois da base: log razão = log razão da base + intensidade * inclinação * anos.

    Sem inclinação, ou com algum arranjo zerado na base, as proporções ficam as da base.
    """
    logs = logs_razoes(base, arranjos)
    if inclinacoes is None or logs is None:
        return dict(base)
    return proporcoes_dos_logs(
        logs[0] + intensidade * inclinacoes[0] * anos, logs[1] + intensidade * inclinacoes[1] * anos, arranjos
    )


def validar_tendencia(
    proporcoes_por_ano: Mapping[float, Mapping[Hashable, Mapping[str, float]]],
    arranjos: tuple[str, str, str],
    treino: tuple[float, float],
    alvo: float,
) -> dict[Hashable, dict[str, float]]:
    """Validação fora do tempo: inclinação estimada só nos anos de `treino`, ancorada no último deles,
    prevendo `alvo`. Devolve o erro (previsto menos observado) em pontos percentuais por faixa e arranjo."""
    tendencia = estimar_tendencia({t: proporcoes_por_ano[t] for t in treino}, arranjos)
    ancora = max(treino)
    erros = {}
    for faixa, inclinacoes in tendencia.items():
        if faixa not in proporcoes_por_ano[alvo]:
            continue
        previsto = projetar_proporcoes(proporcoes_por_ano[ancora][faixa], inclinacoes, alvo - ancora, 1.0, arranjos)
        observado = proporcoes_por_ano[alvo][faixa]
        erros[faixa] = {a: (previsto[a] - observado.get(a, 0.0)) * 100 for a in arranjos}
    return erros


# ---------- velocidade do envelhecimento (RF02) ----------


def ajustar_envelhecimento(
    populacao_por_grupo: Mapping[int, Mapping[str, float]], k: float, ano_base: int
) -> dict[int, dict[str, float]]:
    """Participação do grupo g no ano s: part_g(base) + k * (part_g(s) - part_g(base)), com piso em zero,
    renormalizada e aplicada à população total do ano. Os grupos precisam cobrir todas as idades.

    Anos anteriores ao ano-base ficam como estão; k = 1 devolve a população original.
    """
    if k <= 0:
        raise ValueError("a velocidade do envelhecimento precisa ser maior que zero")
    if ano_base not in populacao_por_grupo:
        raise ValueError(f"falta a população de {ano_base}")
    base = populacao_por_grupo[ano_base]
    total_base = sum(base.values())
    if total_base <= 0:
        raise ValueError("a população do ano-base precisa ser maior que zero")
    part_base = {g: p / total_base for g, p in base.items()}
    resultado = {}
    for ano, grupos in populacao_por_grupo.items():
        total = sum(grupos.values())
        if ano < ano_base or k == 1 or total <= 0:
            resultado[ano] = dict(grupos)
            continue
        brutas = {g: max(0.0, part_base.get(g, 0.0) + k * (p / total - part_base.get(g, 0.0))) for g, p in grupos.items()}
        soma = sum(brutas.values())
        resultado[ano] = {g: v / soma * total for g, v in brutas.items()}
    return resultado
