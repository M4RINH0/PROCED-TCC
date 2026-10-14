import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.dados import obter_dados
from test.dados_teste import RepositorioFalso

app = criar_app()
app.dependency_overrides[obter_dados] = RepositorioFalso
cliente = TestClient(app)


def test_entrada_valida_segue_o_contrato():
    # valores calculados à mão em test/test_panorama.py
    r = cliente.get("/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    corpo = r.json()
    assert set(corpo) == {
        "ano", "recorte", "unidade", "cenarios", "efeito_envelhecimento_kwh", "efeito_envelhecimento_total_kwh_mes",
        "dados_ilustrativos", "fonte", "localidade", "domicilios_amostra", "celulas", "baixa_confiabilidade",
    }
    assert corpo["cenarios"] == [
        {"id": "taxas", "valor": 153.3, "consumo_por_pessoa_kwh": 153.3, "consumo_total_calibrado_kwh_mes": 794545,
         "variacao_kwh": None, "variacao_pct": None},
        {"id": "ml_rf", "valor": None, "consumo_por_pessoa_kwh": None, "consumo_total_calibrado_kwh_mes": None,
         "variacao_kwh": None, "variacao_pct": None},
        {"id": "ml_gb", "valor": None, "consumo_por_pessoa_kwh": None, "consumo_total_calibrado_kwh_mes": None,
         "variacao_kwh": None, "variacao_pct": None},
        {"id": "contrafactual", "valor": 142.5, "consumo_por_pessoa_kwh": 142.5,
         "consumo_total_calibrado_kwh_mes": 676875, "variacao_kwh": None, "variacao_pct": None},
    ]
    assert corpo["efeito_envelhecimento_kwh"] == 10.8 and corpo["efeito_envelhecimento_total_kwh_mes"] == 117670
    assert corpo["dados_ilustrativos"] is False
    assert corpo["fonte"] == "POF 2017 a 2018 e Projeções da População (IBGE)"
    assert corpo["localidade"] == "Brasil" and corpo["domicilios_amostra"] == 4
    assert corpo["baixa_confiabilidade"] is True
    assert {"faixa": "60 a 69", "arranjo": "Unipessoal (Mononuclear)", "domicilios_amostra": 1,
            "baixa_confiabilidade": True} in corpo["celulas"]
    assert "oficial" not in r.text


def test_horizonte_termina_em_2070():
    assert cliente.get("/projecoes", params={"ano": 2070, "recorte": "chefe_60_mais"}).status_code == 200
    assert cliente.get("/projecoes", params={"ano": 2071, "recorte": "chefe_60_mais"}).status_code == 422


@pytest.mark.parametrize("ano", [2025, 2071, "dois mil"])
def test_ano_invalido_retorna_422(ano):
    assert cliente.get("/projecoes", params={"ano": ano, "recorte": "chefe_60_mais"}).status_code == 422


def test_recorte_invalido_retorna_422():
    assert cliente.get("/projecoes", params={"ano": 2030, "recorte": "todos"}).status_code == 422
    assert cliente.get("/projecoes/serie", params={"recorte": "todos"}).status_code == 422


def test_parametros_ausentes_retornam_422():
    assert cliente.get("/projecoes").status_code == 422
    assert cliente.get("/projecoes/serie").status_code == 422


def test_serie_tem_45_anos_e_taxas_ate_2070():
    r = cliente.get("/projecoes/serie", params={"recorte": "chefe_60_mais"})
    assert r.status_code == 200
    pontos = r.json()["pontos"]
    assert len(pontos) == 45 and pontos[0]["ano"] == 2026 and pontos[-1]["ano"] == 2070
    taxas = {p["ano"]: next(c["valor"] for c in p["cenarios"] if c["id"] == "taxas") for p in pontos}
    assert taxas[2070] is not None
    assert pontos[4]["efeito_envelhecimento_kwh"] == 10.8  # 2030
