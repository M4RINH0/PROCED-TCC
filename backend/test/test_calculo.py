"""Valores esperados calculados à mão, indicados em cada teste."""

import pytest

import math

from app.calculo import (
    TAXAS_ARRANJOS_FIXOS,
    ajustar_envelhecimento,
    calibrar_intensidade,
    erro_medio_absoluto,
    estimar_tendencia,
    inclinacao,
    logs_razoes,
    projetar_proporcoes,
    proporcoes_arranjos,
    proporcoes_dos_logs,
    validar_tendencia,
    CONTRAFACTUAL,
    TAXAS,
    Celula,
    Projecao,
    congelar_composicao,
    fator_calibracao,
    parametros_celulas,
    consumo_por_pessoa,
    consumo_total,
    domicilios_projetados,
    media_ponderada,
    moradores_projetados,
    reponderar,
    taxas_chefia,
    tbc,
    tbc_pd,
    tec,
)


def test_tec_divide_consumo_pelos_domicilios():
    # 1500 / 10 = 150
    assert tec(1500, 10) == pytest.approx(150.0)


def test_tec_com_consumo_zero():
    assert tec(0, 5) == 0


@pytest.mark.parametrize("dom", [0, -3])
def test_tec_rejeita_domicilios_nao_positivos(dom):
    with pytest.raises(ValueError):
        tec(100, dom)


def test_tec_rejeita_consumo_negativo():
    with pytest.raises(ValueError):
        tec(-1, 10)


def test_tbc_divide_consumo_total_pelos_domicilios():
    # 4200 / 30 = 140
    assert tbc(4200, 30) == pytest.approx(140.0)


def test_tbc_rejeita_domicilios_zero():
    with pytest.raises(ValueError):
        tbc(100, 0)


def test_tbc_pd_media_ponderada_pelos_domicilios_do_cenario():
    # (100 * 3 + 200 * 1) / (3 + 1) = 500 / 4 = 125
    assert tbc_pd({"60 a 69": 100, "70 a 79": 200}, {"60 a 69": 3, "70 a 79": 1}) == pytest.approx(125.0)


def test_tbc_pd_com_tres_faixas():
    # (120 * 50 + 150 * 30 + 180 * 20) / 100 = (6000 + 4500 + 3600) / 100 = 141
    tecs = {"60 a 69": 120, "70 a 79": 150, "80+": 180}
    ndom = {"60 a 69": 50, "70 a 79": 30, "80+": 20}
    assert tbc_pd(tecs, ndom) == pytest.approx(141.0)


def test_tbc_pd_com_estrutura_uniforme_e_a_media_simples():
    # (90 + 110) / 2 = 100
    assert tbc_pd({"a": 90, "b": 110}, {"a": 7, "b": 7}) == pytest.approx(100.0)


def test_tbc_pd_faixa_com_zero_domicilios_nao_pesa():
    # (100 * 4 + 999 * 0) / 4 = 100
    assert tbc_pd({"a": 100, "b": 999}, {"a": 4, "b": 0}) == pytest.approx(100.0)


def test_tbc_pd_rejeita_faixas_diferentes():
    with pytest.raises(ValueError):
        tbc_pd({"a": 100}, {"b": 1})


def test_tbc_pd_rejeita_entrada_vazia():
    with pytest.raises(ValueError):
        tbc_pd({}, {})


def test_tbc_pd_rejeita_total_de_domicilios_zero():
    with pytest.raises(ValueError):
        tbc_pd({"a": 100, "b": 200}, {"a": 0, "b": 0})


def test_tbc_pd_rejeita_valores_negativos():
    with pytest.raises(ValueError):
        tbc_pd({"a": -1}, {"a": 1})
    with pytest.raises(ValueError):
        tbc_pd({"a": 1}, {"a": -1})


# ---------- conjunto mínimo calculado à mão ----------
# domicílio  célula               peso  consumo  moradores  per capita
#     A      (60 a 69, uni)          2      100          1         100
#     B      (60 a 69, uni)          1      130          1         130
#     C      (30 a 39, multi)        3      300          3         100
#     D      (30 a 39, multi)        1      200          4          50
# c1 = (60 a 69, uni):   soma dos pesos 3, TEC (2*100 + 130) / 3 = 110, consumo por domicílio 110, moradores 1
# c2 = (30 a 39, multi): soma dos pesos 4, TEC (3*100 + 50) / 4 = 87,5,
#                        consumo por domicílio (900 + 200) / 4 = 275, moradores (9 + 4) / 4 = 3,25
# população: 2018 -> 300 (60 a 69) e 400 (30 a 39); 2050 -> 600 e 200
C1, C2 = ("60 a 69", "uni"), ("30 a 39", "multi")
PESOS = [2, 1, 3, 1]
CELULAS = [C1, C1, C2, C2]
PER_CAPITA = [100, 130, 100, 50]
POP_2018 = {"60 a 69": 300, "30 a 39": 400}
POP_2050 = {"60 a 69": 600, "30 a 39": 200}
TEC = {C1: 110.0, C2: 87.5}
CONSUMO_DOMICILIO = {C1: 110.0, C2: 275.0}
MORADORES = {C1: 1.0, C2: 3.25}


def test_media_ponderada_da_tec_de_cada_celula():
    assert media_ponderada([100, 130], [2, 1]) == pytest.approx(110.0)
    assert media_ponderada([100, 50], [3, 1]) == pytest.approx(87.5)


def test_tbc_ponderada_sem_distinguir_faixa():
    # (2*100 + 130 + 3*100 + 50) / 7 = 680 / 7
    assert media_ponderada(PER_CAPITA, PESOS) == pytest.approx(680 / 7)


def test_media_com_peso_um_e_a_media_simples():
    assert media_ponderada([1, 2, 6], [1, 1, 1]) == pytest.approx(3.0)


def test_media_ponderada_rejeita_entradas_invalidas():
    with pytest.raises(ValueError):
        media_ponderada([1, 2], [1])
    with pytest.raises(ValueError):
        media_ponderada([1], [-1])
    with pytest.raises(ValueError):
        media_ponderada([1, 2], [0, 0])


def test_tec_com_somas_ponderadas():
    # soma(peso * per capita) = 330, soma(peso) = 3
    assert tec(330, 3) == pytest.approx(110.0)


def test_taxa_de_chefia_vezes_populacao_de_2018_reproduz_a_soma_dos_pesos():
    chefia = taxas_chefia({C1: 3, C2: 4}, POP_2018)
    assert chefia == pytest.approx({C1: 0.01, C2: 0.01})
    assert domicilios_projetados(chefia, POP_2018) == pytest.approx({C1: 3, C2: 4})


def test_taxa_de_chefia_exige_populacao_da_faixa():
    with pytest.raises(ValueError, match="30 a 39"):
        taxas_chefia({C2: 4}, {"30 a 39": 0})
    with pytest.raises(ValueError):
        taxas_chefia({C1: -1}, POP_2018)


def test_domicilios_projetados_em_2050():
    # 0,01 * 600 = 6; 0,01 * 200 = 2
    assert domicilios_projetados({C1: 0.01, C2: 0.01}, POP_2050) == pytest.approx({C1: 6, C2: 2})


def test_domicilios_projetados_rejeitam_populacao_negativa():
    with pytest.raises(ValueError):
        domicilios_projetados({C1: 0.01}, {"60 a 69": -1})


def test_padronizacao_com_a_composicao_do_ano_base_reproduz_a_tbc_observada():
    # ndom de 2018 = 3 e 4, as próprias somas dos pesos: (110*3 + 87,5*4) / 7 = 680 / 7
    assert tbc_pd(TEC, {C1: 3, C2: 4}) == pytest.approx(media_ponderada(PER_CAPITA, PESOS))


def test_padronizacao_em_2050():
    # (110*6 + 87,5*2) / 8 = 835 / 8 = 104,375
    assert tbc_pd(TEC, {C1: 6, C2: 2}) == pytest.approx(104.375)


def test_consumo_total_e_domicilios_vezes_consumo_por_domicilio():
    # 6*110 + 2*275 = 1210
    assert consumo_total({C1: 6, C2: 2}, CONSUMO_DOMICILIO) == pytest.approx(1210.0)


def test_consumo_total_rejeita_celulas_diferentes_e_negativos():
    with pytest.raises(ValueError):
        consumo_total({C1: 6}, CONSUMO_DOMICILIO)
    with pytest.raises(ValueError):
        consumo_total({C1: -6, C2: 2}, CONSUMO_DOMICILIO)


def test_moradores_e_consumo_por_pessoa_em_2050():
    # moradores 6*1 + 2*3,25 = 12,5; consumo por pessoa 1210 / 12,5 = 96,8
    moradores = moradores_projetados({C1: 6, C2: 2}, MORADORES)
    assert moradores == pytest.approx(12.5)
    assert consumo_por_pessoa(1210, moradores) == pytest.approx(96.8)


def test_consumo_por_pessoa_rejeita_zero_moradores():
    with pytest.raises(ValueError):
        consumo_por_pessoa(100, 0)


def test_reponderacao_soma_o_alvo_em_cada_celula():
    # c1: 2 e 1 viram 4 e 2 (alvo 6); c2: 3 e 1 viram 1,5 e 0,5 (alvo 2)
    novos = reponderar(PESOS, CELULAS, {C1: 6, C2: 2})
    assert novos == pytest.approx([4, 2, 1.5, 0.5])
    assert sum(novos[:2]) == pytest.approx(6) and sum(novos[2:]) == pytest.approx(2)


def test_reponderacao_com_a_media_da_celula_reproduz_o_metodo_das_taxas():
    novos = reponderar(PESOS, CELULAS, {C1: 6, C2: 2})
    previsao = [CONSUMO_DOMICILIO[c] for c in CELULAS]
    esperado = consumo_total({C1: 6, C2: 2}, CONSUMO_DOMICILIO)
    assert sum(w * y for w, y in zip(novos, previsao)) == pytest.approx(esperado)


def test_reponderacao_rejeita_celula_sem_alvo_ou_sem_peso():
    with pytest.raises(ValueError, match="sem alvo"):
        reponderar(PESOS, CELULAS, {C1: 6})
    with pytest.raises(ValueError, match="sem peso"):
        reponderar([0, 0], [C1, C1], {C1: 5})
    with pytest.raises(ValueError):
        reponderar([1], [C1, C2], {C1: 1, C2: 1})


# ---------- projeção por células, contrafactual e calibração (P10 e P12) ----------
# Mesmo conjunto mínimo; população por faixa: 2026 -> 450 e 300; população total de 2050: 25.
# taxas 2050: ndom 6 e 2; consumo 1210; moradores 12,5; por pessoa 96,8; calibrado 96,8 * 25 = 2420
# contrafactual 2050: composição de 2026 (4,5 e 3, isto é 60% e 40%) com o total de 2050 (8): 4,8 e 3,2
#   consumo 4,8*110 + 3,2*275 = 1408; moradores 4,8 + 3,2*3,25 = 15,2; TBC (110*4,8 + 87,5*3,2) / 8 = 101
#   calibrado 1408 * 25 / 15,2


def _projecao(total=None):
    celulas = parametros_celulas(
        [(C1, 2, 100, 100, 1), (C1, 1, 130, 130, 1), (C2, 3, 300, 100, 3), (C2, 1, 200, 50, 4)]
    )
    pop = {2018: POP_2018, 2026: {"60 a 69": 450, "30 a 39": 300}, 2050: POP_2050}
    return Projecao(celulas, pop, 2018, 2026, total)


def test_parametros_das_celulas_sao_medias_ponderadas():
    celulas = _projecao().celulas
    assert celulas[C1] == Celula(amostra=2, peso=3, tec=110, consumo_domicilio=110, moradores=1)
    assert celulas[C2].amostra == 2 and celulas[C2].peso == 4
    assert celulas[C2].tec == pytest.approx(87.5) and celulas[C2].consumo_domicilio == pytest.approx(275)
    assert celulas[C2].moradores == pytest.approx(3.25)


def test_parametros_das_celulas_rejeitam_peso_nao_positivo():
    with pytest.raises(ValueError):
        parametros_celulas([(C1, 0, 100, 100, 1)])


def test_projecao_pelo_metodo_das_taxas_em_2050():
    r = _projecao({2050: 25}).resumo(2050)
    assert r.domicilios == pytest.approx(8) and r.consumo_total == pytest.approx(1210)
    assert r.tbc_padronizada == pytest.approx(104.375) and r.moradores == pytest.approx(12.5)
    assert r.consumo_por_pessoa == pytest.approx(96.8)
    assert r.consumo_total_calibrado == pytest.approx(2420)


def test_calibrado_e_consumo_por_pessoa_vezes_a_populacao():
    r = _projecao({2050: 25}).resumo(2050)
    assert r.consumo_total_calibrado == pytest.approx(r.consumo_por_pessoa * 25)


def test_contrafactual_congela_a_distribuicao_de_2026():
    p = _projecao({2050: 25})
    assert p.domicilios(2050, CONTRAFACTUAL) == pytest.approx({C1: 4.8, C2: 3.2})
    r = p.resumo(2050, CONTRAFACTUAL)
    assert r.consumo_total == pytest.approx(1408) and r.moradores == pytest.approx(15.2)
    assert r.tbc_padronizada == pytest.approx(101)
    assert r.consumo_total_calibrado == pytest.approx(1408 * 25 / 15.2)


def test_contrafactual_no_ano_base_e_igual_as_taxas():
    p = _projecao()
    assert p.domicilios(2026, CONTRAFACTUAL) == pytest.approx(p.domicilios(2026, TAXAS))


def test_recorte_usa_o_fator_de_todas_as_celulas():
    # só C1: consumo 6*110 = 660; fator 25 / 12,5 = 2 (moradores de todas as células) -> 1320
    r = _projecao({2050: 25}).resumo(2050, TAXAS, [C1])
    assert r.consumo_total == pytest.approx(660) and r.consumo_total_calibrado == pytest.approx(1320)
    assert r.tbc_padronizada == pytest.approx(110)


def test_sem_populacao_total_nao_calibra():
    assert _projecao().resumo(2050).consumo_total_calibrado is None


def test_recorte_sem_domicilios_fica_sem_resumo():
    assert _projecao().resumo(2050, TAXAS, [("80+", "uni")]) is None


def test_projecao_rejeita_cenario_e_ano_desconhecidos():
    with pytest.raises(ValueError):
        _projecao().domicilios(2050, "pde")
    with pytest.raises(KeyError):
        _projecao().domicilios(2040)


def test_projecao_exige_ano_de_referencia_e_celulas():
    with pytest.raises(ValueError, match="2018"):
        Projecao(_projecao().celulas, {2050: POP_2050}, 2018, 2026)
    with pytest.raises(ValueError):
        Projecao({}, {2018: POP_2018}, 2018, 2026)


def test_fator_de_calibracao():
    assert fator_calibracao(25, 12.5) == 2
    with pytest.raises(ValueError):
        fator_calibracao(25, 0)
    with pytest.raises(ValueError):
        fator_calibracao(-1, 10)


def test_congelar_composicao():
    assert congelar_composicao({"a": 3, "b": 1}, 8) == pytest.approx({"a": 6, "b": 2})
    with pytest.raises(ValueError):
        congelar_composicao({"a": 0}, 8)
    with pytest.raises(ValueError):
        congelar_composicao({"a": 1}, -1)



# ---------- tendência dos arranjos (P13) ----------
A = ("u", "c", "m")  # unipessoal, casal ou dupla, multipessoal


def test_proporcoes_ponderadas_excluem_os_fora_da_rede_geral():
    # faixa F: u peso 2, c peso 3, m peso 5 (e um m fora da rede, peso 90, que sai) -> 0,2, 0,3, 0,5
    registros = [("F", "u", 2, True), ("F", "c", 3, True), ("F", "m", 5, True), ("F", "m", 90, False), ("G", "u", 1, True)]
    props = proporcoes_arranjos(registros)
    assert props["F"] == pytest.approx({"u": 0.2, "c": 0.3, "m": 0.5})
    assert props["G"] == {"u": 1.0}


def test_proporcoes_rejeitam_peso_nao_positivo():
    with pytest.raises(ValueError):
        proporcoes_arranjos([("F", "u", 0, True)])


def test_logs_das_razoes():
    # log(0,2 / 0,5) e log(0,3 / 0,5)
    assert logs_razoes({"u": 0.2, "c": 0.3, "m": 0.5}, A) == pytest.approx((math.log(0.4), math.log(0.6)))
    assert logs_razoes({"u": 0.0, "c": 0.5, "m": 0.5}, A) is None


def test_proporcoes_dos_logs_invertem_os_logs_e_somam_1():
    props = proporcoes_dos_logs(math.log(0.4), math.log(0.6), A)
    assert props == pytest.approx({"u": 0.2, "c": 0.3, "m": 0.5})
    extremas = proporcoes_dos_logs(40.0, -40.0, A)
    assert sum(extremas.values()) == pytest.approx(1) and all(0 <= v <= 1 for v in extremas.values())


def test_inclinacao_de_minimos_quadrados():
    # t = 2002,5, 2008,5, 2017,5 (média 2009,5; desvios -7, -1, 8; soma dos quadrados 114)
    # y = 1, 2, 4 -> inclinação (-7*1 - 1*2 + 8*4) / 114 = 23 / 114
    assert inclinacao([(2002.5, 1), (2008.5, 2), (2017.5, 4)]) == pytest.approx(23 / 114)
    with pytest.raises(ValueError):
        inclinacao([(2002.5, 1), (2002.5, 2)])


def test_tendencia_nas_tres_edicoes():
    # u/m: 1/7, 0,25, 0,4; inclinação = soma(desvio * log) / 114
    props = {
        2002.5: {"F": {"u": 0.1, "c": 0.2, "m": 0.7}},
        2008.5: {"F": {"u": 0.15, "c": 0.25, "m": 0.6}},
        2017.5: {"F": {"u": 0.2, "c": 0.3, "m": 0.5}},
    }
    bu, bc = estimar_tendencia(props, A)["F"]
    assert bu == pytest.approx((-7 * math.log(1 / 7) - math.log(0.25) + 8 * math.log(0.4)) / 114)
    assert bc == pytest.approx((-7 * math.log(2 / 7) - math.log(0.25 / 0.6) + 8 * math.log(0.6)) / 114)
    assert bu > 0 and bc > 0  # unipessoal e casal crescem em relação ao multipessoal


def test_faixa_sem_duas_edicoes_validas_fica_sem_tendencia():
    props = {2002.5: {"F": {"u": 0.0, "c": 0.5, "m": 0.5}}, 2017.5: {"F": {"u": 0.2, "c": 0.3, "m": 0.5}}}
    assert estimar_tendencia(props, A) == {}


def test_projecao_das_proporcoes_soma_1_e_respeita_a_intensidade():
    base = {"u": 0.2, "c": 0.3, "m": 0.5}
    projetadas = projetar_proporcoes(base, (0.02, 0.01), 10, 1.0, A)
    # log razão = log razão da base + inclinação * 10
    assert logs_razoes(projetadas, A) == pytest.approx((math.log(0.4) + 0.2, math.log(0.6) + 0.1))
    assert sum(projetadas.values()) == pytest.approx(1)
    meia = projetar_proporcoes(base, (0.02, 0.01), 10, 0.5, A)
    assert logs_razoes(meia, A) == pytest.approx((math.log(0.4) + 0.1, math.log(0.6) + 0.05))
    assert projetar_proporcoes(base, (0.02, 0.01), 10, 0.0, A) == pytest.approx(base)


def test_projecao_muito_longa_fica_entre_0_e_1():
    projetadas = projetar_proporcoes({"u": 0.2, "c": 0.3, "m": 0.5}, (0.5, -0.5), 200, 1.5, A)
    assert sum(projetadas.values()) == pytest.approx(1) and all(0 <= v <= 1 for v in projetadas.values())


def test_sem_inclinacao_ou_com_arranjo_zerado_as_proporcoes_ficam():
    assert projetar_proporcoes({"u": 0.2, "c": 0.3, "m": 0.5}, None, 10, 1, A) == {"u": 0.2, "c": 0.3, "m": 0.5}
    assert projetar_proporcoes({"u": 0.0, "c": 0.5, "m": 0.5}, (0.1, 0.1), 10, 1, A) == {"u": 0.0, "c": 0.5, "m": 0.5}


def _linear(t):
    # logs exatamente lineares: u/m = -2 + 0,1 (t - 2002,5); c/m = -1 + 0,05 (t - 2002,5)
    return proporcoes_dos_logs(-2 + 0.1 * (t - 2002.5), -1 + 0.05 * (t - 2002.5), A)


def test_validacao_fora_do_tempo_com_tendencia_exata_tem_erro_zero():
    props = {t: {"F": _linear(t)} for t in (2002.5, 2008.5, 2017.5)}
    erros = validar_tendencia(props, A, (2002.5, 2008.5), 2017.5)
    assert erros["F"] == pytest.approx({"u": 0, "c": 0, "m": 0}, abs=1e-9)


def test_validacao_fora_do_tempo_mede_o_erro_em_pontos_percentuais():
    # o previsto para 2017,5 é o linear; o observado tem 2 pontos a mais de unipessoal e 2 a menos de multipessoal
    previsto = _linear(2017.5)
    observado = {"u": previsto["u"] + 0.02, "c": previsto["c"], "m": previsto["m"] - 0.02}
    props = {2002.5: {"F": _linear(2002.5)}, 2008.5: {"F": _linear(2008.5)}, 2017.5: {"F": observado}}
    erros = validar_tendencia(props, A, (2002.5, 2008.5), 2017.5)
    assert erros["F"] == pytest.approx({"u": -2.0, "c": 0.0, "m": 2.0})


def test_validacao_ancora_no_ultimo_ano_de_treino():
    # 2002 fora da reta: a inclinação muda, mas a previsão parte do valor observado em 2008,5
    props = {2002.5: {"F": _linear(2002.5)}, 2008.5: {"F": _linear(2008.5)}, 2017.5: {"F": _linear(2017.5)}}
    inclinacao_u = (math.log(_linear(2008.5)["u"] / _linear(2008.5)["m"]) - math.log(_linear(2002.5)["u"] / _linear(2002.5)["m"])) / 6
    assert inclinacao_u == pytest.approx(0.1)
    assert validar_tendencia(props, A, (2002.5, 2008.5), 2017.5)["F"]["u"] == pytest.approx(0, abs=1e-9)


# ---------- velocidade do envelhecimento (k) ----------
# 2026: A 60, B 40 (participações 0,6 e 0,4); 2050: A 80, B 120 (0,4 e 0,6; total 200)
POP_GRUPOS = {2018: {"A": 70, "B": 30}, 2026: {"A": 60, "B": 40}, 2050: {"A": 80, "B": 120}}


def test_k_igual_a_1_devolve_a_populacao_original():
    assert ajustar_envelhecimento(POP_GRUPOS, 1.0, 2026) == POP_GRUPOS


def test_k_meio_freia_o_envelhecimento():
    # A: 0,6 + 0,5 * (0,4 - 0,6) = 0,5 -> 100; B: 0,4 + 0,5 * 0,2 = 0,5 -> 100
    assert ajustar_envelhecimento(POP_GRUPOS, 0.5, 2026)[2050] == pytest.approx({"A": 100, "B": 100})


def test_k_acima_de_1_acelera_e_mantem_o_total():
    # A: 0,6 + 1,5 * (-0,2) = 0,3 -> 60; B: 0,4 + 1,5 * 0,2 = 0,7 -> 140
    ajustada = ajustar_envelhecimento(POP_GRUPOS, 1.5, 2026)
    assert ajustada[2050] == pytest.approx({"A": 60, "B": 140})
    assert sum(ajustada[2050].values()) == pytest.approx(200)
    assert ajustada[2018] == POP_GRUPOS[2018] and ajustada[2026] == pytest.approx(POP_GRUPOS[2026])


def test_k_tem_piso_em_zero_e_renormaliza():
    # k = 4: A = 0,6 + 4 * (-0,2) = -0,2 -> 0; B = 1,2 -> renormalizado para 1 -> 200
    assert ajustar_envelhecimento(POP_GRUPOS, 4.0, 2026)[2050] == pytest.approx({"A": 0, "B": 200})


def test_k_rejeita_valor_nao_positivo_e_falta_do_ano_base():
    with pytest.raises(ValueError):
        ajustar_envelhecimento(POP_GRUPOS, 0, 2026)
    with pytest.raises(ValueError, match="2030"):
        ajustar_envelhecimento(POP_GRUPOS, 1.2, 2030)


# ---------- projeção com a tendência ----------
# Faixa F: u peso 2 (TEC 100), c peso 3 (TEC 60), m peso 5 (TEC 40); chefia da faixa 10 / 100 = 0,1
# Faixa G (sem tendência): u peso 4 (TEC 80); chefia 4 / 40 = 0,1
# população: F 100 em 2018 e 2026, 200 em 2050; G 40 em 2018 e 2026, 120 em 2050


def _celulas_tendencia():
    return parametros_celulas(
        [(("F", "u"), 2, 100, 100, 1), (("F", "c"), 3, 120, 60, 2), (("F", "m"), 5, 160, 40, 4), (("G", "u"), 4, 80, 80, 1)]
    )


POP_T = {2018: {"F": 100, "G": 40}, 2026: {"F": 100, "G": 40}, 2050: {"F": 200, "G": 120}}


def _projecao_tendencia(intensidade=1.0, tendencia=None):
    tendencia = {"F": (0.02, 0.01)} if tendencia is None else tendencia
    return Projecao(_celulas_tendencia(), POP_T, 2018, 2026, None, tendencia, intensidade, A)


def test_intensidade_zero_reproduz_o_modelo_sem_tendencia():
    sem = Projecao(_celulas_tendencia(), POP_T, 2018, 2026)
    zero = _projecao_tendencia(0.0)
    for ano in (2026, 2050):
        assert zero.domicilios(ano) == pytest.approx(sem.domicilios(ano))
        assert zero.domicilios(ano, TAXAS_ARRANJOS_FIXOS) == pytest.approx(sem.domicilios(ano))
    # sem tendência: 2050 = 0,1 * 200 * (0,2, 0,3, 0,5) = 4, 6, 10 e 0,1 * 120 = 12
    assert sem.domicilios(2050) == pytest.approx({("F", "u"): 4, ("F", "c"): 6, ("F", "m"): 10, ("G", "u"): 12})


def test_chefia_total_da_faixa_fica_constante_com_a_tendencia():
    p = _projecao_tendencia(1.5)
    ndom = p.domicilios(2050)
    assert ndom[("F", "u")] + ndom[("F", "c")] + ndom[("F", "m")] == pytest.approx(0.1 * 200)
    assert ndom[("G", "u")] == pytest.approx(12)


def test_taxas_usa_as_proporcoes_do_ano_e_arranjos_fixos_as_de_2026():
    p = _projecao_tendencia()
    base = {"u": 0.2, "c": 0.3, "m": 0.5}
    em_2050 = projetar_proporcoes(base, (0.02, 0.01), 2050 - 2017.5, 1.0, A)
    em_2026 = projetar_proporcoes(base, (0.02, 0.01), 2026 - 2017.5, 1.0, A)
    assert p.domicilios(2050)[("F", "u")] == pytest.approx(20 * em_2050["u"])
    assert p.domicilios(2050, TAXAS_ARRANJOS_FIXOS)[("F", "u")] == pytest.approx(20 * em_2026["u"])


def test_os_tres_cenarios_coincidem_no_ano_base():
    p = _projecao_tendencia()
    for cenario in (TAXAS_ARRANJOS_FIXOS, CONTRAFACTUAL):
        assert p.domicilios(2026, cenario) == pytest.approx(p.domicilios(2026, TAXAS))


def test_contrafactual_congela_a_composicao_de_taxas_em_2026():
    p = _projecao_tendencia()
    base = p.domicilios(2026)
    total_2050 = sum(p.domicilios(2050).values())
    esperado = {c: n / sum(base.values()) * total_2050 for c, n in base.items()}
    assert p.domicilios(2050, CONTRAFACTUAL) == pytest.approx(esperado)


def test_decomposicao_fecha():
    p = _projecao_tendencia()
    t, f, c = (p.resumo(2050, x).tbc_padronizada for x in (TAXAS, TAXAS_ARRANJOS_FIXOS, CONTRAFACTUAL))
    assert (f - c) + (t - f) == pytest.approx(t - c)
    assert t > f  # mais unipessoais, que consomem mais por pessoa, elevam a TBC


def test_verificacao_com_arranjos_congelados_a_tbc_cresce_com_o_envelhecimento():
    # jovens (TEC 50) e idosos (TEC 100), uma célula cada; a população idosa cresce
    celulas = parametros_celulas([(("jovem", "u"), 1, 50, 50, 1), (("idoso", "u"), 1, 100, 100, 1)])
    pop = {2018: {"jovem": 100, "idoso": 100}, 2026: {"jovem": 100, "idoso": 100}, 2070: {"jovem": 80, "idoso": 160}}
    p = Projecao(celulas, pop, 2018, 2026, None, {}, 0.0, A)
    # 2026: (50 + 100) / 2 = 75; 2070: (50 * 0,8 + 100 * 1,6) / 2,4 = 200 / 2,4
    assert p.resumo(2026, TAXAS_ARRANJOS_FIXOS).tbc_padronizada == pytest.approx(75)
    assert p.resumo(2070, TAXAS_ARRANJOS_FIXOS).tbc_padronizada == pytest.approx(200 / 2.4)


def test_projecao_rejeita_intensidade_negativa_e_tendencia_sem_rotulos():
    with pytest.raises(ValueError):
        _projecao_tendencia(-0.1)
    with pytest.raises(ValueError, match="rótulos"):
        Projecao(_celulas_tendencia(), POP_T, 2018, 2026, None, {"F": (0.1, 0.1)})


# ---------- intensidade padrão até 2026 e controle só depois (P13) ----------


def _projecao_calibrada(intensidade):
    return Projecao(_celulas_tendencia(), POP_T, 2018, 2026, None, {"F": (0.02, 0.01)}, intensidade, A, intensidade_ate_base=0.6)


@pytest.mark.parametrize("intensidade", [i / 10 for i in range(0, 16)])
def test_todas_as_intensidades_e_cenarios_partem_do_mesmo_valor_em_2026(intensidade):
    referencia = _projecao_calibrada(0.6).domicilios(2026)
    p = _projecao_calibrada(intensidade)
    for cenario in (TAXAS, TAXAS_ARRANJOS_FIXOS, CONTRAFACTUAL):
        assert p.domicilios(2026, cenario) == pytest.approx(referencia)
    assert p.resumo(2026, TAXAS).tbc_padronizada == pytest.approx(_projecao_calibrada(0.6).resumo(2026).tbc_padronizada)


def test_intensidade_so_age_depois_de_2026():
    # 2050: anos de tendência = 0,6 * (2026 - 2017,5) + intensidade * (2050 - 2026)
    for intensidade in (0.0, 0.5, 1.5):
        p = _projecao_calibrada(intensidade)
        assert p.anos_de_tendencia(2050) == pytest.approx(0.6 * 8.5 + intensidade * 24)
        assert p.anos_de_tendencia(2020) == pytest.approx(0.6 * 2.5)
    esperado = projetar_proporcoes({"u": 0.2, "c": 0.3, "m": 0.5}, (0.02, 0.01), 0.6 * 8.5 + 1.5 * 24, 1.0, A)
    assert _projecao_calibrada(1.5).domicilios(2050)[("F", "u")] == pytest.approx(20 * esperado["u"])


def test_intensidade_zero_congela_os_arranjos_de_2026_em_diante():
    p = _projecao_calibrada(0.0)
    assert p.proporcoes(2050)["F"] == pytest.approx(p.proporcoes(2026)["F"])
    assert p.domicilios(2050, TAXAS) == pytest.approx(p.domicilios(2050, TAXAS_ARRANJOS_FIXOS))


def test_erro_medio_absoluto_ponderado_pela_faixa():
    # F (peso 3): erros 1, -2, 1 -> média 4/3; G (peso 1): erros 3, -3, 0 -> média 2
    # (3 * 4 + 1 * 6) / (3 * 3 + 1 * 3) = 18 / 12 = 1,5
    erros = {"F": {"u": 1, "c": -2, "m": 1}, "G": {"u": 3, "c": -3, "m": 0}}
    assert erro_medio_absoluto(erros, {"F": 3, "G": 1}) == pytest.approx(1.5)
    with pytest.raises(ValueError):
        erro_medio_absoluto(erros, {})


def test_calibracao_acha_a_intensidade_que_reproduz_a_tendencia():
    # 2017,5 observado exatamente na reta com metade da inclinação de 2002 a 2008: o ótimo é 0,5
    def ponto(t, fator=1.0):
        return proporcoes_dos_logs(-2 + 0.1 * fator * (t - 2002.5), -1 + 0.05 * fator * (t - 2002.5), A)

    ancora = ponto(2008.5)
    alvo = projetar_proporcoes(ancora, (0.1, 0.05), 9, 0.5, A)
    props = {2002.5: {"F": ponto(2002.5)}, 2008.5: {"F": ancora}, 2017.5: {"F": alvo}}
    melhor, curva = calibrar_intensidade(props, A, (2002.5, 2008.5), 2017.5, {"F": 1}, [i / 10 for i in range(16)])
    assert melhor == 0.5 and curva[0.5] == pytest.approx(0, abs=1e-9)
    assert curva[0.0] > curva[0.3] > curva[0.5] < curva[0.7] < curva[1.0]


def test_participacao_do_recorte_no_consumo_de_todos_os_domicilios():
    # 2050: consumo de C1 = 6 * 110 = 660; de todas as células = 1210 -> 660 / 1210
    p = _projecao({2050: 25})
    assert p.resumo(2050, TAXAS, [C1]).participacao_consumo == pytest.approx(660 / 1210)
    assert p.resumo(2050).participacao_consumo == pytest.approx(1.0)
    # com o fator de calibração (2), a participação é a mesma: 1320 / 2420
    r = p.resumo(2050, TAXAS, [C1])
    assert r.consumo_total_calibrado / p.resumo(2050).consumo_total_calibrado == pytest.approx(r.participacao_consumo)


# ---------- fórmulas que saíram do ETL ----------


def test_consumo_calibrado_usa_o_fator_unico_da_p12():
    from app.calculo import consumo_calibrado

    # fator = 1.000 pessoas / 800 moradores = 1,25; 400 kWh * 1,25 = 500
    assert consumo_calibrado(400, 1000, 800) == pytest.approx(500)
    with pytest.raises(ValueError):
        consumo_calibrado(400, 1000, 0)


def test_diferenca_percentual_calculada_a_mao():
    from app.calculo import diferenca_percentual

    # 1.022 moradores contra 1.000 pessoas: 2,2% acima; 950 contra 1.000: 5% abaixo
    assert diferenca_percentual(1022, 1000) == pytest.approx(2.2)
    assert diferenca_percentual(950, 1000) == pytest.approx(-5.0)
    with pytest.raises(ValueError):
        diferenca_percentual(1, 0)


def test_fator_de_cobertura_da_p9():
    from app.calculo import fator_cobertura

    # 68,9 milhões / 63,68 milhões = 1,0820
    assert fator_cobertura(63_680_000, 68_900_000) == pytest.approx(1.08197, rel=1e-5)
    for soma, total in ((0, 10), (10, 0), (-1, 10)):
        with pytest.raises(ValueError):
            fator_cobertura(soma, total)


@pytest.mark.parametrize(
    "ano, esperado",
    [
        # antes do ano-base vale só a intensidade até a base: 0,6 * (2020 - 2017,5) = 1,5
        (2020, 1.5),
        # no ano-base: 0,6 * 8,5 = 5,1
        (2026, 5.1),
        # depois: 5,1 + 1,2 * (2050 - 2026) = 5,1 + 28,8 = 33,9
        (2050, 33.9),
    ],
)
def test_anos_de_tendencia_por_trecho(ano, esperado):
    from app.calculo import anos_de_tendencia

    assert anos_de_tendencia(ano, 2026, 2017.5, 1.2, 0.6) == pytest.approx(esperado)
