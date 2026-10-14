"""Regras do Panorama (RF01, RF02, RF11).

Cenários do método das taxas, todos com a TBC padronizada (eq:tbc-pd) e a TEC
ponderada de cada célula (faixa do chefe, arranjo) medida na POF 2017 a 2018:

- taxas: estrutura etária do IBGE e tendência dos arranjos (P2 e P13);
- taxas_arranjos_fixos: só o envelhecimento, com os arranjos congelados em 2026;
- contrafactual: a distribuição dos domicílios entre as células congelada na de 2026 (P10).

Decomposição: efeito da idade = taxas_arranjos_fixos menos contrafactual; efeito
dos arranjos = taxas menos taxas_arranjos_fixos; os dois somam o efeito do
envelhecimento (taxas menos contrafactual). O consumo total é calibrado pela
população do IBGE (P12).

Controles de simulação (RF02): intensidade da tendência dos arranjos e velocidade
do envelhecimento k. Os padrões (1 e 1) reproduzem o cenário principal.

Os cenários de machine learning (ml_rf e ml_gb) estão pausados e saem como null.
"""

from collections.abc import Iterable

from app.calculo import CONTRAFACTUAL, TAXAS, TAXAS_ARRANJOS_FIXOS, Resumo
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    BRASIL,
    CELULAS_DO_RECORTE,
    FAIXAS_CHEFE,
    FAIXAS_DO_RECORTE,
    IDADE_IDOSO,
    INTENSIDADE_PADRAO,
    K_PADRAO,
    Recorte,
    baixa_confiabilidade,
    celula_do_domicilio,
    em_simulacao,
    BaseProjecao,
    base_da_localidade,
    base_da_projecao,
    projecao_da_base,
    tendencia_dos_dados,
)
from app.schemas.panorama import (
    Amostra,
    Cenario,
    CelulaAmostra,
    CenarioId,
    Efeitos,
    PontoSerie,
    ProjecaoResposta,
    SerieResposta,
    Simulacao,
)

FAIXAS_60 = {f.rotulo for f in FAIXAS_CHEFE if f.minima >= IDADE_IDOSO}


class ParametrosRecorte:
    """Projeção do método das taxas, com os parâmetros das células fixados no ano de referência da POF."""

    def __init__(
        self,
        recorte: Recorte,
        domicilios: Iterable[Domicilio],
        populacao: dict[int, dict[int, int]],
        tendencia: dict[str, tuple[float, float]] | None = None,
        intensidade: float = INTENSIDADE_PADRAO,
        k: float = K_PADRAO,
        base: BaseProjecao | None = None,
    ):
        """`base` vem do cache da localidade (RNF02); sem ela, é montada a partir dos domicílios."""
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        if base is None:
            lista = list(domicilios)
            base = base_da_projecao(lista, populacao) if any(celula_do_domicilio(d) for d in lista) else None
        self.populacao = populacao
        self.celulas = CELULAS_DO_RECORTE[recorte]
        amostra = {c: p.amostra for c, p in base.celulas.items()} if base else {}
        self.amostra_celulas = {c: amostra.get(c, 0) for c in self.celulas}
        self.amostra = sum(self.amostra_celulas.values())
        # sem domicílio da amostra numa faixa do recorte, a padronização não fecha e o valor fica nulo
        self.completo = all(
            any(self.amostra_celulas[(f.rotulo, a)] for a in {c[1] for c in self.celulas})
            for f in FAIXAS_DO_RECORTE[recorte]
        )
        self.projecao = projecao_da_base(base, tendencia, intensidade, k) if base else None

    def resumo(self, ano: int, cenario: str = TAXAS) -> Resumo | None:
        if not self.completo or self.projecao is None or ano not in self.populacao:
            return None
        if cenario == CONTRAFACTUAL and self.projecao.ano_base not in self.populacao:
            return None
        return self.projecao.resumo(ano, cenario, self.celulas)

    def participacao_60_mais(self, ano: int) -> float | None:
        """Pessoas de 60 anos ou mais na população do ano, já com o controle k aplicado."""
        if ano not in self.populacao:
            return None
        if self.projecao is None:
            return participacao_60_mais(self.populacao[ano])
        total = self.projecao.populacao_total.get(ano, 0)
        if total <= 0:
            return None
        idosos = sum(p for f, p in self.projecao.populacao_por_faixa[ano].items() if f in FAIXAS_60)
        return round(idosos / total * 100, 2)

    def amostra_resposta(self) -> Amostra:
        celulas = [
            CelulaAmostra(faixa=f, arranjo=a, domicilios_amostra=n, baixa_confiabilidade=baixa_confiabilidade(n))
            for (f, a), n in self.amostra_celulas.items()
        ]
        return Amostra(
            domicilios_amostra=self.amostra,
            celulas=celulas,
            baixa_confiabilidade=any(c.baixa_confiabilidade for c in celulas),
        )


def _validar_ano(ano: int) -> None:
    if not ANO_INICIAL <= ano <= ANO_FINAL:
        raise ValueError(f"o ano precisa estar entre {ANO_INICIAL} e {ANO_FINAL}")


def _cenario(id_: CenarioId, resumo: Resumo | None) -> Cenario:
    if resumo is None:
        return Cenario(id=id_, valor=None)
    calibrado = resumo.consumo_total_calibrado
    return Cenario(
        id=id_,
        valor=round(resumo.tbc_padronizada, 1),
        consumo_por_pessoa_kwh=round(resumo.consumo_por_pessoa, 1),
        consumo_total_calibrado_kwh_mes=None if calibrado is None else round(calibrado),
    )


def _cenarios(parametros: ParametrosRecorte, ano: int) -> list[Cenario]:
    return [
        _cenario(CenarioId.taxas, parametros.resumo(ano, TAXAS)),
        _cenario(CenarioId.taxas_arranjos_fixos, parametros.resumo(ano, TAXAS_ARRANJOS_FIXOS)),
        Cenario(id=CenarioId.ml_rf, valor=None),
        Cenario(id=CenarioId.ml_gb, valor=None),
        _cenario(CenarioId.contrafactual, parametros.resumo(ano, CONTRAFACTUAL)),
    ]


def _diferenca(a: float | None, b: float | None, casas: int | None) -> float | None:
    if a is None or b is None:
        return None
    return round(a - b, casas) if casas is not None else round(a - b)


def efeitos(cenarios: list[Cenario]) -> Efeitos:
    """Decomposição do efeito do envelhecimento em idade e arranjos, na TBC e no consumo total."""
    por_id = {c.id: c for c in cenarios}
    t, f, c = (por_id.get(i) for i in (CenarioId.taxas, CenarioId.taxas_arranjos_fixos, CenarioId.contrafactual))

    def valor(x: Cenario | None) -> float | None:
        return None if x is None else x.valor

    def total(x: Cenario | None) -> float | None:
        return None if x is None else x.consumo_total_calibrado_kwh_mes

    return Efeitos(
        efeito_envelhecimento_kwh=_diferenca(valor(t), valor(c), 1),
        efeito_idade_kwh=_diferenca(valor(f), valor(c), 1),
        efeito_arranjos_kwh=_diferenca(valor(t), valor(f), 1),
        efeito_envelhecimento_total_kwh_mes=_diferenca(total(t), total(c), None),
        efeito_idade_total_kwh_mes=_diferenca(total(f), total(c), None),
        efeito_arranjos_total_kwh_mes=_diferenca(total(t), total(f), None),
    )


def _parametros(recorte: Recorte, dados, localidade: str, intensidade: float, k: float) -> ParametrosRecorte:
    # base da localidade e inclinações nacionais (P13) vêm do cache; só a projeção depende dos controles
    base = base_da_localidade(dados, localidade)
    return ParametrosRecorte(
        recorte, (), dados.populacao_por_idade(localidade), tendencia_dos_dados(dados), intensidade, k, base=base
    )


def _simulacao(intensidade: float, k: float) -> Simulacao:
    return Simulacao(intensidade=intensidade, k=k, simulacao=em_simulacao(intensidade, k))


def obter_projecao(
    ano: int, recorte: Recorte, dados, localidade: str = BRASIL, intensidade: float = INTENSIDADE_PADRAO, k: float = K_PADRAO
) -> ProjecaoResposta:
    _validar_ano(ano)
    parametros = _parametros(recorte, dados, localidade, intensidade, k)
    cenarios = _cenarios(parametros, ano)
    return ProjecaoResposta(
        ano=ano,
        recorte=recorte,
        cenarios=cenarios,
        dados_ilustrativos=False,
        localidade=localidade,
        **efeitos(cenarios).model_dump(),
        **parametros.amostra_resposta().model_dump(),
        **_simulacao(intensidade, k).model_dump(),
    )


def participacao_60_mais(populacao_do_ano: dict[int, int]) -> float | None:
    total = sum(populacao_do_ano.values())
    if total <= 0:
        return None
    return round(sum(p for idade, p in populacao_do_ano.items() if idade >= IDADE_IDOSO) / total * 100, 2)


def com_variacao(cenarios: list[Cenario], base: list[Cenario]) -> list[Cenario]:
    """Acrescenta a variação de cada cenário em relação aos valores de 2026."""
    inicial = {c.id: c.valor for c in base}
    resultado = []
    for c in cenarios:
        b = inicial.get(c.id)
        if c.valor is None or b is None or b == 0:
            resultado.append(c)
            continue
        resultado.append(
            c.model_copy(update={"variacao_kwh": round(c.valor - b, 1), "variacao_pct": round((c.valor / b - 1) * 100, 1)})
        )
    return resultado


def _ponto(parametros: ParametrosRecorte, ano: int, base: list[Cenario]) -> PontoSerie:
    cenarios = com_variacao(_cenarios(parametros, ano), base)
    return PontoSerie(
        ano=ano,
        cenarios=cenarios,
        participacao_60_mais_pct=parametros.participacao_60_mais(ano),
        **efeitos(cenarios).model_dump(),
    )


def obter_serie(
    recorte: Recorte, dados, localidade: str = BRASIL, intensidade: float = INTENSIDADE_PADRAO, k: float = K_PADRAO
) -> SerieResposta:
    parametros = _parametros(recorte, dados, localidade, intensidade, k)
    base = _cenarios(parametros, ANO_INICIAL)
    pontos = [_ponto(parametros, a, base) for a in range(ANO_INICIAL, ANO_FINAL + 1)]
    return SerieResposta(
        recorte=recorte,
        pontos=pontos,
        dados_ilustrativos=False,
        localidade=localidade,
        **parametros.amostra_resposta().model_dump(),
        **_simulacao(intensidade, k).model_dump(),
    )
