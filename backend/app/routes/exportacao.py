from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.dados import Dados, obter_dados
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    INTENSIDADE_MAXIMA,
    INTENSIDADE_MINIMA,
    INTENSIDADE_PADRAO,
    K_MAXIMO,
    K_MINIMO,
    K_PADRAO,
    Localidade,
    Recorte,
)
from app.routes.comparacao import ler_grupos
from app.schemas.comparacao import FormaComparacao, IndicadorComparacao
from app.schemas.exportacao import EscopoExportacao, FormatoExportacao
from app.schemas.panorama import CenarioId
from app.services.comparacao import obter_comparacao
from app.services.exportacao import ArquivoExportado, exportar_comparacao, exportar_dados

router = APIRouter(prefix="/exportar", tags=["exportacao"])


@router.get("", summary="Exporta as projeções em CSV ou XLSX (RF08)")
def baixar_exportacao(
    dados: Annotated[Dados, Depends(obter_dados)],
    formato: Annotated[FormatoExportacao, Query(description="csv ou xlsx")] = FormatoExportacao.csv,
    escopo: Annotated[EscopoExportacao, Query(description="ano ou serie")] = EscopoExportacao.ano,
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")] = ANO_FINAL,
    recorte: Annotated[Recorte | None, Query(description="Grupo de domicílios opcional")] = None,
    localidade: Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")] = Localidade.Brasil,
    intensidade: Annotated[float, Query(ge=INTENSIDADE_MINIMA, le=INTENSIDADE_MAXIMA)] = INTENSIDADE_PADRAO,
    k: Annotated[float, Query(ge=K_MINIMO, le=K_MAXIMO)] = K_PADRAO,
) -> Response:
    return _download(exportar_dados(dados, formato, escopo, ano, recorte, localidade.value, intensidade, k))


@router.get("/comparacao", summary="Exporta a comparação de grupos em CSV ou XLSX (RF08 e RF12)")
def baixar_comparacao(
    grupos: Annotated[str, Query(description="Os mesmos grupos de /comparacao, separados por vírgula")],
    dados: Annotated[Dados, Depends(obter_dados)],
    formato: Annotated[FormatoExportacao, Query(description="csv ou xlsx")] = FormatoExportacao.csv,
    indicador: Annotated[IndicadorComparacao, Query()] = IndicadorComparacao.domicilios,
    forma: Annotated[FormaComparacao, Query()] = FormaComparacao.indice,
    cenario: Annotated[CenarioId, Query()] = CenarioId.taxas,
    localidade: Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")] = Localidade.Brasil,
    intensidade: Annotated[float, Query(ge=INTENSIDADE_MINIMA, le=INTENSIDADE_MAXIMA)] = INTENSIDADE_PADRAO,
    k: Annotated[float, Query(ge=K_MINIMO, le=K_MAXIMO)] = K_PADRAO,
) -> Response:
    resposta = obter_comparacao(ler_grupos(grupos), dados, indicador, forma, cenario, localidade.value, intensidade, k)
    return _download(exportar_comparacao(resposta, formato))


def _download(arquivo: ArquivoExportado) -> Response:
    return Response(
        content=arquivo.conteudo,
        media_type=arquivo.media_type,
        headers={"Content-Disposition": f'attachment; filename="{arquivo.nome_arquivo}"'},
    )
