"""Rotas da página Estrutura etária (RF02, RF05, RF06)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import ANO_FINAL, ANO_INICIAL, K_MAXIMO, K_MINIMO, K_PADRAO, FiltroArranjo, Localidade
from app.schemas.estrutura_etaria import ConsumoChefeResposta, PiramideResposta, PiramidesResposta
from app.services.estrutura_etaria import obter_consumo_chefe, obter_piramide, obter_piramides

router = APIRouter(prefix="/estrutura-etaria", tags=["estrutura etária"])

DadosDep = Annotated[Dados, Depends(obter_dados)]
ParamLocalidade = Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")]
ParamK = Annotated[
    float, Query(ge=K_MINIMO, le=K_MAXIMO, description="Velocidade do envelhecimento: 1 é a projeção do IBGE (padrão)")
]


@router.get("/piramide", response_model=PiramideResposta, summary="Pirâmide etária da localidade num ano")
def consultar_piramide(
    ano: Annotated[int, Query(ge=ANO_INICIAL, le=ANO_FINAL, description="Ano de 2026 a 2070")],
    dados: DadosDep,
    localidade: ParamLocalidade = Localidade.Brasil,
    k: ParamK = K_PADRAO,
) -> PiramideResposta:
    return obter_piramide(ano, dados, localidade.value, k=k)


@router.get("/piramides", response_model=PiramidesResposta, summary="Pirâmides etárias da localidade, 2026 a 2070")
def consultar_piramides(
    dados: DadosDep, localidade: ParamLocalidade = Localidade.Brasil, k: ParamK = K_PADRAO
) -> PiramidesResposta:
    return obter_piramides(dados, localidade.value, k=k)


@router.get("/consumo-chefe", response_model=ConsumoChefeResposta, summary="Consumo por faixa etária do chefe")
def consultar_consumo_chefe(
    dados: DadosDep,
    arranjo: Annotated[FiltroArranjo, Query()] = FiltroArranjo.mononucleares,
    localidade: ParamLocalidade = Localidade.Brasil,
) -> ConsumoChefeResposta:
    return obter_consumo_chefe(arranjo, dados, localidade.value)
