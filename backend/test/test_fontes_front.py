"""O rodapé do front-end cita a fonte da API; enquanto a resposta não chega ou quando a consulta
falha, usa os textos de frontend/src/utils/fontes.js. Este teste garante que são os mesmos."""

import re
from pathlib import Path

from app.schemas.domicilios import FONTE_COMPOSICAO
from app.schemas.estrutura_etaria import FONTE_CONSUMO, FONTE_PIRAMIDE
from app.schemas.panorama import FONTE as FONTE_PANORAMA
from app.schemas.simulador import FONTE as FONTE_SIMULADOR

ARQUIVO = Path(__file__).resolve().parents[2] / "frontend" / "src" / "utils" / "fontes.js"


def _constantes_do_front() -> dict[str, str]:
    texto = ARQUIVO.read_text(encoding="utf-8")
    return {nome: valor for nome, valor in re.findall(r"export const (\w+) =\s*'([^']*)'", texto)}


def test_fontes_do_front_sao_iguais_as_da_api():
    front = _constantes_do_front()
    assert front == {
        "FONTE_PANORAMA": FONTE_PANORAMA,
        "FONTE_COMPOSICAO": FONTE_COMPOSICAO,
        "FONTE_PIRAMIDE": FONTE_PIRAMIDE,
        "FONTE_CONSUMO_CHEFE": FONTE_CONSUMO,
        "FONTE_SIMULADOR": FONTE_SIMULADOR,
    }
