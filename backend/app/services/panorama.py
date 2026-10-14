"""Regras do Panorama (RF01, RF11).

Cenário taxas (método das taxas): TBC padronizada (eq:tbc-pd) com a TEC ponderada
de cada célula (faixa do chefe, arranjo) medida na POF e a estrutura de domicílios
do ano s estimada pela projeção populacional do IBGE com taxa de chefia constante
(premissa P2):

    TEC_c    = soma(peso * consumo per capita) / soma(peso)
    nDom_c,s = (soma dos pesos da célula c / Pop_x,2018) * Pop_x,s

Cenário contrafactual: o mesmo cálculo com a distribuição dos domicílios entre as
células congelada na de 2026 (P10). A diferença entre os dois é o efeito do
envelhecimento. O consumo total é calibrado pela população do IBGE (P12).

Os cenários de machine learning (ml_rf e ml_gb) estão pausados e saem como null.
"""

from collections.abc import Iterable

from app.calculo import CONTRAFACTUAL, TAXAS, Resumo
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    BRASIL,
    CELULAS_DO_RECORTE,
    FAIXAS_DO_RECORTE,
    IDADE_IDOSO,
    Recorte,
    baixa_confiabilidade,
    celula_do_domicilio,
    da_localidade,
    montar_projecao,
)
from app.schemas.panorama import Amostra, Cenario, CelulaAmostra, CenarioId, PontoSerie, ProjecaoResposta, SerieResposta


class ParametrosRecorte:
    """Projeção do método das taxas, com os parâmetros das células fixados no ano de referência da POF."""

    def __init__(self, recorte: Recorte, domicilios: Iterable[Domicilio], populacao: dict[int, dict[int, int]]):
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        lista = list(domicilios)
        self.populacao = populacao
        self.celulas = CELULAS_DO_RECORTE[recorte]
        contagem: dict[tuple[str, str], int] = {}
        for d in lista:
            celula = celula_do_domicilio(d)
            if celula in self.celulas:
                contagem[celula] = contagem.get(celula, 0) + 1
        self.amostra_celulas = {c: contagem.get(c, 0) for c in self.celulas}
        self.amostra = sum(self.amostra_celulas.values())
        # sem domicílio da amostra numa faixa do recorte, a padronização não fecha e o valor fica nulo
        self.completo = all(
            any(self.amostra_celulas[(f.rotulo, a)] for a in {c[1] for c in self.celulas})
            for f in FAIXAS_DO_RECORTE[recorte]
        )
        self.projecao = montar_projecao(lista, populacao) if lista else None

    def resumo(self, ano: int, cenario: str = TAXAS) -> Resumo | None:
        if not self.completo or self.projecao is None or ano not in self.populacao:
            return None
        if cenario == CONTRAFACTUAL and self.projecao.ano_base not in self.populacao:
            return None
        return self.projecao.resumo(ano, cenario, self.celulas)

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
        Cenario(id=CenarioId.ml_rf, valor=None),
        Cenario(id=CenarioId.ml_gb, valor=None),
        _cenario(CenarioId.contrafactual, parametros.resumo(ano, CONTRAFACTUAL)),
    ]


def efeito_envelhecimento(cenarios: list[Cenario]) -> tuple[float | None, float | None]:
    """taxas menos contrafactual, na TBC padronizada e no consumo total calibrado."""
    por_id = {c.id: c for c in cenarios}
    t, c = por_id.get(CenarioId.taxas), por_id.get(CenarioId.contrafactual)
    if t is None or c is None:
        return None, None
    tbc = None if t.valor is None or c.valor is None else round(t.valor - c.valor, 1)
    total = (
        None
        if t.consumo_total_calibrado_kwh_mes is None or c.consumo_total_calibrado_kwh_mes is None
        else round(t.consumo_total_calibrado_kwh_mes - c.consumo_total_calibrado_kwh_mes)
    )
    return tbc, total


def _parametros(recorte: Recorte, dados, localidade: str) -> ParametrosRecorte:
    domicilios = da_localidade(dados.domicilios(), localidade)
    return ParametrosRecorte(recorte, domicilios, dados.populacao_por_idade(localidade))


def obter_projecao(ano: int, recorte: Recorte, dados, localidade: str = BRASIL) -> ProjecaoResposta:
    _validar_ano(ano)
    parametros = _parametros(recorte, dados, localidade)
    cenarios = _cenarios(parametros, ano)
    efeito, efeito_total = efeito_envelhecimento(cenarios)
    return ProjecaoResposta(
        ano=ano,
        recorte=recorte,
        cenarios=cenarios,
        efeito_envelhecimento_kwh=efeito,
        efeito_envelhecimento_total_kwh_mes=efeito_total,
        dados_ilustrativos=False,
        localidade=localidade,
        **parametros.amostra_resposta().model_dump(),
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


def _ponto(parametros: ParametrosRecorte, ano: int, base: list[Cenario], populacao: dict[int, dict[int, int]]) -> PontoSerie:
    cenarios = com_variacao(_cenarios(parametros, ano), base)
    efeito, efeito_total = efeito_envelhecimento(cenarios)
    return PontoSerie(
        ano=ano,
        cenarios=cenarios,
        participacao_60_mais_pct=participacao_60_mais(populacao[ano]) if ano in populacao else None,
        efeito_envelhecimento_kwh=efeito,
        efeito_envelhecimento_total_kwh_mes=efeito_total,
    )


def obter_serie(recorte: Recorte, dados, localidade: str = BRASIL) -> SerieResposta:
    parametros = _parametros(recorte, dados, localidade)
    populacao = dados.populacao_por_idade(localidade)
    base = _cenarios(parametros, ANO_INICIAL)
    pontos = [_ponto(parametros, a, base, populacao) for a in range(ANO_INICIAL, ANO_FINAL + 1)]
    return SerieResposta(
        recorte=recorte,
        pontos=pontos,
        dados_ilustrativos=False,
        localidade=localidade,
        **parametros.amostra_resposta().model_dump(),
    )
