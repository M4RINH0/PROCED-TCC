import threading
from typing import Protocol

from app.core import ClienteSupabase

COLUNAS = (
    "sigla_uf,arranjo_familiar,is_60_mais,total_domicilios_amostra,"
    "media_consumo_total_kwh,media_consumo_per_capita_kwh,media_gasto_rs"
)


class RepositorioArranjos(Protocol):
    def coeficientes(self) -> list[dict]:
        """Linhas de dim_coeficiente_consumo: uma por UF, arranjo e indicador 60+."""
        ...


class RepositorioSupabase:
    def __init__(self, cliente: ClienteSupabase):
        self._cliente = cliente
        self._trava = threading.Lock()
        self._linhas: list[dict] | None = None

    def coeficientes(self) -> list[dict]:
        with self._trava:
            if self._linhas is None:
                self._linhas = self._cliente.selecionar("dim_coeficiente_consumo", COLUNAS, {"order": "id.asc"})
            return self._linhas
