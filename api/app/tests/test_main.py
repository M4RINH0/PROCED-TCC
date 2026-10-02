from fastapi.testclient import TestClient

from app.core import Configuracao, ErroFonteDados, supabase
from app.main import criar_app
from app.modules import projecoes

ORIGEM = "http://localhost:5173"
CONFIG = Configuracao(cors_origin=ORIGEM, supabase_url=None, database_url=None)
PARAMS = {"recorte": "chefe_60_mais"}


class Quebrado:
    def domicilios(self):
        raise ErroFonteDados("fora do ar")

    def populacao_por_idade(self):
        raise ErroFonteDados("fora do ar")


def _cliente(repositorio=Quebrado):
    app = criar_app(CONFIG)
    app.dependency_overrides[projecoes.obter_repositorio] = repositorio
    return TestClient(app)


def test_cors_libera_a_origem_do_front_end():
    r = _cliente().get("/fontes", headers={"Origin": ORIGEM})
    assert r.headers.get("access-control-allow-origin") == ORIGEM


def test_cors_nao_libera_outra_origem():
    r = _cliente().get("/fontes", headers={"Origin": "https://outro-site.exemplo"})
    assert "access-control-allow-origin" not in r.headers


def test_documentacao_gerada_pelo_codigo():
    caminhos = _cliente().get("/openapi.json").json()["paths"]
    for caminho in ["/projecoes", "/projecoes/serie", "/arranjos", "/estrutura-etaria/piramide",
                    "/estrutura-etaria/consumo-chefe", "/fontes"]:
        assert caminho in caminhos


def test_fonte_indisponivel_vira_503():
    r = _cliente().get("/projecoes/serie", params=PARAMS)
    assert r.status_code == 503
    assert r.json() == {"detail": "Fonte de dados indisponível no momento"}


def test_sem_credenciais_vira_503_sem_expor_detalhe(monkeypatch):
    monkeypatch.setattr(supabase, "carregar_configuracao", lambda **_: CONFIG)
    supabase.obter_cliente.cache_clear()
    projecoes.obter_repositorio.cache_clear()
    try:
        r = TestClient(criar_app(CONFIG)).get("/projecoes/serie", params=PARAMS)
        assert r.status_code == 503
        assert "SUPABASE" not in r.text
    finally:
        supabase.obter_cliente.cache_clear()
        projecoes.obter_repositorio.cache_clear()


def test_aquecer_conta_as_cargas_e_ignora_falha_da_fonte():
    from app.main import aquecer

    chamadas = []

    def ok():
        chamadas.append("ok")

    def falha():
        raise ErroFonteDados("fora do ar")

    assert aquecer([ok, falha, ok]) == 2
    assert chamadas == ["ok", "ok"]
