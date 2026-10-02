import pytest

from app.modules.projecoes.repository import RepositorioIlustrativo
from app.modules.projecoes.schemas import CenarioId, Recorte
from app.modules.projecoes.service import obter_projecao


class RepositorioFixo:
    """Devolve sempre o mesmo valor, inclusive para o IBGE depois de 2060."""

    dados_ilustrativos = False

    def valor(self, cenario, ano, recorte):
        return 100.04


def _valores(resposta):
    return {c.id: c.valor for c in resposta.cenarios}


def test_retorna_os_tres_cenarios_na_ordem_do_contrato():
    resposta = obter_projecao(2030, Recorte.chefe_60_mais, RepositorioFixo())
    assert [c.id for c in resposta.cenarios] == [CenarioId.mod, CenarioId.ibge, CenarioId.alt]
    assert resposta.unidade == "kWh/mes/pessoa"


def test_arredonda_para_uma_casa_decimal():
    assert _valores(obter_projecao(2030, Recorte.chefe_60_mais, RepositorioFixo()))[CenarioId.mod] == 100.0


def test_ibge_existe_em_2060():
    assert _valores(obter_projecao(2060, Recorte.chefe_60_mais, RepositorioFixo()))[CenarioId.ibge] == 100.0


@pytest.mark.parametrize("ano", [2061, 2075])
def test_ibge_e_null_depois_de_2060_mesmo_se_a_fonte_tiver_valor(ano):
    valores = _valores(obter_projecao(ano, Recorte.chefe_60_mais, RepositorioFixo()))
    assert valores[CenarioId.ibge] is None
    assert valores[CenarioId.mod] is not None


def test_propaga_a_marcacao_de_dados_ilustrativos():
    assert obter_projecao(2030, Recorte.chefe_60_mais, RepositorioFixo()).dados_ilustrativos is False
    assert obter_projecao(2030, Recorte.chefe_60_mais, RepositorioIlustrativo()).dados_ilustrativos is True


@pytest.mark.parametrize("ano", [2025, 2076])
def test_rejeita_ano_fora_do_horizonte(ano):
    with pytest.raises(ValueError):
        obter_projecao(ano, Recorte.chefe_60_mais, RepositorioFixo())


def test_repositorio_ilustrativo_reproduz_o_exemplo_do_contrato():
    # 2075: forma = 1, logo mod = 158,4 + 71,9 = 230,3 e alt = 159,2 + 103,1 = 262,3
    valores = _valores(obter_projecao(2075, Recorte.chefe_60_mais, RepositorioIlustrativo()))
    assert valores == {CenarioId.mod: 230.3, CenarioId.ibge: None, CenarioId.alt: 262.3}


def test_repositorio_ilustrativo_no_ano_inicial():
    # 2026: forma = 0; abaixo de 60 aplica fator 0,8: 158,4 * 0,8 = 126,72
    valores = _valores(obter_projecao(2026, Recorte.mononuclear_abaixo_60, RepositorioIlustrativo()))
    assert valores[CenarioId.mod] == 126.7
    assert valores[CenarioId.ibge] == pytest.approx(round(157.9 * 0.8, 1))
