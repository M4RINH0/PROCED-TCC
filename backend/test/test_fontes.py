from fastapi.testclient import TestClient

from app.main import criar_app


def test_lista_fontes_com_periodo():
    r = TestClient(criar_app()).get("/fontes")
    assert r.status_code == 200
    fontes = {f["id"]: f for f in r.json()}
    assert fontes["pof"]["periodo"] == "2017 a 2018"
    assert fontes["projecao"]["periodo"] == "2000 a 2070"
    assert all(f["nome"] and f["uso"] for f in fontes.values())
