from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/fontes", tags=["fontes"])


class Fonte(BaseModel):
    id: str
    nome: str
    periodo: str
    uso: str


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
