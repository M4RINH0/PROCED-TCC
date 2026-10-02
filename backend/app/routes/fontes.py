"""Fontes e períodos de referência (RF10), usadas pela gaveta Fontes."""

from fastapi import APIRouter

from app.schemas.fontes import Fonte

router = APIRouter(prefix="/fontes", tags=["fontes"])


FONTES = [
    Fonte(
        id="pof",
        nome="Pesquisa de Orçamentos Familiares (IBGE)",
        periodo="2017 a 2018",
        uso="Consumo de energia por domicílio, arranjo e idade do chefe",
    ),
    Fonte(
        id="projecao",
        nome="Projeções da População (IBGE)",
        periodo="2000 a 2070",
        uso="Pirâmide etária e estrutura de domicílios do cenário oficial",
    ),
    Fonte(
        id="censo",
        nome="Censo Demográfico (IBGE)",
        periodo="2022",
        uso="População e envelhecimento por UF (no banco, ainda sem uso nas telas)",
    ),
]


@router.get("", response_model=list[Fonte], summary="Fontes e períodos de referência")
def listar_fontes() -> list[Fonte]:
    return FONTES
