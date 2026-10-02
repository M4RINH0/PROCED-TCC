import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.modules.projecoes import obter_repositorio
from app.modules.projecoes.tests.dados_teste import RepositorioFalso

app = criar_app()
app.dependency_overrides[obter_repositorio] = RepositorioFalso
cliente = TestClient(app)


def test_entrada_valida_segue_o_contrato():
    r = cliente.get("/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    assert r.json() == {
        "ano": 2030,
        "recorte": "chefe_60_mais",
        "unidade": "kWh/mes/pessoa",
        "cenarios": [
            {"id": "mod", "valor": None},
            {"id": "ibge", "valor": 153.3},
            {"id": "alt", "valor": None},
        ],
        "dados_ilustrativos": False,
        "fonte": "POF 2017 a 2018 e Projeções da População (IBGE)",
    }


def test_ausencia_de_dado_oficial_depois_de_2070():
    r = cliente.get("/projecoes", params={"ano": 2071, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    ibge = next(c for c in r.json()["cenarios"] if c["id"] == "ibge")
    assert ibge["valor"] is None


@pytest.mark.parametrize("ano", [2025, 2076, "dois mil"])
def test_ano_invalido_retorna_422(ano):
    assert cliente.get("/projecoes", params={"ano": ano, "recorte": "chefe_60_mais"}).status_code == 422


def test_recorte_invalido_retorna_422():
    assert cliente.get("/projecoes", params={"ano": 2030, "recorte": "todos"}).status_code == 422
    assert cliente.get("/projecoes/serie", params={"recorte": "todos"}).status_code == 422


def test_parametros_ausentes_retornam_422():
    assert cliente.get("/projecoes").status_code == 422
    assert cliente.get("/projecoes/serie").status_code == 422


def test_serie_tem_50_anos_e_oficial_ate_2070():
    r = cliente.get("/projecoes/serie", params={"recorte": "chefe_60_mais"})
    assert r.status_code == 200
    pontos = r.json()["pontos"]
    assert len(pontos) == 50 and pontos[0]["ano"] == 2026 and pontos[-1]["ano"] == 2075
    ibge = {p["ano"]: next(c["valor"] for c in p["cenarios"] if c["id"] == "ibge") for p in pontos}
    assert ibge[2070] is not None and ibge[2071] is None
