"""Testes dos novos endpoints e estruturas tabulares do TCC."""

import pytest
from fastapi.testclient import TestClient

from app.dados import obter_dados
from app.main import criar_app
from test.test_estrutura_etaria import DadosFalsos


@pytest.fixture
def cliente():
    app = criar_app()
    app.dependency_overrides[obter_dados] = DadosFalsos
    return TestClient(app)


def test_endpoint_sintese_regional(cliente):
    r = cliente.get("/localidades/sintese-regional")
    assert r.status_code == 200
    dados = r.json()
    assert "linhas" in dados
    assert len(dados["linhas"]) == 6
    brasil = next(l for l in dados["linhas"] if l["localidade"] == "Brasil")
    assert brasil["tbc_2026"] == 71.54
    assert brasil["tbc_2070"] == 82.68
    assert brasil["amostra_pof"] == 52102


def test_endpoint_sensibilidade_intensidade(cliente):
    r = cliente.get("/comparacao/sensibilidade-intensidade")
    assert r.status_code == 200
    dados = r.json()
    assert "linhas" in dados
    assert len(dados["linhas"]) == 8
    p2050 = [l for l in dados["linhas"] if l["ano"] == 2050]
    assert len(p2050) == 4
    i06 = next(l for l in p2050 if l["intensidade"] == 0.6)
    assert i06["tbc_kwh"] == 78.52
    assert i06["efeito_arranjos_kwh"] == 3.59


def test_endpoint_sensibilidade_cobertura(cliente):
    r = cliente.get("/comparacao/sensibilidade-cobertura")
    assert r.status_code == 200
    dados = r.json()
    assert "linhas" in dados
    assert len(dados["linhas"]) == 6
    p2026 = [l for l in dados["linhas"] if l["ano"] == 2026]
    f10819 = next(l for l in p2026 if l["fator_peso"] == 1.0819)
    assert f10819["domicilios_mi"] == 78.32
    assert f10819["tbc_kwh"] == 71.54


def test_consumo_chefe_com_matriz(cliente):
    r = cliente.get("/estrutura-etaria/consumo-chefe")
    assert r.status_code == 200
    dados = r.json()
    assert "matriz" in dados
    assert dados["matriz"] is not None
    assert len(dados["matriz"]) == 7
    faixa_60 = next(l for l in dados["matriz"] if l["faixa"] == "60 a 69")
    assert "unipessoal" in faixa_60
    assert "casal_ou_dupla" in faixa_60
    assert "multipessoal" in faixa_60
