"""Regras do Panorama (RF01, RF11).

Cenário ibge (método das taxas, que será renomeado para taxas): TBC padronizada
(eq:tbc-pd) com a TEC ponderada de cada faixa do chefe medida na POF e a
estrutura de domicílios do ano s estimada pela projeção populacional do IBGE com
taxa de chefia constante (docs/premissas.md):

    TEC_x    = soma(peso * consumo per capita) / soma(peso)
    nDom_x,s = (soma dos pesos da faixa x / Pop_x,2018) * Pop_x,s

Os cenários do modelo (mod) e alternativo (alt) ainda não têm formulação
definida no TCC e saem como null.
"""

from collections.abc import Iterable

from app.calculo import tbc_pd, tec
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    BRASIL,
    FAIXAS_DO_RECORTE,
    IDADE_IDOSO,
    FiltroArranjo,
    Recorte,
    da_faixa,
    da_localidade,
    filtrar,
    populacao_da_faixa,
)
from app.schemas.panorama import Cenario, CenarioId, PontoSerie, ProjecaoResposta, SerieResposta


class ParametrosRecorte:
    """TEC e taxa de chefia por faixa, ponderadas por peso_final e fixadas no ano de referência da POF."""

    def __init__(self, recorte: Recorte, domicilios: Iterable[Domicilio], populacao: dict[int, dict[int, int]]):
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        mononucleares = filtrar(domicilios, FiltroArranjo.mononucleares)
        self.faixas = FAIXAS_DO_RECORTE[recorte]
        self.populacao = populacao
        self.tec: dict[str, float] = {}
        self.chefia: dict[str, float] = {}
        self.amostra = 0
        self.completo = True  # False se alguma faixa do recorte não tem domicílio na amostra
        for faixa in self.faixas:
            grupo = da_faixa(mononucleares, faixa)
            self.amostra += len(grupo)
            if not grupo:
                self.completo = False
                continue
            peso = sum(d.peso for d in grupo)
            self.tec[faixa.rotulo] = tec(sum(d.peso * d.consumo_per_capita_kwh for d in grupo), peso)
            self.chefia[faixa.rotulo] = peso / populacao_da_faixa(populacao[ANO_REFERENCIA_POF], faixa)

    def tbc_ibge(self, ano: int) -> float | None:
        if not self.completo or ano not in self.populacao:
            return None
        ndom = {
            f.rotulo: self.chefia[f.rotulo] * populacao_da_faixa(self.populacao[ano], f) for f in self.faixas
        }
        return tbc_pd(self.tec, ndom)


def _validar_ano(ano: int) -> None:
    if not ANO_INICIAL <= ano <= ANO_FINAL:
        raise ValueError(f"o ano precisa estar entre {ANO_INICIAL} e {ANO_FINAL}")


def _cenarios(parametros: ParametrosRecorte, ano: int) -> list[Cenario]:
    ibge = parametros.tbc_ibge(ano)
    return [
        Cenario(id=CenarioId.mod, valor=None),
        Cenario(id=CenarioId.ibge, valor=None if ibge is None else round(ibge, 1)),
        Cenario(id=CenarioId.alt, valor=None),
    ]


def _parametros(recorte: Recorte, dados, localidade: str) -> ParametrosRecorte:
    domicilios = da_localidade(dados.domicilios(), localidade)
    return ParametrosRecorte(recorte, domicilios, dados.populacao_por_idade(localidade))


def obter_projecao(ano: int, recorte: Recorte, dados, localidade: str = BRASIL) -> ProjecaoResposta:
    _validar_ano(ano)
    parametros = _parametros(recorte, dados, localidade)
    return ProjecaoResposta(
        ano=ano,
        recorte=recorte,
        cenarios=_cenarios(parametros, ano),
        dados_ilustrativos=False,
        localidade=localidade,
        domicilios_amostra=parametros.amostra,
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


def comparativos(cenarios: list[Cenario]) -> tuple[float | None, float | None]:
    """Amplitude entre os cenários com dado e a diferença do modelo para o oficial."""
    valores = {c.id: c.valor for c in cenarios if c.valor is not None}
    amplitude = round(max(valores.values()) - min(valores.values()), 1) if len(valores) > 1 else None
    diferenca = (
        round(valores[CenarioId.mod] - valores[CenarioId.ibge], 1)
        if CenarioId.mod in valores and CenarioId.ibge in valores
        else None
    )
    return amplitude, diferenca


def _ponto(parametros: ParametrosRecorte, ano: int, base: list[Cenario], populacao: dict[int, dict[int, int]]) -> PontoSerie:
    cenarios = com_variacao(_cenarios(parametros, ano), base)
    amplitude, diferenca = comparativos(cenarios)
    return PontoSerie(
        ano=ano,
        cenarios=cenarios,
        participacao_60_mais_pct=participacao_60_mais(populacao[ano]) if ano in populacao else None,
        amplitude_kwh=amplitude,
        modelo_menos_oficial_kwh=diferenca,
    )


def obter_serie(recorte: Recorte, dados, localidade: str = BRASIL) -> SerieResposta:
    parametros = _parametros(recorte, dados, localidade)
    populacao = dados.populacao_por_idade(localidade)
    base = _cenarios(parametros, ANO_INICIAL)
    pontos = [_ponto(parametros, a, base, populacao) for a in range(ANO_INICIAL, ANO_FINAL + 1)]
    return SerieResposta(
        recorte=recorte, pontos=pontos, dados_ilustrativos=False, localidade=localidade, domicilios_amostra=parametros.amostra
    )
