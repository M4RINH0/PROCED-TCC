"""Valores esperados calculados à mão, indicados em cada teste."""

import pytest

from app.modules.projecoes.calculo import tbc, tbc_pd, tec


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
