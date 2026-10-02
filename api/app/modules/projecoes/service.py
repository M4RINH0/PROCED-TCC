"""Regras da projeção (RF01, RF11).

Cenário oficial (ibge): TBC padronizada (eq:tbc-pd) com a TEC de cada faixa do
chefe medida na POF e a estrutura de domicílios do ano s estimada pela
projeção populacional do IBGE com taxa de chefia constante (docs/premissas.md):

    nDom_x,s = (domicílios da amostra na faixa x / Pop_x,2018) * Pop_x,s

Os cenários do modelo (mod) e alternativo (alt) ainda não têm formulação
definida no TCC e saem como null.
"""

from collections.abc import Iterable

from app.modules.projecoes.calculo import tbc_pd, tec
from app.modules.projecoes.faixas import ARRANJOS_DO_FILTRO, FAIXAS_CHEFE, FAIXAS_DO_RECORTE, Faixa
from app.modules.projecoes.repository import Domicilio, RepositorioProjecoes
from app.modules.projecoes.schemas import (
    ANO_FINAL,
    ANO_FINAL_IBGE,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    Cenario,
    CenarioId,
    FaixaConsumo,
    FiltroArranjo,
    PontoSerie,
    ProjecaoResposta,
    Recorte,
    SerieResposta,
)


def filtrar(domicilios: Iterable[Domicilio], filtro: FiltroArranjo) -> list[Domicilio]:
    arranjos = ARRANJOS_DO_FILTRO[filtro]
    return [d for d in domicilios if d.arranjo in arranjos]


def _da_faixa(domicilios: Iterable[Domicilio], faixa: Faixa) -> list[Domicilio]:
    return [d for d in domicilios if faixa.contem(d.idade_chefe)]


def consumo_por_faixa(domicilios: Iterable[Domicilio], filtro: FiltroArranjo) -> list[FaixaConsumo]:
    """TEC por faixa etária do chefe (RF05, RF06)."""
    selecionados = filtrar(domicilios, filtro)
    resultado = []
    for faixa in FAIXAS_CHEFE:
        grupo = _da_faixa(selecionados, faixa)
        valor = tec(sum(d.consumo_per_capita_kwh for d in grupo), len(grupo)) if grupo else None
        resultado.append(
            FaixaConsumo(
                faixa=faixa.rotulo,
                domicilios_amostra=len(grupo),
                consumo_per_capita_kwh=None if valor is None else round(valor, 1),
            )
        )
    return resultado


def populacao_da_faixa(populacao_do_ano: dict[int, int], faixa: Faixa) -> int:
    return sum(p for idade, p in populacao_do_ano.items() if faixa.contem(idade))


class ParametrosRecorte:
    """TEC e taxa de chefia por faixa, fixadas no ano de referência da POF."""

    def __init__(self, recorte: Recorte, domicilios: Iterable[Domicilio], populacao: dict[int, dict[int, int]]):
        if ANO_REFERENCIA_POF not in populacao:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}, ano de referência da POF")
        mononucleares = filtrar(domicilios, FiltroArranjo.mononucleares)
        self.faixas = FAIXAS_DO_RECORTE[recorte]
        self.populacao = populacao
        self.tec: dict[str, float] = {}
        self.chefia: dict[str, float] = {}
        for faixa in self.faixas:
            grupo = _da_faixa(mononucleares, faixa)
            self.tec[faixa.rotulo] = tec(sum(d.consumo_per_capita_kwh for d in grupo), len(grupo))
            self.chefia[faixa.rotulo] = len(grupo) / populacao_da_faixa(populacao[ANO_REFERENCIA_POF], faixa)

    def tbc_ibge(self, ano: int) -> float | None:
        if ano > ANO_FINAL_IBGE or ano not in self.populacao:
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


def _parametros(recorte: Recorte, repositorio: RepositorioProjecoes) -> ParametrosRecorte:
    return ParametrosRecorte(recorte, repositorio.domicilios(), repositorio.populacao_por_idade())


def obter_projecao(ano: int, recorte: Recorte, repositorio: RepositorioProjecoes) -> ProjecaoResposta:
    _validar_ano(ano)
    parametros = _parametros(recorte, repositorio)
    return ProjecaoResposta(ano=ano, recorte=recorte, cenarios=_cenarios(parametros, ano), dados_ilustrativos=False)


def obter_serie(recorte: Recorte, repositorio: RepositorioProjecoes) -> SerieResposta:
    parametros = _parametros(recorte, repositorio)
    pontos = [PontoSerie(ano=a, cenarios=_cenarios(parametros, a)) for a in range(ANO_INICIAL, ANO_FINAL + 1)]
    return SerieResposta(recorte=recorte, pontos=pontos, dados_ilustrativos=False)


def obter_consumo_por_faixa(filtro: FiltroArranjo, repositorio: RepositorioProjecoes) -> list[FaixaConsumo]:
    return consumo_por_faixa(repositorio.domicilios(), filtro)
