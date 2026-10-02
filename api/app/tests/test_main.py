from fastapi.testclient import TestClient

from app.core import Configuracao
from app.main import criar_app

ORIGEM = "http://localhost:5173"
cliente = TestClient(
    criar_app(Configuracao(cors_origin=ORIGEM, supabase_url=None, database_url=None))
)


def test_cors_libera_a_origem_do_front_end():
    r = cliente.get(
        "/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais"}, headers={"Origin": ORIGEM}
    )
    assert r.headers.get("access-control-allow-origin") == ORIGEM


def test_cors_nao_libera_outra_origem():
    r = cliente.get(
        "/projecoes",
        params={"ano": 2030, "recorte": "chefe_60_mais"},
        headers={"Origin": "https://outro-site.exemplo"},
    )
    assert "access-control-allow-origin" not in r.headers


def test_documentacao_gerada_pelo_codigo():
    r = cliente.get("/openapi.json")
    assert r.status_code == 200
    assert "/projecoes" in r.json()["paths"]
