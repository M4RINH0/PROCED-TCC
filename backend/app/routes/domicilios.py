"""Rotas da página Domicílios (RF02, RF03, RF04)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dados import Dados, obter_dados
from app.dominio import INTENSIDADE_MAXIMA, INTENSIDADE_MINIMA, INTENSIDADE_PADRAO, K_MAXIMO, K_MINIMO, K_PADRAO, Localidade
from app.schemas.domicilios import ArranjosResposta, ComposicaoResposta, Grupo
from app.services.domicilios import obter_arranjos, obter_composicao

router = APIRouter(prefix="/arranjos", tags=["domicílios"])

DadosDep = Annotated[Dados, Depends(obter_dados)]
ParamLocalidade = Annotated[Localidade, Query(description="Brasil, região ou sigla da UF")]
ParamIntensidade = Annotated[
    float,
    Query(
        ge=INTENSIDADE_MINIMA,
        le=INTENSIDADE_MAXIMA,
        description="Intensidade da tendência dos arranjos depois de 2026: 0 congela os arranjos (padrão calibrado 0,6)",
    ),
]
ParamK = Annotated[
    float, Query(ge=K_MINIMO, le=K_MAXIMO, description="Velocidade do envelhecimento: 1 é a projeção do IBGE (padrão)")
]


@router.get("", response_model=ArranjosResposta, summary="Consumo por arranjo domiciliar")
def consultar_arranjos(
    dados: DadosDep,
    grupo: Annotated[Grupo, Query(description="Idade do chefe")] = Grupo.todos,
    localidade: ParamLocalidade = Localidade.Brasil,
) -> ArranjosResposta:
    return obter_arranjos(grupo, dados, localidade.value)


@router.get("/composicao", response_model=ComposicaoResposta, summary="Composição dos domicílios por arranjo, 2026 a 2070")
def consultar_composicao(
    dados: DadosDep,
    localidade: ParamLocalidade = Localidade.Brasil,
    intensidade: ParamIntensidade = INTENSIDADE_PADRAO,
    k: ParamK = K_PADRAO,
) -> ComposicaoResposta:
    return obter_composicao(dados, localidade.value, intensidade, k)
