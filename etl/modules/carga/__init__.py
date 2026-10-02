"""Carga: gravação da base analítica no banco.

Pendente: escrever no banco exige aprovação do esquema (modelo
entidade-relacionamento) pelos integrantes.
"""

import pandas as pd


def carregar(_: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    raise NotImplementedError("carga ainda não implementada: depende da aprovação do esquema do banco")


__all__ = ["carregar"]
