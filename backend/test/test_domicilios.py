import pytest
from fastapi.testclient import TestClient

from app.dados import Domicilio, obter_dados
from app.main import criar_app
from app.schemas.domicilios import Grupo
from app.services.domicilios import agregar

U, C, M = "Unipessoal (Mononuclear)", "Casal ou Dupla", "Multipessoal (3+)"

# arranjo, idade, per capita, UF, peso, consumo do domicílio, moradores, id, gasto
DOMICILIOS = [
    Domicilio(M, 40, 40.0, "AC", 50.0, 160.0, 4, 1, 100.0),
    Domicilio(U, 65, 100.0, "AC", 10.0, 100.0, 1, 2, 50.0),
    Domicilio(U, 70, 200.0, "SP", 30.0, 200.0, 1, 3, 90.0),
    Domicilio(C, 45, 80.0, "SP", 20.0, 160.0, 2, 4, 70.0),
]


class RepositorioFalso:
    def domicilios(self):
        return DOMICILIOS


def test_media_ponderada_pelo_peso_amostral():
    uni = agregar(DOMICILIOS, Grupo.todos)[0]
    # (10 * 100 + 30 * 200) / 40 = 175; gasto (10 * 50 + 30 * 90) / 40 = 80
    assert uni.arranjo == U and uni.chefe_60_mais
    assert uni.domicilios_amostra == 2 and uni.baixa_confiabilidade is True
    assert uni.consumo_per_capita_kwh == 175.0
    assert uni.consumo_total_kwh == 175.0
    assert uni.gasto_rs == 80.0
    assert uni.mononuclear is True


def test_consumo_do_domicilio_e_per_capita_sao_medias_diferentes():
    # casal: per capita 80, consumo do domicílio 160
    casal = next(a for a in agregar(DOMICILIOS, Grupo.todos) if a.arranjo == C)
    assert (casal.consumo_per_capita_kwh, casal.consumo_total_kwh) == (80.0, 160.0)


def test_ordem_e_marcacao_de_mononucleares():
    r = agregar(DOMICILIOS, Grupo.todos)
    assert [(a.arranjo, a.mononuclear) for a in r] == [(U, True), (C, True), (M, False)]


@pytest.mark.parametrize(
    "grupo, esperado", [(Grupo.chefe_60_mais, {True}), (Grupo.abaixo_60, {False}), (Grupo.todos, {True, False})]
)
def test_filtra_pela_idade_do_chefe(grupo, esperado):
    assert {a.chefe_60_mais for a in agregar(DOMICILIOS, grupo)} == esperado


def test_sem_domicilios_nao_ha_arranjo():
    assert agregar([], Grupo.todos) == []


def test_gasto_ausente_fica_nulo():
    sem_gasto = [Domicilio(U, 65, 100.0, "AC", 10.0, 100.0, 1, 2)]
    assert agregar(sem_gasto, Grupo.todos)[0].gasto_rs is None


def test_30_domicilios_nao_tem_aviso():
    trinta = [Domicilio(U, 65, 100.0, "AC", 1.0, 100.0, 1, i) for i in range(30)]
    assert agregar(trinta, Grupo.todos)[0].baixa_confiabilidade is False


def test_endpoint_valida_e_filtra():
    app = criar_app()
    app.dependency_overrides[obter_dados] = RepositorioFalso
    cliente = TestClient(app)
    r = cliente.get("/arranjos", params={"grupo": "abaixo_60"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["unidade"] == "kWh/mes/pessoa" and "peso amostral" in corpo["fonte"]
    assert [a["arranjo"] for a in corpo["arranjos"]] == [C, M]
    assert cliente.get("/arranjos").status_code == 200
    assert cliente.get("/arranjos", params={"grupo": "idosos"}).status_code == 422
