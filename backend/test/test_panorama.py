import pytest

from app.dominio import CASAL_OU_DUPLA, FAIXAS_CHEFE, MULTIPESSOAL, UNIPESSOAL, FiltroArranjo, Recorte, populacao_da_faixa
from app.schemas.panorama import Cenario, CenarioId
from app.services.domicilios import EstruturaDomicilios
from app.services.estrutura_etaria import consumo_por_faixa
from app.services.panorama import (
    ParametrosRecorte,
    com_variacao,
    comparativos,
    obter_projecao,
    obter_serie,
    participacao_60_mais,
)
from test.dados_teste import DOMICILIOS, POPULACAO, RepositorioFalso


def _valores(resposta):
    return {c.id: c.valor for c in resposta.cenarios}


def test_parametros_do_recorte_60_mais():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.tec == {"60 a 69": 110.0, "70 a 79": 150.0, "80+": 200.0}
    assert p.chefia == pytest.approx({"60 a 69": 0.002, "70 a 79": 0.002, "80+": 0.004})


def test_tbc_ibge_no_ano_de_referencia():
    # ndom = 2, 1, 1 -> (110*2 + 150*1 + 200*1) / 4 = 570 / 4 = 142,5
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.tbc_ibge(2018) == pytest.approx(142.5)


def test_tbc_ibge_com_envelhecimento_em_2030():
    # ndom = 0,002*1000, 0,002*1000, 0,004*500 = 2, 2, 2 -> (220 + 300 + 400) / 6 = 153,333...
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.tbc_ibge(2030) == pytest.approx(920 / 6)


def test_tbc_ibge_nula_depois_de_2070_e_em_ano_sem_projecao():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.tbc_ibge(2070) is not None
    assert p.tbc_ibge(2040) is None  # ano ausente na tabela de população


def test_recorte_abaixo_de_60():
    # até 29: 80 (n=1, pop 2000); 30 a 39: sem mononuclear -> falha; o recorte exige dados em todas as faixas
    with pytest.raises(ValueError):
        ParametrosRecorte(Recorte.mononuclear_abaixo_60, DOMICILIOS, POPULACAO)


def test_exige_populacao_do_ano_de_referencia():
    with pytest.raises(ValueError, match="2018"):
        ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, {2030: POPULACAO[2030]})


def test_populacao_da_faixa_inclui_90_ou_mais_no_80_mais():
    assert populacao_da_faixa({79: 1, 80: 10, 90: 100}, FAIXAS_CHEFE[-1]) == 110


def test_obter_projecao_segue_o_contrato():
    r = obter_projecao(2030, Recorte.chefe_60_mais, RepositorioFalso())
    assert _valores(r) == {CenarioId.mod: None, CenarioId.ibge: 153.3, CenarioId.alt: None}
    assert r.dados_ilustrativos is False
    assert "POF" in r.fonte


@pytest.mark.parametrize("ano", [2025, 2071])
def test_obter_projecao_rejeita_ano_fora_do_horizonte(ano):
    with pytest.raises(ValueError):
        obter_projecao(ano, Recorte.chefe_60_mais, RepositorioFalso())


def test_obter_serie_cobre_2026_a_2070():
    s = obter_serie(Recorte.chefe_60_mais, RepositorioFalso())
    assert [p.ano for p in s.pontos] == list(range(2026, 2071))
    por_ano = {p.ano: _valores(p)[CenarioId.ibge] for p in s.pontos}
    assert por_ano[2030] == 153.3
    assert por_ano[2070] is not None
    assert max(por_ano) == 2070


def test_consumo_por_faixa_mononucleares():
    faixas = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.mononucleares)}
    assert [f for f in faixas] == ["até 29", "30 a 39", "40 a 49", "50 a 59", "60 a 69", "70 a 79", "80+"]
    assert faixas["60 a 69"].consumo_per_capita_kwh == 110.0 and faixas["60 a 69"].domicilios_amostra == 2
    assert faixas["30 a 39"].consumo_per_capita_kwh is None and faixas["30 a 39"].domicilios_amostra == 0


def test_consumo_por_faixa_filtra_arranjo():
    faixas = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.multipessoal)}
    assert faixas["70 a 79"].consumo_per_capita_kwh == 999.0
    assert faixas["30 a 39"].consumo_per_capita_kwh == 40.0
    todos = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.todos)}
    # 70 a 79: (150 + 999) / 2 = 574,5
    assert todos["70 a 79"].consumo_per_capita_kwh == 574.5


# --- série: variação e participação de 60+ ---



def test_participacao_60_mais():
    # 2030: total 9500, 60+ = 1000 + 1000 + 500 = 2500 -> 26,32%
    assert participacao_60_mais(POPULACAO[2030]) == 26.32
    assert participacao_60_mais({}) is None


def test_com_variacao_em_relacao_a_2026():
    base = [Cenario(id=CenarioId.ibge, valor=100.0), Cenario(id=CenarioId.mod, valor=None)]
    atual = [Cenario(id=CenarioId.ibge, valor=110.0), Cenario(id=CenarioId.mod, valor=None)]
    ibge, mod = com_variacao(atual, base)
    assert (ibge.variacao_kwh, ibge.variacao_pct) == (10.0, 10.0)
    assert mod.variacao_kwh is None and mod.variacao_pct is None


def test_serie_traz_participacao_60_mais_ate_2070():
    s = obter_serie(Recorte.chefe_60_mais, RepositorioFalso())
    por_ano = {p.ano: p.participacao_60_mais_pct for p in s.pontos}
    assert por_ano[2030] == 26.32
    assert por_ano[2040] is None  # ano ausente na tabela de teste


# --- estrutura de domicílios por faixa e arranjo ---

def test_estrutura_aplica_chefia_constante_por_arranjo():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    # (60 a 69, unipessoal): 1 / 1000 em 2018; 2030 tem 1000 -> 1,0
    # (80+, casal): 1 / 250 em 2018; 2030 tem 500 -> 2,0
    em_2030 = e.no_ano(2030)
    assert em_2030[("60 a 69", UNIPESSOAL)] == pytest.approx(1.0)
    assert em_2030[("80+", CASAL_OU_DUPLA)] == pytest.approx(2.0)
    assert e.amostra[("70 a 79", MULTIPESSOAL)] == 1


def test_estrutura_sem_projecao_depois_de_2070():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    assert e.no_ano(2040) is None


def test_tec_do_grupo_soma_as_faixas():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    # unipessoal 60+: 100 (62 anos) e 150 (75 anos) -> (100 + 150) / 2 = 125
    assert e.tec_do_grupo(["60 a 69", "70 a 79", "80+"], UNIPESSOAL) == (2, 125.0)
    assert e.tec_do_grupo(["50 a 59"], UNIPESSOAL) == (0, None)


def test_estrutura_exige_populacao_de_2018():
    with pytest.raises(ValueError):
        EstruturaDomicilios(DOMICILIOS, {2030: POPULACAO[2030]})


def test_comparativos_entre_cenarios():
    # mod 120, ibge 100, alt 90: amplitude 120 - 90 = 30; modelo menos oficial 120 - 100 = 20
    tres = [Cenario(id=CenarioId.mod, valor=120.0), Cenario(id=CenarioId.ibge, valor=100.0), Cenario(id=CenarioId.alt, valor=90.0)]
    assert comparativos(tres) == (30.0, 20.0)
    # só o oficial tem valor: sem amplitude nem diferença
    so_ibge = [Cenario(id=CenarioId.mod, valor=None), Cenario(id=CenarioId.ibge, valor=100.0)]
    assert comparativos(so_ibge) == (None, None)
