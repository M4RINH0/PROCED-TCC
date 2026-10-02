import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from types import SimpleNamespace

from app.dados import Dados, obter_dados
from app.services.estrutura_etaria import FAIXAS_PIRAMIDE, montar_piramide

# total 100: homens 10 (5 anos) + 30 (65 anos); mulheres 20 (5 anos) + 40 (90 anos)
POR_SEXO = {"Homem": {5: 10, 65: 30}, "Mulher": {5: 20, 90: 40}}


class RepositorioFalso:
    def populacao_por_sexo(self, ano, localidade="Brasil"):
        return POR_SEXO

    def anos_piramide(self, localidade="Brasil"):
        return [2026, 2070]


class RepositorioProjecoesFalso:
    """60 a 69 mononucleares: 100 e 120 kWh -> TEC 110 com 2 domicílios."""

    def domicilios(self):
        return [
            SimpleNamespace(arranjo="Unipessoal (Mononuclear)", idade_chefe=62, consumo_per_capita_kwh=100.0),
            SimpleNamespace(arranjo="Casal ou Dupla", idade_chefe=68, consumo_per_capita_kwh=120.0),
            SimpleNamespace(arranjo="Multipessoal (3+)", idade_chefe=65, consumo_per_capita_kwh=999.0),
        ]

    def populacao_por_idade(self, localidade="Brasil"):
        return {}


class DadosFalsos(RepositorioFalso, RepositorioProjecoesFalso):
    """Uma fonte só com os métodos das duas partes da página."""


def test_faixas_da_piramide():
    assert [f[0] for f in FAIXAS_PIRAMIDE] == [
        "0 a 9", "10 a 19", "20 a 29", "30 a 39", "40 a 49", "50 a 59", "60 a 69", "70 a 79", "80+"
    ]


def test_percentuais_sobre_a_populacao_total():
    p = {f.faixa: f for f in montar_piramide(2030, POR_SEXO).faixas}
    assert (p["0 a 9"].homens_pct, p["0 a 9"].mulheres_pct) == (10.0, 20.0)
    assert p["60 a 69"].homens_pct == 30.0
    assert p["80+"].mulheres_pct == 40.0  # idade 90 entra no 80+
    assert p["30 a 39"].homens_pct == 0.0


def test_participacao_de_60_mais():
    # (30 + 40) / 100 = 70%
    assert montar_piramide(2030, POR_SEXO).participacao_60_mais_pct == 70.0


def test_ano_sem_populacao_falha():
    with pytest.raises(ValueError):
        montar_piramide(2030, {"Homem": {}, "Mulher": {}})


def test_repositorio_le_todos_os_anos_de_uma_vez_e_guarda_em_cache():
    chamadas = []

    class Cliente:
        def selecionar(self, tabela, colunas, filtros=None):
            chamadas.append(filtros)
            return [
                {"ano": 2030, "sexo": "Homem", "idade": 0, "populacao": 5},
                {"ano": 2030, "sexo": "Mulher", "idade": 0, "populacao": 6},
                {"ano": 2031, "sexo": "Homem", "idade": 0, "populacao": 7},
            ]

    repo = Dados(Cliente())
    assert repo.populacao_por_sexo(2030) == {"Homem": {0: 5}, "Mulher": {0: 6}}
    assert repo.populacao_por_sexo(2099) == {"Homem": {}, "Mulher": {}}
    assert repo.anos_piramide() == [2030, 2031]
    assert len(chamadas) == 1
    assert chamadas[0]["ano"] == "gte.2026" and chamadas[0]["localidade"] == "eq.Brasil"


@pytest.fixture
def cliente():
    app = criar_app()
    app.dependency_overrides[obter_dados] = DadosFalsos
    return TestClient(app)


def test_endpoint_piramide(cliente):
    r = cliente.get("/estrutura-etaria/piramide", params={"ano": 2050})
    assert r.status_code == 200 and r.json()["participacao_60_mais_pct"] == 70.0


@pytest.mark.parametrize("ano", [2025, 2071])
def test_endpoint_piramide_fora_da_projecao_retorna_422(cliente, ano):
    assert cliente.get("/estrutura-etaria/piramide", params={"ano": ano}).status_code == 422


def test_endpoint_consumo_chefe_padrao_mononucleares(cliente):
    r = cliente.get("/estrutura-etaria/consumo-chefe")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["arranjo"] == "mononucleares"
    faixa = next(f for f in corpo["faixas"] if f["faixa"] == "60 a 69")
    assert faixa == {"faixa": "60 a 69", "domicilios_amostra": 2, "consumo_per_capita_kwh": 110.0}


def test_endpoint_consumo_chefe_filtro_invalido(cliente):
    assert cliente.get("/estrutura-etaria/consumo-chefe", params={"arranjo": "familia"}).status_code == 422


def test_endpoint_piramides_para_em_2070(cliente):
    r = cliente.get("/estrutura-etaria/piramides")
    assert r.status_code == 200
    assert [p["ano"] for p in r.json()["piramides"]] == [2026, 2070]
