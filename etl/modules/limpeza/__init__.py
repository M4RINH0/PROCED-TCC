"""Limpeza: nulos, outliers e critérios de inclusão e exclusão.

Pendente: os critérios precisam vir da Metodologia do TCC.
"""

import pandas as pd


def limpar(_: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    raise NotImplementedError("limpeza ainda não implementada: critérios a definir na Metodologia")


__all__ = ["limpar"]
