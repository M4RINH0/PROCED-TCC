"""Regiões e estados disponíveis para os filtros de todas as páginas."""

from fastapi import APIRouter

from app.dominio import BRASIL, NOMES_UF, REGIOES
from app.schemas.localidades import Estado, LocalidadesResposta, Regiao

router = APIRouter(prefix="/localidades", tags=["localidades"])


@router.get("", response_model=LocalidadesResposta, summary="Regiões e estados para os filtros")
def listar_localidades() -> LocalidadesResposta:
    return LocalidadesResposta(
        padrao=BRASIL,
        regioes=[
            Regiao(nome=nome, estados=[Estado(sigla=uf, nome=NOMES_UF[uf]) for uf in sorted(ufs, key=NOMES_UF.get)])
            for nome, ufs in REGIOES.items()
        ],
    )
