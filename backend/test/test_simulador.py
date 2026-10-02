from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.dados import obter_dados
from app.dominio import CASAL_OU_DUPLA as C
from app.dominio import UNIPESSOAL as U
from app.schemas.simulador import ArranjoSim, BaseSim, FaixaSim
from app.services.simulador import simular


class RepositorioFalso:
    """Unipessoal 70 a 79: 100 e 140 kWh -> TEC 120 com 2 domicílios."""

    def domicilios(self):
        return [
            SimpleNamespace(arranjo=U, idade_chefe=72, consumo_per_capita_kwh=100.0),
            SimpleNamespace(arranjo=U, idade_chefe=78, consumo_per_capita_kwh=140.0),
            SimpleNamespace(arranjo=C, idade_chefe=72, consumo_per_capita_kwh=999.0),
        ]

    def populacao_por_idade(self):
        return {}


def _sim(ano=2050, faixa=FaixaSim.de_70_a_79, arranjo=ArranjoSim.unipessoal, base=BaseSim.ibge):
    return simular(ano, faixa, arranjo, base, 1.7, RepositorioFalso())


def test_oficial_devolve_a_tec_da_combinacao():
    r = _sim()
    assert (r.valor, r.domicilios_amostra, r.motivo_sem_valor) == (120.0, 2, None)
    assert r.faixa == "70 a 79" and r.taxa == 1.7
    assert len(r.por_faixa) == 7


@pytest.mark.parametrize("base", [BaseSim.mod, BaseSim.alt])
def test_cenarios_nao_modelados(base):
    r = _sim(base=base)
    assert r.valor is None and r.motivo_sem_valor == "Cenário ainda não modelado."


def test_combinacao_sem_amostra():
    r = _sim(faixa=FaixaSim.de_30_a_39)
    assert r.valor is None and r.domicilios_amostra == 0 and "amostra" in r.motivo_sem_valor


@pytest.fixture
def cliente():
    app = criar_app()
    app.dependency_overrides[obter_dados] = RepositorioFalso
    return TestClient(app)


PARAMS = {"ano": 2050, "faixa": "70_79", "arranjo": "unipessoal", "base": "ibge", "taxa": 1.7}


def test_endpoint_entrada_valida(cliente):
    r = cliente.get("/simulador", params=PARAMS)
    assert r.status_code == 200 and r.json()["valor"] == 120.0


@pytest.mark.parametrize(
    "campo, valor", [("ano", 2071), ("faixa", "90_99"), ("arranjo", "familia"), ("base", "pde"), ("taxa", 11), ("taxa", -1)]
)
def test_endpoint_entrada_invalida_retorna_422(cliente, campo, valor):
    assert cliente.get("/simulador", params={**PARAMS, campo: valor}).status_code == 422


def test_endpoint_parametro_ausente_retorna_422(cliente):
    params = dict(PARAMS)
    del params["faixa"]
    assert cliente.get("/simulador", params=params).status_code == 422
