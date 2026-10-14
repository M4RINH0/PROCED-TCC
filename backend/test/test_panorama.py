import random

import pytest

from app.calculo import CONTRAFACTUAL, TAXAS
from app.dados import Domicilio
from app.dominio import (
    CASAL_OU_DUPLA,
    FAIXAS_CHEFE,
    FAIXAS_DO_RECORTE,
    MULTIPESSOAL,
    UNIPESSOAL,
    FiltroArranjo,
    Recorte,
    da_faixa,
    filtrar,
    populacao_da_faixa,
)
from app.schemas.panorama import Cenario, CenarioId
from app.services.domicilios import EstruturaDomicilios
from app.services.estrutura_etaria import consumo_por_faixa
from app.services.panorama import (
    ParametrosRecorte,
    com_variacao,
    efeitos,
    obter_projecao,
    obter_serie,
    participacao_60_mais,
)
from test.dados_teste import DOMICILIOS, POPULACAO, RepositorioFalso

# Contas à mão com test/dados_teste.py (peso 1 e um morador por domicílio):
# chefia de 2018: (60 a 69, uni) 1/1000, (60 a 69, casal) 1/1000, (70 a 79, uni) 1/500, (70 a 79, multi) 1/500,
#                 (80+, casal) 1/250, (até 29, uni) 1/2000, (40 a 49, casal) 1/2000, (30 a 39, multi) 1/2000
# 2030: domicílios 1, 1, 2, 2, 2, 1, 1, 1 (total 11); população total 9500
# taxas, recorte 60+: TBC (100*1 + 120*1 + 150*2 + 200*2) / 6 = 920 / 6 = 153,33; consumo 920; moradores 6
#   calibrado = 920 * 9500 / 11 = 794.545,45
# contrafactual 2030: composição de 2026 (= 2018: um domicílio por célula, total 8) com o total de 2030 (11)
#   cada célula 11 / 8 = 1,375; TBC (100 + 120 + 150 + 200) / 4 = 142,5; consumo 570 * 1,375 = 783,75
#   calibrado = 783,75 * 9500 / 11 = 676.875
# efeito do envelhecimento: 153,3 menos 142,5 = 10,8 kWh; 794.545 menos 676.875 = 117.670 kWh/mês


def _valores(resposta):
    return {c.id: c.valor for c in resposta.cenarios}


def test_taxas_e_contrafactual_do_recorte_60_mais_em_2030():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    t, c = p.resumo(2030, TAXAS), p.resumo(2030, CONTRAFACTUAL)
    assert t.tbc_padronizada == pytest.approx(920 / 6)
    assert t.consumo_total == pytest.approx(920) and t.moradores == pytest.approx(6)
    assert t.consumo_por_pessoa == pytest.approx(920 / 6)
    assert t.consumo_total_calibrado == pytest.approx(920 * 9500 / 11)
    assert c.tbc_padronizada == pytest.approx(142.5)
    assert c.consumo_total == pytest.approx(783.75)
    assert c.consumo_total_calibrado == pytest.approx(676875)


def test_no_ano_base_o_contrafactual_e_igual_as_taxas():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.resumo(2026, CONTRAFACTUAL) == p.resumo(2026, TAXAS)


def test_tbc_no_ano_de_referencia():
    # ndom = amostra: (100 + 120 + 150 + 200) / 4 = 142,5
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.resumo(2018).tbc_padronizada == pytest.approx(142.5)


def test_parametros_usam_o_peso_amostral():
    # 60 a 69: peso 3 com 100 kWh (uni) e peso 1 com 200 kWh (casal) -> TEC da faixa (300 + 200) / 4 = 125
    # 70 a 79: peso 2 com 150 kWh; 80+: peso 1 com 200 kWh
    # 2030: chefia 3/1000, 1/1000, 2/500, 1/250 -> ndom 3, 1, 4, 2 -> (300 + 200 + 600 + 400) / 10 = 150
    domicilios = [
        Domicilio(UNIPESSOAL, 62, 100.0, peso=3.0),
        Domicilio(CASAL_OU_DUPLA, 68, 200.0, peso=1.0),
        Domicilio(UNIPESSOAL, 75, 150.0, peso=2.0),
        Domicilio(UNIPESSOAL, 85, 200.0, peso=1.0),
        Domicilio(MULTIPESSOAL, 65, 999.0, peso=50.0),  # fora do recorte mononuclear
    ]
    p = ParametrosRecorte(Recorte.chefe_60_mais, domicilios, POPULACAO)
    assert p.amostra == 4
    assert p.resumo(2030).tbc_padronizada == pytest.approx(150.0)


def test_amostra_por_celula_marca_baixa_confiabilidade():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    amostra = p.amostra_resposta()
    celulas = {(c.faixa, c.arranjo): c for c in amostra.celulas}
    assert len(celulas) == 6  # 3 faixas x 2 arranjos mononucleares
    assert celulas[("60 a 69", UNIPESSOAL)].domicilios_amostra == 1
    assert celulas[("80+", UNIPESSOAL)].domicilios_amostra == 0
    assert all(c.baixa_confiabilidade for c in amostra.celulas)
    assert amostra.baixa_confiabilidade is True and amostra.domicilios_amostra == 4


def test_amostra_com_30_ou_mais_domicilios_nao_tem_aviso():
    domicilios = [Domicilio(a, idade, 100.0) for idade in (65, 75, 85) for a in (UNIPESSOAL, CASAL_OU_DUPLA) for _ in range(30)]
    amostra = ParametrosRecorte(Recorte.chefe_60_mais, domicilios, POPULACAO).amostra_resposta()
    assert amostra.baixa_confiabilidade is False
    assert all(c.domicilios_amostra == 30 and not c.baixa_confiabilidade for c in amostra.celulas)


def test_recorte_com_faixa_sem_amostra_fica_sem_valor():
    # abaixo de 60: até 29 tem 1 domicílio, 40 a 49 tem 1; 30 a 39 e 50 a 59 não têm nenhum mononuclear.
    p = ParametrosRecorte(Recorte.mononuclear_abaixo_60, DOMICILIOS, POPULACAO)
    assert p.completo is False and p.amostra == 2
    assert p.resumo(2030) is None


def test_ano_sem_projecao_fica_sem_valor():
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, POPULACAO)
    assert p.resumo(2040) is None


def test_contrafactual_sem_o_ano_base_fica_sem_valor():
    sem_2026 = {a: v for a, v in POPULACAO.items() if a != 2026}
    p = ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, sem_2026)
    assert p.resumo(2030, CONTRAFACTUAL) is None and p.resumo(2030, TAXAS) is not None


def test_exige_populacao_do_ano_de_referencia():
    with pytest.raises(ValueError, match="2018"):
        ParametrosRecorte(Recorte.chefe_60_mais, DOMICILIOS, {2030: POPULACAO[2030]})


def test_populacao_da_faixa_inclui_90_ou_mais_no_80_mais():
    assert populacao_da_faixa({79: 1, 80: 10, 90: 100}, FAIXAS_CHEFE[-1]) == 110


def test_obter_projecao_segue_o_contrato():
    r = obter_projecao(2030, Recorte.chefe_60_mais, RepositorioFalso())
    # sem as POFs anteriores não há tendência: taxas e taxas_arranjos_fixos coincidem
    assert _valores(r) == {
        CenarioId.taxas: 153.3,
        CenarioId.taxas_arranjos_fixos: 153.3,
        CenarioId.ml_rf: None,
        CenarioId.ml_gb: None,
        CenarioId.contrafactual: 142.5,
    }
    taxas = r.cenarios[0]
    assert taxas.consumo_por_pessoa_kwh == 153.3 and taxas.consumo_total_calibrado_kwh_mes == 794545
    assert {c.id: c for c in r.cenarios}[CenarioId.contrafactual].consumo_total_calibrado_kwh_mes == 676875
    assert r.efeito_envelhecimento_kwh == 10.8 and r.efeito_envelhecimento_total_kwh_mes == 117670
    # sem tendência, todo o efeito é da idade
    assert (r.efeito_idade_kwh, r.efeito_arranjos_kwh) == (10.8, 0.0)
    assert r.simulacao is False and (r.intensidade, r.k) == (1.0, 1.0)
    assert r.dados_ilustrativos is False and r.baixa_confiabilidade is True
    assert "POF" in r.fonte and "oficial" not in r.fonte


@pytest.mark.parametrize("ano", [2025, 2071])
def test_obter_projecao_rejeita_ano_fora_do_horizonte(ano):
    with pytest.raises(ValueError):
        obter_projecao(ano, Recorte.chefe_60_mais, RepositorioFalso())


def test_obter_serie_cobre_2026_a_2070():
    s = obter_serie(Recorte.chefe_60_mais, RepositorioFalso())
    assert [p.ano for p in s.pontos] == list(range(2026, 2071))
    por_ano = {p.ano: _valores(p)[CenarioId.taxas] for p in s.pontos}
    assert por_ano[2030] == 153.3 and por_ano[2026] == 142.5
    assert por_ano[2070] is not None
    assert all(_valores(p)[CenarioId.ml_rf] is None and _valores(p)[CenarioId.ml_gb] is None for p in s.pontos)


def test_serie_traz_variacao_e_efeito_do_envelhecimento():
    s = {p.ano: p for p in obter_serie(Recorte.chefe_60_mais, RepositorioFalso()).pontos}
    taxas = s[2030].cenarios[0]
    # 153,3 menos 142,5 (2026) = 10,8; 10,8 / 142,5 = 7,6%
    assert (taxas.variacao_kwh, taxas.variacao_pct) == (10.8, 7.6)
    assert s[2030].efeito_envelhecimento_kwh == 10.8
    assert s[2026].efeito_envelhecimento_kwh == 0.0
    assert s[2040].efeito_envelhecimento_kwh is None


def test_decomposicao_em_idade_e_arranjos():
    # taxas 110, arranjos fixos 104, contrafactual 100: idade 4, arranjos 6, envelhecimento 10
    cenarios = [
        Cenario(id=CenarioId.taxas, valor=110.0, consumo_total_calibrado_kwh_mes=1500),
        Cenario(id=CenarioId.taxas_arranjos_fixos, valor=104.0, consumo_total_calibrado_kwh_mes=1200),
        Cenario(id=CenarioId.contrafactual, valor=100.0, consumo_total_calibrado_kwh_mes=1000),
    ]
    e = efeitos(cenarios)
    assert (e.efeito_envelhecimento_kwh, e.efeito_idade_kwh, e.efeito_arranjos_kwh) == (10.0, 4.0, 6.0)
    assert (e.efeito_envelhecimento_total_kwh_mes, e.efeito_idade_total_kwh_mes, e.efeito_arranjos_total_kwh_mes) == (500, 200, 300)
    assert e.efeito_idade_kwh + e.efeito_arranjos_kwh == e.efeito_envelhecimento_kwh


def test_decomposicao_sem_um_dos_cenarios():
    so_taxas = [Cenario(id=CenarioId.taxas, valor=100.0), Cenario(id=CenarioId.contrafactual, valor=None)]
    e = efeitos(so_taxas)
    assert e.efeito_envelhecimento_kwh is None and e.efeito_idade_kwh is None and e.efeito_arranjos_kwh is None
    assert efeitos([]).efeito_envelhecimento_total_kwh_mes is None


def test_com_variacao_em_relacao_a_2026():
    base = [Cenario(id=CenarioId.taxas, valor=100.0), Cenario(id=CenarioId.ml_rf, valor=None)]
    atual = [Cenario(id=CenarioId.taxas, valor=110.0), Cenario(id=CenarioId.ml_rf, valor=None)]
    taxas, ml = com_variacao(atual, base)
    assert (taxas.variacao_kwh, taxas.variacao_pct) == (10.0, 10.0)
    assert ml.variacao_kwh is None and ml.variacao_pct is None


def test_participacao_60_mais():
    # 2030: total 9500, 60+ = 1000 + 1000 + 500 = 2500 -> 26,32%
    assert participacao_60_mais(POPULACAO[2030]) == 26.32
    assert participacao_60_mais({}) is None


def test_serie_traz_participacao_60_mais_ate_2070():
    s = obter_serie(Recorte.chefe_60_mais, RepositorioFalso())
    por_ano = {p.ano: p.participacao_60_mais_pct for p in s.pontos}
    assert por_ano[2030] == 26.32
    assert por_ano[2040] is None  # ano ausente na tabela de teste


# ---------- a troca de faixas para células (faixa, arranjo) não muda a série ----------


def _serie_por_faixa(recorte, domicilios, populacao, anos):
    """Cálculo anterior à troca (commit ef74e18): TEC e chefia por faixa, só com mononucleares."""
    mononucleares = filtrar(domicilios, FiltroArranjo.mononucleares)
    tec, chefia = {}, {}
    for faixa in FAIXAS_DO_RECORTE[recorte]:
        grupo = da_faixa(mononucleares, faixa)
        peso = sum(d.peso for d in grupo)
        tec[faixa.rotulo] = sum(d.peso * d.consumo_per_capita_kwh for d in grupo) / peso
        chefia[faixa.rotulo] = peso / populacao_da_faixa(populacao[2018], faixa)
    resultado = {}
    for ano in anos:
        ndom = {f.rotulo: chefia[f.rotulo] * populacao_da_faixa(populacao[ano], f) for f in FAIXAS_DO_RECORTE[recorte]}
        resultado[ano] = sum(tec[x] * ndom[x] for x in tec) / sum(ndom.values())
    return resultado


@pytest.mark.parametrize("recorte", [Recorte.chefe_60_mais, Recorte.mononuclear_abaixo_60])  # os recortes que existiam antes
@pytest.mark.parametrize("semente", [1, 2, 3])
def test_serie_por_celulas_igual_a_serie_por_faixas(recorte, semente):
    rng = random.Random(semente)
    domicilios = [
        Domicilio(
            rng.choice([UNIPESSOAL, CASAL_OU_DUPLA, MULTIPESSOAL]),
            rng.randint(14, 95),
            rng.uniform(20, 300),
            peso=rng.uniform(50, 3000),
        )
        for _ in range(400)
    ]
    anos = list(range(2026, 2071))
    populacao = {a: {i: rng.randint(1000, 90000) for i in range(0, 91)} for a in [2018, *anos]}
    antes = _serie_por_faixa(recorte, domicilios, populacao, anos)
    depois = ParametrosRecorte(recorte, domicilios, populacao)
    for ano in anos:
        assert depois.resumo(ano).tbc_padronizada == pytest.approx(antes[ano], rel=1e-12)


# ---------- consumo por faixa do chefe ----------


def test_consumo_por_faixa_mononucleares():
    faixas = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.mononucleares)}
    assert [f for f in faixas] == ["até 29", "30 a 39", "40 a 49", "50 a 59", "60 a 69", "70 a 79", "80+"]
    assert faixas["60 a 69"].consumo_per_capita_kwh == 110.0 and faixas["60 a 69"].domicilios_amostra == 2
    assert faixas["60 a 69"].baixa_confiabilidade is True
    assert faixas["30 a 39"].consumo_per_capita_kwh is None and faixas["30 a 39"].domicilios_amostra == 0


def test_consumo_por_faixa_filtra_arranjo():
    faixas = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.multipessoal)}
    assert faixas["70 a 79"].consumo_per_capita_kwh == 999.0
    assert faixas["30 a 39"].consumo_per_capita_kwh == 40.0
    todos = {f.faixa: f for f in consumo_por_faixa(DOMICILIOS, FiltroArranjo.todos)}
    # 70 a 79: (150 + 999) / 2 = 574,5
    assert todos["70 a 79"].consumo_per_capita_kwh == 574.5


def test_consumo_por_faixa_usa_o_peso():
    # 60 a 69: peso 3 com 100 kWh e peso 1 com 200 kWh -> (300 + 200) / 4 = 125
    domicilios = [Domicilio(UNIPESSOAL, 62, 100.0, peso=3.0), Domicilio(UNIPESSOAL, 66, 200.0, peso=1.0)]
    faixas = {f.faixa: f for f in consumo_por_faixa(domicilios, FiltroArranjo.unipessoal)}
    assert faixas["60 a 69"].consumo_per_capita_kwh == 125.0


def test_consumo_por_faixa_sem_aviso_com_30_domicilios():
    domicilios = [Domicilio(UNIPESSOAL, 62, 100.0)] * 30
    faixas = {f.faixa: f for f in consumo_por_faixa(domicilios, FiltroArranjo.unipessoal)}
    assert faixas["60 a 69"].baixa_confiabilidade is False


# ---------- estrutura de domicílios por faixa e arranjo ----------


def test_estrutura_aplica_chefia_constante_por_arranjo():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    # (60 a 69, unipessoal): 1 / 1000 em 2018; 2030 tem 1000 -> 1,0
    # (80+, casal): 1 / 250 em 2018; 2030 tem 500 -> 2,0
    em_2030 = e.no_ano(2030)
    assert em_2030[("60 a 69", UNIPESSOAL)] == pytest.approx(1.0)
    assert em_2030[("80+", CASAL_OU_DUPLA)] == pytest.approx(2.0)
    assert e.amostra[("70 a 79", MULTIPESSOAL)] == 1


def test_estrutura_sem_projecao_em_ano_ausente():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    assert e.no_ano(2040) is None


def test_tec_do_grupo_soma_as_faixas():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    # unipessoal 60+: 100 (62 anos) e 150 (75 anos) -> (100 + 150) / 2 = 125
    assert e.tec_do_grupo(["60 a 69", "70 a 79", "80+"], UNIPESSOAL) == (2, 125.0)
    assert e.tec_do_grupo(["50 a 59"], UNIPESSOAL) == (0, None)


def test_estrutura_marca_grupo_com_celula_pequena():
    e = EstruturaDomicilios(DOMICILIOS, POPULACAO)
    assert e.baixa_confiabilidade(["60 a 69", "70 a 79", "80+"], UNIPESSOAL) is True


def test_estrutura_exige_populacao_de_2018():
    with pytest.raises(ValueError):
        EstruturaDomicilios(DOMICILIOS, {2030: POPULACAO[2030]})
