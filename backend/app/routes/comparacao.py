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
from app.schemas.comparacao import ComparacaoResposta, FormaComparacao, IndicadorComparacao
from app.schemas.panorama import CenarioId
from app.services.comparacao import obter_comparacao, validar_grupos

router = APIRouter(prefix="/comparacao", tags=["comparacao"])

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
