"""Valores esperados calculados à mão, indicados em cada teste."""

import pytest

from app.calculo import (
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
