"""Orquestra as etapas do ETL em ordem (RNF08).

Cada etapa recebe a tabela da anterior e devolve (tabela, registro). O registro
diz a fonte e a transformação aplicada, para manter a rastreabilidade.
Hoje só existe a derivação; extração, limpeza e carga entram aqui quando forem
implementadas.
"""

from collections.abc import Callable, Sequence

import pandas as pd

from etl.derivacao import derivar

Etapa = Callable[[pd.DataFrame | None], tuple[pd.DataFrame, dict]]
ETAPAS: tuple[Etapa, ...] = (derivar,)


def executar(entrada: pd.DataFrame | None, etapas: Sequence[Etapa] = ETAPAS) -> tuple[pd.DataFrame | None, list[dict]]:
    dados = entrada
    rastro: list[dict] = []
    for etapa in etapas:
        dados, registro = etapa(dados)
        for campo in ("etapa", "fonte", "transformacao"):
            if not registro.get(campo):
                raise ValueError(f"a etapa {etapa.__name__} não registrou o campo {campo}")
        rastro.append(registro)
    return dados, rastro
