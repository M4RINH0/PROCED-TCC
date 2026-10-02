"""Orquestra as etapas do ETL na ordem: extração, limpeza, derivação e carga (RNF08).

Cada etapa recebe a tabela da anterior e devolve (tabela, registro). O registro
diz a fonte e a transformação aplicada, para manter a rastreabilidade.
"""

from collections.abc import Callable, Sequence

import pandas as pd

from modules.carga import carregar
from modules.derivacao import derivar
from modules.extracao import extrair
from modules.limpeza import limpar

Etapa = Callable[[pd.DataFrame | None], tuple[pd.DataFrame, dict]]
ETAPAS: tuple[Etapa, ...] = (extrair, limpar, derivar, carregar)


def executar(etapas: Sequence[Etapa] = ETAPAS) -> tuple[pd.DataFrame | None, list[dict]]:
    dados: pd.DataFrame | None = None
    rastro: list[dict] = []
    for etapa in etapas:
        dados, registro = etapa(dados)
        for campo in ("etapa", "fonte", "transformacao"):
            if not registro.get(campo):
                raise ValueError(f"a etapa {etapa.__name__} não registrou o campo {campo}")
        rastro.append(registro)
    return dados, rastro


if __name__ == "__main__":
    _, rastro = executar()
    for registro in rastro:
        print(f"{registro['etapa']}: {registro['transformacao']}")
