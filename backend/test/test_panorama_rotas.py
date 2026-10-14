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
        "efeito_idade_kwh", "efeito_idade_total_kwh_mes", "efeito_arranjos_kwh", "efeito_arranjos_total_kwh_mes",
        "efeito_envelhecimento_participacao_pp", "efeito_idade_participacao_pp", "efeito_arranjos_participacao_pp",
        "dados_ilustrativos", "fonte", "localidade", "domicilios_amostra", "celulas", "baixa_confiabilidade",
        "intensidade", "k", "simulacao",
    }
    assert corpo["cenarios"] == [
        {"id": "taxas", "valor": 153.3, "consumo_por_pessoa_kwh": 153.3, "consumo_total_calibrado_kwh_mes": 794545,
         "participacao_consumo_pct": 29.7, "variacao_kwh": None, "variacao_pct": None},
        {"id": "taxas_arranjos_fixos", "valor": 153.3, "consumo_por_pessoa_kwh": 153.3,
         "consumo_total_calibrado_kwh_mes": 794545, "participacao_consumo_pct": 29.7, "variacao_kwh": None, "variacao_pct": None},
        {"id": "ml_rf", "valor": None, "consumo_por_pessoa_kwh": None, "consumo_total_calibrado_kwh_mes": None,
         "participacao_consumo_pct": None, "variacao_kwh": None, "variacao_pct": None},
        {"id": "ml_gb", "valor": None, "consumo_por_pessoa_kwh": None, "consumo_total_calibrado_kwh_mes": None,
         "participacao_consumo_pct": None, "variacao_kwh": None, "variacao_pct": None},
        {"id": "contrafactual", "valor": 142.5, "consumo_por_pessoa_kwh": 142.5,
         "consumo_total_calibrado_kwh_mes": 676875, "participacao_consumo_pct": 32.59, "variacao_kwh": None, "variacao_pct": None},
    ]
    assert corpo["efeito_envelhecimento_kwh"] == 10.8 and corpo["efeito_envelhecimento_total_kwh_mes"] == 117670
    # participação: taxas 920 / 3098 = 29,70%; contrafactual 783,75 / 2404,875 = 32,59%
    assert corpo["efeito_envelhecimento_participacao_pp"] == -2.89
    assert (corpo["efeito_idade_participacao_pp"], corpo["efeito_arranjos_participacao_pp"]) == (-2.89, 0.0)
    assert corpo["dados_ilustrativos"] is False
    assert corpo["fonte"].startswith("POF 2002 a 2003, 2008 a 2009 e 2017 a 2018")
    assert (corpo["intensidade"], corpo["k"], corpo["simulacao"]) == (0.6, 1.0, False)
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


@pytest.mark.parametrize(
    "campo, valor", [("intensidade", -0.1), ("intensidade", 1.6), ("k", 0.4), ("k", 1.6), ("k", "rapido")]
)
def test_controle_fora_do_limite_retorna_422(campo, valor):
    params = {"ano": 2030, "recorte": "chefe_60_mais", campo: valor}
    assert cliente.get("/projecoes", params=params).status_code == 422
    assert cliente.get("/projecoes/serie", params={"recorte": "chefe_60_mais", campo: valor}).status_code == 422


def test_controle_fora_do_padrao_marca_simulacao():
    r = cliente.get("/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais", "intensidade": 0.5, "k": 1.5}).json()
    assert (r["intensidade"], r["k"], r["simulacao"]) == (0.5, 1.5, True)
    s = cliente.get("/projecoes/serie", params={"recorte": "chefe_60_mais", "intensidade": 0}).json()
    assert s["simulacao"] is True and s["intensidade"] == 0


@pytest.mark.parametrize("recorte", ["todos_domicilios", "chefe_60_mais_todos", "chefe_60_mais", "mononuclear_abaixo_60"])
def test_aceita_os_quatro_recortes(recorte):
    r = cliente.get("/projecoes/serie", params={"recorte": recorte})
    assert r.status_code == 200 and r.json()["recorte"] == recorte


def test_todos_os_domicilios_incluem_os_multipessoais():
    # 2030: inclui (70 a 79, multipessoal) com 999 kWh, que o recorte mononuclear deixa de fora
    todos = cliente.get("/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais_todos"}).json()
    mono = cliente.get("/projecoes", params={"ano": 2030, "recorte": "chefe_60_mais"}).json()
    assert todos["domicilios_amostra"] == mono["domicilios_amostra"] + 1
    assert todos["cenarios"][0]["valor"] > mono["cenarios"][0]["valor"]
