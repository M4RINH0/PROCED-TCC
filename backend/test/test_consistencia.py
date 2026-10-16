"""Consistência entre as telas (endpoints) na base sintética: Brasil, uma região e uma UF, com os
parâmetros padrão e com valores de simulação. Cada checagem devolve a lista de divergências."""

import pytest
from fastapi.testclient import TestClient

from app.dados import obter_dados
from app.main import criar_app
from test import consistencia
from test.base_sintetica import dados_sinteticos

DADOS = dados_sinteticos()
app = criar_app()
app.dependency_overrides[obter_dados] = lambda: DADOS
cliente = TestClient(app)

CASOS = [
    pytest.param({"localidade": local, "intensidade": i, "k": k}, id=f"{local}-{nome}")
    for local in ("Brasil", "Centro-Oeste", "DF")
    for nome, i, k in (("padrao", 0.6, 1.0), ("simulacao", 1.0, 1.3))
]


@pytest.mark.parametrize("params", CASOS)
def test_1_consumo_das_celulas_soma_o_consumo_total_do_panorama(params):
    assert consistencia.checar_consumo_das_celulas(cliente, DADOS, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_2_composicao_igual_as_proporcoes_das_celulas(params):
    assert consistencia.checar_composicao(cliente, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_3_participacao_60_mais_da_piramide_igual_a_do_panorama(params):
    assert consistencia.checar_participacao_60_mais(cliente, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_4_celulas_do_simulador_somam_o_total_do_ano(params):
    assert consistencia.checar_totais_do_simulador(cliente, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_5_exportacao_igual_a_api(params):
    assert consistencia.checar_exportacao(cliente, params) == []


@pytest.mark.parametrize("params", CASOS)
def test_6_comparacao_bate_com_o_panorama_nos_agregados(params):
    assert consistencia.checar_comparacao_e_panorama(cliente, params) == []


def test_base_sintetica_tem_tendencia_e_ignora_as_linhas_de_total():
    """Sanidade da própria base: a tendência age (taxas difere de só o envelhecimento em 2070) e a
    população do Brasil é a soma das quatro UFs com "Ambos", sem as linhas de total."""
    serie = consistencia.serie(cliente, consistencia.Recorte.todos_domicilios, {"localidade": "Brasil", "intensidade": 0.6, "k": 1.0})
    assert serie[2070]["taxas"]["valor"] != serie[2070]["taxas_arranjos_fixos"]["valor"]
    pop = DADOS.populacao_por_idade("Brasil")[2018]
    df = DADOS.populacao_por_idade("DF")[2018]
    assert pop[30] > df[30] and pop[30] < 5 * df[30]
