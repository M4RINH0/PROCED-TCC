"""Extração: leitura dos microdados brutos da POF 2017 a 2018 e das projeções do IBGE.

Pendente: o formato dos arquivos brutos usados na carga atual do banco ainda
não está versionado neste repositório.
"""

import pandas as pd


def extrair(_: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    raise NotImplementedError("extração ainda não implementada: definir os arquivos brutos de origem")


__all__ = ["extrair"]
