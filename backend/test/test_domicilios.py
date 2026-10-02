import pytest
from fastapi.testclient import TestClient

from app.main import criar_app
from app.dados import Dados, obter_dados
from app.schemas.domicilios import Grupo
from app.services.domicilios import agregar


def _linha(uf, arranjo, idoso, n, per_capita, total=0.0, gasto=0.0):
    return {
        "sigla_uf": uf,
        "arranjo_familiar": arranjo,
        "is_60_mais": idoso,
        "total_domicilios_amostra": n,
        "media_consumo_per_capita_kwh": per_capita,
        "media_consumo_total_kwh": total,
        "media_gasto_rs": gasto,
    }


LINHAS = [
    _linha("AC", "Multipessoal (3+)", False, 50, 40.0, 160.0, 100.0),
    _linha("AC", "Unipessoal (Mononuclear)", True, 10, 100.0, 100.0, 50.0),
    _linha("SP", "Unipessoal (Mononuclear)", True, 30, 200.0, 200.0, 90.0),
    _linha("SP", "Casal ou Dupla", False, 20, 80.0, 160.0, 70.0),
]


class RepositorioFalso:
    def coeficientes(self):
        return LINHAS


def test_media_nacional_pondera_pela_amostra():
    uni = agregar(LINHAS, Grupo.todos)[0]
    # (10 * 100 + 30 * 200) / 40 = 175; gasto (10 * 50 + 30 * 90) / 40 = 80
    assert uni.arranjo == "Unipessoal (Mononuclear)" and uni.chefe_60_mais
    assert uni.domicilios_amostra == 40
    assert uni.consumo_per_capita_kwh == 175.0
    assert uni.consumo_total_kwh == 175.0
    assert uni.gasto_rs == 80.0
    assert uni.mononuclear is True


def test_ordem_e_marcacao_de_mononucleares():
    r = agregar(LINHAS, Grupo.todos)
    assert [(a.arranjo, a.mononuclear) for a in r] == [
        ("Unipessoal (Mononuclear)", True),
        ("Casal ou Dupla", True),
        ("Multipessoal (3+)", False),
    ]


@pytest.mark.parametrize(
    "grupo, esperado", [(Grupo.chefe_60_mais, {True}), (Grupo.abaixo_60, {False}), (Grupo.todos, {True, False})]
)
def test_filtra_pela_idade_do_chefe(grupo, esperado):
    assert {a.chefe_60_mais for a in agregar(LINHAS, grupo)} == esperado


def test_ignora_combinacao_sem_amostra():
    assert agregar([_linha("AC", "Casal ou Dupla", True, 0, 10.0)], Grupo.todos) == []


def test_repositorio_le_a_tabela_uma_vez():
    class Cliente:
        n = 0

        def selecionar(self, tabela, colunas, filtros=None):
            Cliente.n += 1
            assert tabela == "dim_coeficiente_consumo"
            return LINHAS

    repo = Dados(Cliente())
    repo.coeficientes(), repo.coeficientes()
    assert Cliente.n == 1


def test_endpoint_valida_e_filtra():
    app = criar_app()
    app.dependency_overrides[obter_dados] = RepositorioFalso
    cliente = TestClient(app)
    r = cliente.get("/arranjos", params={"grupo": "abaixo_60"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["unidade"] == "kWh/mes/pessoa" and "POF" in corpo["fonte"]
    assert [a["arranjo"] for a in corpo["arranjos"]] == ["Casal ou Dupla", "Multipessoal (3+)"]
    assert cliente.get("/arranjos").status_code == 200
    assert cliente.get("/arranjos", params={"grupo": "idosos"}).status_code == 422
