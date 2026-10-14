"""Filtros de região e estado em todas as páginas."""

import pytest
from fastapi.testclient import TestClient

from app.dados import Dados, Domicilio, obter_dados
from app.dominio import NOMES_UF, REGIOES, Localidade, da_localidade, ufs_da_localidade
from app.main import criar_app
from app.schemas.domicilios import Grupo
from app.services.domicilios import obter_arranjos
from app.services.estrutura_etaria import obter_consumo_chefe
from app.services.panorama import obter_serie
from app.dominio import FiltroArranjo, Recorte

UNI, CASAL = "Unipessoal (Mononuclear)", "Casal ou Dupla"

# DF: 60 a 69 = 100 e 70 a 79 = 200 e 80+ = 300 (um domicílio cada); SP: 60 a 69 = 50
DOMICILIOS = [
    Domicilio(UNI, 65, 100.0, "DF"),
    Domicilio(CASAL, 75, 200.0, "DF"),
    Domicilio(UNI, 85, 300.0, "DF"),
    Domicilio(UNI, 65, 50.0, "SP"),
]
POP = {2018: {65: 100, 75: 100, 85: 100}, 2030: {65: 100, 75: 100, 85: 100}}


class DadosFalsos:
    def __init__(self):
        self.localidades_pedidas = []

    def domicilios(self):
        return DOMICILIOS

    def domicilios_historicos(self):
        return []  # sem as POFs anteriores não há tendência: os arranjos ficam congelados

    def populacao_por_idade(self, localidade="Brasil"):
        self.localidades_pedidas.append(localidade)
        return POP


# ---------- domínio ----------

def test_regioes_cobrem_as_27_ufs_sem_repetir():
    todas = [uf for ufs in REGIOES.values() for uf in ufs]
    assert len(todas) == 27 and set(todas) == set(NOMES_UF)


@pytest.mark.parametrize(
    "localidade, esperado",
    [("Brasil", None), ("Centro-Oeste", {"DF", "GO", "MS", "MT"}), ("SP", {"SP"})],
)
def test_ufs_da_localidade(localidade, esperado):
    assert ufs_da_localidade(localidade) == esperado


def test_localidade_desconhecida_falha():
    with pytest.raises(ValueError):
        ufs_da_localidade("Atlântida")


def test_da_localidade_filtra_os_domicilios_pela_uf():
    assert len(da_localidade(DOMICILIOS, "Brasil")) == 4
    assert len(da_localidade(DOMICILIOS, "Centro-Oeste")) == 3
    assert [d.consumo_per_capita_kwh for d in da_localidade(DOMICILIOS, "SP")] == [50.0]
    assert da_localidade(DOMICILIOS, "AC") == []


def test_enumeracao_aceita_brasil_regioes_e_ufs():
    valores = {l.value for l in Localidade}
    assert len(valores) == 33 and {"Brasil", "Centro-Oeste", "DF"} <= valores


# ---------- leitura do banco ----------

def test_projecao_e_lida_por_localidade_e_guardada_em_cache():
    chamadas = []

    class Cliente:
        def selecionar(self, tabela, colunas, filtros=None):
            chamadas.append(filtros)
            return [
                {"localidade": "PR", "sexo": "Ambos", "ano": 2030, "idade": 60, "populacao": 7},
                {"localidade": "RS", "sexo": "Ambos", "ano": 2030, "idade": 60, "populacao": 3},
                {"localidade": "Sul", "sexo": "Ambos", "ano": 2030, "idade": 60, "populacao": 10},
            ]

    dados = Dados(Cliente())
    sul = dados.populacao_por_idade("Sul")
    dados.populacao_por_idade("Sul"), dados.populacao_por_idade("RS")
    # a região é a soma das suas UFs pela lista explícita; a linha de total "Sul" não entra
    assert [c["localidade"] for c in chamadas] == ["in.(PR,RS,SC)", "in.(RS)"]
    assert sul == {2030: {60: 10}}
    assert dados.populacao_por_idade("RS") == {2030: {60: 3}}
    assert chamadas[0]["ano"] == "gte.2018" and chamadas[0]["sexo"] == "eq.Ambos"


# ---------- serviços ----------

def test_serie_usa_so_os_domicilios_e_a_populacao_da_localidade():
    dados = DadosFalsos()
    # DF: (100 + 200 + 300) / 3 = 200, com chefia igual nas três faixas
    df = obter_serie(Recorte.chefe_60_mais, dados, "DF")
    assert df.localidade == "DF" and df.domicilios_amostra == 3
    assert df.pontos[4].cenarios[0].valor == 200.0  # 2030, cenário taxas
    assert dados.localidades_pedidas[-1] == "DF"
    # SP só tem a faixa de 60 a 69: as outras duas não têm amostra, então fica sem valor
    sp = obter_serie(Recorte.chefe_60_mais, dados, "SP")
    assert sp.domicilios_amostra == 1 and sp.pontos[4].cenarios[0].valor is None
    assert sp.baixa_confiabilidade is True


def test_consumo_por_arranjo_usa_so_os_domicilios_da_regiao():
    # Centro-Oeste: só DF tem domicílios; unipessoal 60+: (100 + 300) / 2 = 200; SP (50) fica de fora
    r = obter_arranjos(Grupo.todos, DadosFalsos(), "Centro-Oeste")
    assert r.localidade == "Centro-Oeste"
    assert r.arranjos[0].domicilios_amostra == 2 and r.arranjos[0].consumo_per_capita_kwh == 200.0
    assert r.arranjos[0].baixa_confiabilidade is True


def test_consumo_por_faixa_do_chefe_na_uf():
    r = obter_consumo_chefe(FiltroArranjo.mononucleares, DadosFalsos(), "SP")
    faixa = {f.faixa: f for f in r.faixas}["60 a 69"]
    assert (faixa.domicilios_amostra, faixa.consumo_per_capita_kwh) == (1, 50.0)


# ---------- rotas ----------

@pytest.fixture
def cliente():
    app = criar_app()
    app.dependency_overrides[obter_dados] = DadosFalsos
    return TestClient(app)


@pytest.mark.parametrize(
    "caminho",
    ["/projecoes/serie?recorte=chefe_60_mais", "/projecoes?ano=2030&recorte=chefe_60_mais", "/arranjos",
     "/estrutura-etaria/consumo-chefe", "/simulador?ano=2030&faixa=60_69&arranjo=unipessoal&base=taxas"],
)
def test_rotas_aceitam_localidade_valida_e_recusam_invalida(cliente, caminho):
    sep = "&" if "?" in caminho else "?"
    r = cliente.get(f"{caminho}{sep}localidade=Centro-Oeste")
    assert r.status_code == 200 and r.json()["localidade"] == "Centro-Oeste"
    assert cliente.get(f"{caminho}{sep}localidade=Atlantida").status_code == 422


def test_sem_localidade_vale_o_brasil(cliente):
    assert cliente.get("/arranjos").json()["localidade"] == "Brasil"


def test_lista_regioes_e_estados(cliente):
    r = cliente.get("/localidades").json()
    assert r["padrao"] == "Brasil"
    regioes = {g["nome"]: g["estados"] for g in r["regioes"]}
    assert list(regioes) == ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    assert {"sigla": "DF", "nome": "Distrito Federal"} in regioes["Centro-Oeste"]
    assert sum(len(e) for e in regioes.values()) == 27
