"""Consistência entre as telas com o banco real (Supabase). Só roda com credenciais no backend/.env e
quando pedido: .venv/Scripts/python -m pytest -m integracao

As consultas só leem: o Simulador roda sem a persistência de cenários (RF09), para o teste não gravar
nada na tabela cenario_salvo.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import DOTENV, ErroConfiguracao, carregar_configuracao
from app.dados import Dados, obter_dados
from app.main import criar_app
from app.supabase import criar_cliente
from test import consistencia

pytestmark = pytest.mark.integracao


class SemCenarioSalvo:
    """Dados reais sem obter_cenario e salvar_cenario: os serviços calculam sempre e não gravam."""

    def __init__(self, dados: Dados):
        self._dados = dados

    def __getattr__(self, nome):
        if nome in ("obter_cenario", "salvar_cenario"):
            raise AttributeError(nome)
        return getattr(self._dados, nome)


def _cliente_real():
    try:
        config = carregar_configuracao(dotenv=DOTENV)
        return criar_cliente(config)
    except (ErroConfiguracao, OSError) as erro:
        pytest.skip(f"sem credenciais do Supabase no .env: {erro}")


@pytest.fixture(scope="module")
def ambiente():
    dados = SemCenarioSalvo(Dados(_cliente_real()))
    app = criar_app(carregar_configuracao(dotenv=DOTENV))
    app.dependency_overrides[obter_dados] = lambda: dados
    return TestClient(app), dados


CASOS = [
    pytest.param({"localidade": local, "intensidade": i, "k": k}, id=f"{local}-{nome}")
    for local in ("Brasil", "Nordeste", "DF")
    for nome, i, k in (("padrao", 0.6, 1.0), ("simulacao", 1.0, 1.3))
]


@pytest.mark.parametrize("params", CASOS)
def test_1_consumo_das_celulas_soma_o_consumo_total_do_panorama(ambiente, params):
    cliente, dados = ambiente
    assert consistencia.checar_consumo_das_celulas(cliente, dados, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_2_composicao_igual_as_proporcoes_das_celulas(ambiente, params):
    assert consistencia.checar_composicao(ambiente[0], params) == []


@pytest.mark.parametrize("params", CASOS)
def test_3_participacao_60_mais_da_piramide_igual_a_do_panorama(ambiente, params):
    assert consistencia.checar_participacao_60_mais(ambiente[0], params) == []


@pytest.mark.parametrize("params", CASOS)
def test_4_celulas_do_simulador_somam_o_total_do_ano(ambiente, params):
    assert consistencia.checar_totais_do_simulador(ambiente[0], params) == []


@pytest.mark.parametrize("params", CASOS)
def test_5_exportacao_igual_a_api(ambiente, params):
    assert consistencia.checar_exportacao(ambiente[0], params) == []


@pytest.mark.parametrize("params", CASOS)
def test_6_comparacao_bate_com_o_panorama_nos_agregados(ambiente, params):
    assert consistencia.checar_comparacao_e_panorama(ambiente[0], params) == []
