import pytest
from fastapi.testclient import TestClient

from app.main import criar_app

cliente = TestClient(criar_app())


def test_entrada_valida_segue_o_contrato():
    r = cliente.get("/projecoes", params={"ano": 2075, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    assert r.json() == {
        "ano": 2075,
        "recorte": "chefe_60_mais",
        "unidade": "kWh/mes/pessoa",
        "cenarios": [
            {"id": "mod", "valor": 230.3},
            {"id": "ibge", "valor": None},
            {"id": "alt", "valor": 262.3},
        ],
        "dados_ilustrativos": True,
    }


def test_ibge_presente_ate_2060():
    r = cliente.get("/projecoes", params={"ano": 2060, "recorte": "chefe_60_mais"})
    ibge = next(c for c in r.json()["cenarios"] if c["id"] == "ibge")
    assert ibge["valor"] is not None


def test_ausencia_de_dado_oficial_depois_de_2060():
    r = cliente.get("/projecoes", params={"ano": 2061, "recorte": "mononuclear_abaixo_60"})
    assert r.status_code == 200
    ibge = next(c for c in r.json()["cenarios"] if c["id"] == "ibge")
    assert ibge["valor"] is None


@pytest.mark.parametrize("ano", [2025, 2076, "dois mil"])
def test_ano_invalido_retorna_422(ano):
    r = cliente.get("/projecoes", params={"ano": ano, "recorte": "chefe_60_mais"})
    assert r.status_code == 422


def test_recorte_invalido_retorna_422():
    r = cliente.get("/projecoes", params={"ano": 2030, "recorte": "todos"})
    assert r.status_code == 422


def test_parametros_ausentes_retornam_422():
    assert cliente.get("/projecoes").status_code == 422
