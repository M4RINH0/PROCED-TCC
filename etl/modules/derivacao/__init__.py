"""Derivação: variáveis derivadas, como o arranjo domiciliar.

Interface pública do módulo.
"""

from modules.derivacao.regras import (
    ARRANJOS,
    arranjo_familiar,
    consumo_per_capita,
    derivar,
    eh_60_mais,
    faixa_etaria_chefe,
)

__all__ = [
    "ARRANJOS",
    "arranjo_familiar",
    "consumo_per_capita",
    "derivar",
    "eh_60_mais",
    "faixa_etaria_chefe",
]
