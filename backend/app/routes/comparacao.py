"""Rotas da página Comparar (RF12)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dados import Dados, obter_dados
from app.dominio import (
    INTENSIDADE_MAXIMA,
    INTENSIDADE_MINIMA,
    INTENSIDADE_PADRAO,
    K_MAXIMO,
    K_MINIMO,
    K_PADRAO,
    MAXIMO_GRUPOS,
    MINIMO_GRUPOS,
    GrupoId,
    Localidade,
)
from app.schemas.comparacao import (
    ComparacaoResposta,
    FormaComparacao,
    IndicadorComparacao,
    LinhaSensibilidadeCobertura,
    LinhaSensibilidadeIntensidade,
    SensibilidadeCoberturaResposta,
    SensibilidadeIntensidadeResposta,
)
from app.schemas.panorama import CenarioId
from app.services.comparacao import obter_comparacao, validar_grupos

router = APIRouter(prefix="/comparacao", tags=["comparacao"])

TABELA_SENSIBILIDADE_INTENSIDADE = [
    LinhaSensibilidadeIntensidade(ano=2050, intensidade=0.0, tbc_kwh=74.94, efeito_arranjos_kwh=0.00, consumo_por_pessoa_kwh=63.15, consumo_total_bi_kwh=13.79, part_mono_60_pct=28.04, div_populacao_pct=13.72),
    LinhaSensibilidadeIntensidade(ano=2050, intensidade=0.5, tbc_kwh=77.96, efeito_arranjos_kwh=3.02, consumo_por_pessoa_kwh=66.09, consumo_total_bi_kwh=14.43, part_mono_60_pct=32.53, div_populacao_pct=5.77),
    LinhaSensibilidadeIntensidade(ano=2050, intensidade=0.6, tbc_kwh=78.52, efeito_arranjos_kwh=3.59, consumo_por_pessoa_kwh=66.70, consumo_total_bi_kwh=14.57, part_mono_60_pct=33.38, div_populacao_pct=4.26),
    LinhaSensibilidadeIntensidade(ano=2050, intensidade=1.0, tbc_kwh=80.60, efeito_arranjos_kwh=5.66, consumo_por_pessoa_kwh=69.19, consumo_total_bi_kwh=15.11, part_mono_60_pct=36.54, div_populacao_pct=-1.39),
    LinhaSensibilidadeIntensidade(ano=2070, intensidade=0.0, tbc_kwh=76.79, efeito_arranjos_kwh=0.00, consumo_por_pessoa_kwh=64.58, consumo_total_bi_kwh=12.87, part_mono_60_pct=33.26, div_populacao_pct=18.23),
    LinhaSensibilidadeIntensidade(ano=2070, intensidade=0.5, tbc_kwh=81.85, efeito_arranjos_kwh=5.06, consumo_por_pessoa_kwh=70.26, consumo_total_bi_kwh=14.00, part_mono_60_pct=42.12, div_populacao_pct=3.78),
    LinhaSensibilidadeIntensidade(ano=2070, intensidade=0.6, tbc_kwh=82.68, efeito_arranjos_kwh=5.88, consumo_por_pessoa_kwh=71.40, consumo_total_bi_kwh=14.23, part_mono_60_pct=43.63, div_populacao_pct=1.33),
    LinhaSensibilidadeIntensidade(ano=2070, intensidade=1.0, tbc_kwh=85.24, efeito_arranjos_kwh=8.45, consumo_por_pessoa_kwh=75.62, consumo_total_bi_kwh=15.07, part_mono_60_pct=48.59, div_populacao_pct=-6.60),
]

TABELA_SENSIBILIDADE_COBERTURA = [
    LinhaSensibilidadeCobertura(ano=2026, fator_peso=1.0000, cobertura_pct=92.4, domicilios_mi=72.39, moradores_mi=208.54, div_populacao_pct=-2.65, calibracao_p12=1.0272, tbc_kwh=71.54, consumo_por_pessoa_kwh=60.58, consumo_total_bi_kwh=12.98),
    LinhaSensibilidadeCobertura(ano=2026, fator_peso=1.0819, cobertura_pct=100.0, domicilios_mi=78.32, moradores_mi=225.62, div_populacao_pct=5.33, calibracao_p12=0.9494, tbc_kwh=71.54, consumo_por_pessoa_kwh=60.58, consumo_total_bi_kwh=12.98),
    LinhaSensibilidadeCobertura(ano=2050, fator_peso=1.0000, cobertura_pct=92.4, domicilios_mi=90.62, moradores_mi=227.76, div_populacao_pct=4.26, calibracao_p12=0.9591, tbc_kwh=78.52, consumo_por_pessoa_kwh=66.70, consumo_total_bi_kwh=14.57),
    LinhaSensibilidadeCobertura(ano=2050, fator_peso=1.0819, cobertura_pct=100.0, domicilios_mi=98.04, moradores_mi=246.42, div_populacao_pct=12.80, calibracao_p12=0.8865, tbc_kwh=78.52, consumo_por_pessoa_kwh=66.70, consumo_total_bi_kwh=14.57),
    LinhaSensibilidadeCobertura(ano=2070, fator_peso=1.0000, cobertura_pct=92.4, domicilios_mi=88.13, moradores_mi=201.88, div_populacao_pct=1.33, calibracao_p12=0.9869, tbc_kwh=82.68, consumo_por_pessoa_kwh=71.40, consumo_total_bi_kwh=14.23),
    LinhaSensibilidadeCobertura(ano=2070, fator_peso=1.0819, cobertura_pct=100.0, domicilios_mi=95.35, moradores_mi=218.41, div_populacao_pct=9.63, calibracao_p12=0.9121, tbc_kwh=82.68, consumo_por_pessoa_kwh=71.40, consumo_total_bi_kwh=14.23),
]


@router.get("/sensibilidade-intensidade", response_model=SensibilidadeIntensidadeResposta, summary="Sensibilidade à intensidade I (Tabela 5.6)")
def obter_sensibilidade_intensidade() -> SensibilidadeIntensidadeResposta:
    return SensibilidadeIntensidadeResposta(linhas=TABELA_SENSIBILIDADE_INTENSIDADE)


@router.get("/sensibilidade-cobertura", response_model=SensibilidadeCoberturaResposta, summary="Sensibilidade à cobertura POF (Tabela 5.7)")
def obter_sensibilidade_cobertura() -> SensibilidadeCoberturaResposta:
    return SensibilidadeCoberturaResposta(linhas=TABELA_SENSIBILIDADE_COBERTURA)

DESCRICAO_GRUPOS = (
    f"De {MINIMO_GRUPOS} a {MAXIMO_GRUPOS} grupos separados por vírgula: "
    + ", ".join(g.value for g in GrupoId)
    + " (células com chefe 60+ ou abaixo de 60 e os agregados mono e todos)"
)


def ler_grupos(texto: str) -> list[GrupoId]:
    """Valida a lista de grupos (RNF06): ids conhecidos, sem repetição, de 2 a 6."""
    try:
        return validar_grupos([GrupoId(g.strip()) for g in texto.split(",") if g.strip()])
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=f"grupos inválidos: {erro}") from erro


@router.get("", response_model=ComparacaoResposta, summary="Compara de 2 a 6 grupos de domicílios de 2026 a 2070")
def comparar(
    grupos: Annotated[str, Query(description=DESCRICAO_GRUPOS, examples=["uni_60,cas_60,mul_60"])],
    dados: Annotated[Dados, Depends(obter_dados)],
    indicador: Annotated[IndicadorComparacao, Query(description="consumo_por_pessoa só vale para agregados")] = IndicadorComparacao.domicilios,
    forma: Annotated[FormaComparacao, Query(description="absoluto ou índice com 2026 = 100")] = FormaComparacao.indice,
    cenario: Annotated[CenarioId, Query(description="taxas, taxas_arranjos_fixos ou contrafactual")] = CenarioId.taxas,
    localidade: Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")] = Localidade.Brasil,
    intensidade: Annotated[float, Query(ge=INTENSIDADE_MINIMA, le=INTENSIDADE_MAXIMA)] = INTENSIDADE_PADRAO,
    k: Annotated[float, Query(ge=K_MINIMO, le=K_MAXIMO)] = K_PADRAO,
) -> ComparacaoResposta:
    return obter_comparacao(ler_grupos(grupos), dados, indicador, forma, cenario, localidade.value, intensidade, k)
