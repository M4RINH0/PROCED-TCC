from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import criar_app
from app.dados import obter_dados
from app.dominio import CASAL_OU_DUPLA as C
from app.dominio import MULTIPESSOAL as M
from app.dominio import UNIPESSOAL as U
from app.services.domicilios import EstruturaDomicilios, maior_resto, montar_composicao

# chefia de 2018: cada combinação tem 1 domicílio para 100 pessoas da faixa
DOMICILIOS = [
    SimpleNamespace(arranjo=U, idade_chefe=65, consumo_per_capita_kwh=100.0, peso=1.0),
    SimpleNamespace(arranjo=C, idade_chefe=65, consumo_per_capita_kwh=200.0, peso=1.0),
    SimpleNamespace(arranjo=M, idade_chefe=65, consumo_per_capita_kwh=50.0, peso=1.0),
    SimpleNamespace(arranjo=U, idade_chefe=30, consumo_per_capita_kwh=80.0, peso=1.0),
]
POPULACAO = {2018: {30: 100, 65: 100}, 2030: {30: 100, 65: 300}}


class RepositorioFalso:
    def domicilios(self):
        return DOMICILIOS

    def populacao_por_idade(self, localidade="Brasil"):
        return POPULACAO


def test_maior_resto_soma_exatamente_100():
    # 33,3 + 33,3 + 33,4: pisos 33, 33, 33; a casa que falta vai para o maior resto
    assert maior_resto([33.3, 33.3, 33.4]) == [33, 33, 34]
    assert maior_resto([0, 0]) == [0, 0]


def test_composicao_com_chefia_constante():
    # 2030: 60 a 69 tem 300 pessoas -> 3 domicílios em cada arranjo; 30 a 39 tem 100 -> 1 unipessoal
    # total 10: uni_60 30%, cas_60 30%, uni_59 10%, cas_59 0%, mul_60 30%, mul_59 0%
    r = montar_composicao(EstruturaDomicilios(DOMICILIOS, POPULACAO))
    assert r.anos == [2030]
    cat = {c.id: c for c in r.categorias}
    assert [c.id for c in r.categorias] == ["uni_60", "cas_60", "uni_59", "cas_59", "mul_60", "mul_59"]
    assert cat["uni_60"].participacao_pct == [30.0] and cat["uni_59"].participacao_pct == [10.0]
    assert [c.casas[0] for c in r.categorias] == [30, 30, 10, 0, 30, 0]
    assert cat["cas_60"].consumo_per_capita_kwh == 200.0 and cat["cas_60"].mononuclear
    assert cat["mul_60"].mononuclear is False
    assert cat["cas_59"].consumo_per_capita_kwh is None and cat["cas_59"].domicilios_amostra == 0


def test_endpoint_composicao():
    app = criar_app()
    app.dependency_overrides[obter_dados] = RepositorioFalso
    r = TestClient(app).get("/arranjos/composicao")
    assert r.status_code == 200
    assert r.json()["anos"] == [2030] and "chefia" in r.json()["fonte"]


def test_composicao_usa_o_peso_amostral():
    # 60 a 69: uni com peso 3 (100 kWh) e com peso 1 (200 kWh); 30 a 39: uni com peso 4
    # 2018: pop 100 nas duas faixas -> chefia uni 60 a 69 = 4/100, uni 30 a 39 = 4/100
    # 2030: 60 a 69 tem 300 -> 12 domicílios; 30 a 39 tem 100 -> 4; uni_60 = 12/16 = 75%
    # TEC uni 60+ = (3*100 + 1*200) / 4 = 125
    domicilios = [
        SimpleNamespace(arranjo=U, idade_chefe=65, consumo_per_capita_kwh=100.0, peso=3.0),
        SimpleNamespace(arranjo=U, idade_chefe=66, consumo_per_capita_kwh=200.0, peso=1.0),
        SimpleNamespace(arranjo=U, idade_chefe=30, consumo_per_capita_kwh=80.0, peso=4.0),
    ]
    r = montar_composicao(EstruturaDomicilios(domicilios, POPULACAO))
    cat = {c.id: c for c in r.categorias}
    assert cat["uni_60"].participacao_pct == [75.0] and cat["uni_59"].participacao_pct == [25.0]
    assert cat["uni_60"].consumo_per_capita_kwh == 125.0 and cat["uni_60"].domicilios_amostra == 2
