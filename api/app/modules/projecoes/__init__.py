"""Módulo projecoes: RF01, RF02 e RF11.

Interface pública. Outros módulos importam só daqui.
"""

from app.modules.projecoes.calculo import tbc, tbc_pd, tec
from app.modules.projecoes.router import router
from app.modules.projecoes.schemas import ANO_FINAL, ANO_FINAL_IBGE, ANO_INICIAL, Recorte

__all__ = ["router", "tec", "tbc", "tbc_pd", "Recorte", "ANO_INICIAL", "ANO_FINAL", "ANO_FINAL_IBGE"]
