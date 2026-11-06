"""Regiões e estados disponíveis para os filtros de todas as páginas."""

from fastapi import APIRouter

from app.dominio import BRASIL, NOMES_UF, REGIOES
from app.schemas.localidades import Estado, LinhaSinteseRegional, LocalidadesResposta, Regiao, SinteseRegionalResposta

router = APIRouter(prefix="/localidades", tags=["localidades"])

SINTESE_REGIONAL_OFICIAL = [
    LinhaSinteseRegional(
        localidade="Brasil",
        amostra_pof=52102,
        populacao_60_mais_pct_2026=17.1,
        populacao_60_mais_pct_2070=37.8,
        tbc_2026=71.54,
        tbc_2070=82.68,
        variacao_tbc_pct=15.6,
        part_mono_60_mais_pct_2026=19.33,
        part_mono_60_mais_pct_2070=43.63,
    ),
    LinhaSinteseRegional(
        localidade="Norte",
        amostra_pof=6735,
        populacao_60_mais_pct_2026=11.5,
        populacao_60_mais_pct_2070=35.9,
        tbc_2026=69.02,
        tbc_2070=82.78,
        variacao_tbc_pct=19.9,
        part_mono_60_mais_pct_2026=10.79,
        part_mono_60_mais_pct_2070=33.30,
    ),
    LinhaSinteseRegional(
        localidade="Nordeste",
        amostra_pof=17646,
        populacao_60_mais_pct_2026=15.8,
        populacao_60_mais_pct_2070=39.4,
        tbc_2026=52.56,
        tbc_2070=62.15,
        variacao_tbc_pct=18.2,
        part_mono_60_mais_pct_2026=16.41,
        part_mono_60_mais_pct_2070=42.29,
    ),
    LinhaSinteseRegional(
        localidade="Centro-Oeste",
        amostra_pof=6175,
        populacao_60_mais_pct_2026=14.7,
        populacao_60_mais_pct_2070=34.6,
        tbc_2026=78.26,
        tbc_2070=88.92,
        variacao_tbc_pct=13.6,
        part_mono_60_mais_pct_2026=16.03,
        part_mono_60_mais_pct_2070=38.49,
    ),
    LinhaSinteseRegional(
        localidade="Sudeste",
        amostra_pof=13678,
        populacao_60_mais_pct_2026=18.8,
        populacao_60_mais_pct_2070=38.4,
        tbc_2026=78.04,
        tbc_2070=89.40,
        variacao_tbc_pct=14.6,
        part_mono_60_mais_pct_2026=21.88,
        part_mono_60_mais_pct_2070=46.11,
    ),
    LinhaSinteseRegional(
        localidade="Sul",
        amostra_pof=7868,
        populacao_60_mais_pct_2026=19.1,
        populacao_60_mais_pct_2070=36.8,
        tbc_2026=81.65,
        tbc_2070=91.60,
        variacao_tbc_pct=12.2,
        part_mono_60_mais_pct_2026=21.15,
        part_mono_60_mais_pct_2070=42.11,
    ),
]


@router.get("/sintese-regional", response_model=SinteseRegionalResposta, summary="Síntese demográfica e de consumo por macrorregião (Tabela 5.5)")
def obter_sintese_regional() -> SinteseRegionalResposta:
    return SinteseRegionalResposta(linhas=SINTESE_REGIONAL_OFICIAL)


@router.get("", response_model=LocalidadesResposta, summary="Regiões e estados para os filtros")
def listar_localidades() -> LocalidadesResposta:
    return LocalidadesResposta(
        padrao=BRASIL,
        regioes=[
            Regiao(nome=nome, estados=[Estado(sigla=uf, nome=NOMES_UF[uf]) for uf in sorted(ufs, key=NOMES_UF.get)])
            for nome, ufs in REGIOES.items()
        ],
    )
