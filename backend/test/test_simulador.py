import pytest
from fastapi.testclient import TestClient

from app.dados import Domicilio, obter_dados
from app.dominio import CASAL_OU_DUPLA as C
from app.dominio import UNIPESSOAL as U
from app.main import criar_app
from app.schemas.simulador import ArranjoSim, BaseSim, FaixaSim
from app.services.simulador import simular

# Peso 1 e um morador por domicílio.
# Unipessoal 70 a 79: 100 e 140 kWh -> TEC 120 com 2 domicílios; casal 70 a 79: 999; unipessoal 30 a 39: 50
# População: 2018 e 2026 -> 75 anos 1000, 35 anos 1000, 5 anos 3000; 2050 -> 2000, 500, 3000 (total 5500)
# chefia: (70 a 79, uni) 2/1000, (70 a 79, casal) 1/1000, (30 a 39, uni) 1/1000
# taxas 2050: domicílios 4, 2 e 0,5 (total 6,5); participação da célula 4 / 6,5 = 61,54%
#   consumo 4 * 120 = 480; calibrado 480 * 5500 / 6,5 = 406.153,85
# contrafactual 2050: composição de 2026 (2, 1, 1: metade, um quarto, um quarto) com o total de 6,5
#   célula 3,25 (50%); consumo 3,25 * 120 = 390; calibrado 390 * 5500 / 6,5 = 330.000
DOMICILIOS = [
    Domicilio(U, 72, 100.0),
    Domicilio(U, 78, 140.0),
    Domicilio(C, 72, 999.0),
    Domicilio(U, 35, 50.0),
]
POP_REF = {75: 1000, 35: 1000, 5: 3000}
POPULACAO = {2018: POP_REF, 2026: POP_REF, 2050: {75: 2000, 35: 500, 5: 3000}}


class RepositorioFalso:
    """Dados de teste com a persistência de cenários em memória, como a tabela cenario_salvo."""

    def __init__(self):
        self.cenarios = {}

    def domicilios(self):
        return DOMICILIOS

    def obter_cenario(self, parametros, versao_modelo):
        return self.cenarios.get((tuple(sorted(parametros.items())), versao_modelo))

    def salvar_cenario(self, parametros, versao_modelo, resultado):
        self.cenarios[(tuple(sorted(parametros.items())), versao_modelo)] = resultado

    def domicilios_historicos(self):
        return []  # sem as POFs anteriores não há tendência: os arranjos ficam congelados

    def populacao_por_idade(self, localidade="Brasil"):
        return POPULACAO


def _sim(ano=2050, faixa=FaixaSim.de_70_a_79, arranjo=ArranjoSim.unipessoal, base=BaseSim.taxas):
    return simular(ano, faixa, arranjo, base, RepositorioFalso())


def test_taxas_devolve_a_tec_e_os_domicilios_da_celula():
    r = _sim()
    assert (r.valor, r.domicilios_amostra, r.motivo_sem_valor) == (120.0, 2, None)
    assert r.faixa == "70 a 79" and r.baixa_confiabilidade is True
    assert r.domicilios_projetados == 4 and r.participacao_pct == 61.54
    assert r.consumo_total_calibrado_kwh_mes == 406154
    assert len(r.por_faixa) == 7


def test_contrafactual_congela_a_distribuicao_de_2026():
    r = _sim(base=BaseSim.contrafactual)
    assert r.valor == 120.0  # a TEC da célula é a mesma nos dois cenários (P6)
    assert r.participacao_pct == 50.0 and r.domicilios_projetados == 3  # 3,25 arredondado
    assert r.consumo_total_calibrado_kwh_mes == 330000


def test_combinacao_sem_amostra():
    r = _sim(faixa=FaixaSim.de_30_a_39, arranjo=ArranjoSim.casal_ou_dupla)
    assert r.valor is None and r.domicilios_amostra == 0 and "amostra" in r.motivo_sem_valor
    assert r.domicilios_projetados is None and r.consumo_total_calibrado_kwh_mes is None


def test_ano_sem_projecao_da_populacao():
    r = _sim(ano=2040)
    assert r.valor == 120.0 and r.domicilios_projetados is None and "projeção" in r.motivo_sem_valor


@pytest.fixture
def cliente():
    app = criar_app()
    repo = RepositorioFalso()
    app.dependency_overrides[obter_dados] = lambda: repo
    return TestClient(app)


PARAMS = {"ano": 2050, "faixa": "70_79", "arranjo": "unipessoal", "base": "taxas"}


def test_endpoint_entrada_valida(cliente):
    r = cliente.get("/simulador", params=PARAMS)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["valor"] == 120.0 and corpo["base"] == "taxas" and "taxa" not in corpo
    assert corpo["recuperado"] is False
    assert cliente.get("/simulador", params={**PARAMS, "base": "contrafactual"}).status_code == 200


def test_persiste_cenario_e_recupera_nas_consultas_seguintes(cliente):
    primeira = cliente.get("/simulador", params=PARAMS).json()
    segunda = cliente.get("/simulador", params=PARAMS).json()
    recalculada = cliente.get("/simulador", params={**PARAMS, "recalcular": True}).json()
    assert primeira["recuperado"] is False
    assert segunda["recuperado"] is True
    assert segunda["domicilios_projetados"] == primeira["domicilios_projetados"]
    assert recalculada["recuperado"] is False


@pytest.mark.parametrize(
    "campo, valor",
    [("ano", 2071), ("ano", 2025), ("faixa", "90_99"), ("arranjo", "familia"), ("base", "ibge"), ("base", "mod"), ("base", "ml_rf")],
)
def test_endpoint_entrada_invalida_retorna_422(cliente, campo, valor):
    assert cliente.get("/simulador", params={**PARAMS, campo: valor}).status_code == 422


def test_endpoint_parametro_ausente_retorna_422(cliente):
    params = dict(PARAMS)
    del params["faixa"]
    assert cliente.get("/simulador", params=params).status_code == 422


def test_arranjos_fixos_e_controles_de_simulacao():
    # sem as POFs anteriores não há tendência: taxas_arranjos_fixos coincide com taxas
    fixos = _sim(base=BaseSim.taxas_arranjos_fixos)
    assert fixos.participacao_pct == _sim().participacao_pct and fixos.simulacao is False
    r = simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, RepositorioFalso(), intensidade=0.5, k=1.2)
    assert (r.intensidade, r.k, r.simulacao) == (0.5, 1.2, True)


@pytest.mark.parametrize("campo, valor", [("intensidade", 2), ("k", 0.1)])
def test_endpoint_controle_fora_do_limite_retorna_422(cliente, campo, valor):
    assert cliente.get("/simulador", params={**PARAMS, campo: valor}).status_code == 422


def test_endpoint_aceita_os_controles(cliente):
    r = cliente.get("/simulador", params={**PARAMS, "base": "taxas_arranjos_fixos", "intensidade": 0.5, "k": 1.5})
    assert r.status_code == 200 and r.json()["simulacao"] is True


def test_cenario_salvo_com_a_versao_do_modelo_e_sem_o_campo_recuperado():
    from app.dominio import VERSAO_MODELO

    repo = RepositorioFalso()
    simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, repo)
    (chave, versao), = repo.cenarios.keys()
    assert versao == VERSAO_MODELO
    assert dict(chave) == {"ano": 2050, "faixa": "70_79", "arranjo": "unipessoal", "base": "taxas",
                           "localidade": "Brasil", "intensidade": 0.6, "k": 1.0}
    assert "recuperado" not in next(iter(repo.cenarios.values()))


def test_cenario_de_versao_antiga_e_recalculado(monkeypatch):
    import app.services.simulador as servico

    repo = RepositorioFalso()
    simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, repo)
    monkeypatch.setattr(servico, "VERSAO_MODELO", "versao-nova")
    r = simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, repo)
    assert r.recuperado is False
    # o cenário antigo continua na tabela, e o novo é gravado com a versão nova
    assert len(repo.cenarios) == 2 and "versao-nova" in {versao for _, versao in repo.cenarios}
    assert simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, repo).recuperado is True


def test_falha_do_banco_nao_impede_a_consulta():
    from app.config import ErroFonteDados

    class BancoFora(RepositorioFalso):
        def obter_cenario(self, parametros, versao_modelo):
            raise ErroFonteDados("fora do ar")

        def salvar_cenario(self, parametros, versao_modelo, resultado):
            raise ErroFonteDados("fora do ar")

    r = simular(2050, FaixaSim.de_70_a_79, ArranjoSim.unipessoal, BaseSim.taxas, BancoFora())
    assert r.valor == 120.0 and r.recuperado is False


def test_combinacao_sem_valor_nao_e_salva():
    repo = RepositorioFalso()
    simular(2050, FaixaSim.de_30_a_39, ArranjoSim.casal_ou_dupla, BaseSim.taxas, repo)
    assert repo.cenarios == {}
