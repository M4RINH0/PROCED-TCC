"""Experimento de machine learning (etl/modelagem.py), fora do escopo das projeções e do site.

Os testes garantem que a avaliação citada no TCC continua reproduzível e que a reponderação com a
média da célula reproduz exatamente o método das taxas (a diferença entre os métodos vem só do modelo).
"""

import json

import numpy as np
import pandas as pd
import pytest

from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL
from etl import modelagem, projecao
from test.test_etl_projecao import C1, C2, _ponte


def test_soma_dos_pesos_ajustados_por_celula_e_o_alvo():
    fato, ponte = _ponte()
    um = np.ones(len(fato))
    r = modelagem.projetar_reponderacao(fato, um, um, ponte, "teste", [2050]).iloc[0]
    # previsão 1 em todo domicílio: o consumo total vira a soma dos pesos ajustados = 6 + 2
    assert r["consumo_total_kwh_mes"] == pytest.approx(8)
    assert r["domicilios_uni_60"] == pytest.approx(6) and r["domicilios_mul_59"] == pytest.approx(2)


def test_reponderacao_com_a_media_da_celula_reproduz_exatamente_o_metodo_das_taxas():
    fato, ponte = _ponte()
    total = np.array([ponte.consumo_domicilio[c] for c in fato["celula"]])
    per_capita = np.array([ponte.tec[c] for c in fato["celula"]])
    anos = [2018, 2026, 2050]
    r = modelagem.projetar_reponderacao(fato, total, per_capita, ponte, "taxas", anos)
    t = projecao.projetar_taxas(ponte, anos)
    pd.testing.assert_frame_equal(r, t, check_exact=False, rtol=1e-12)


# ---------- machine learning ----------


def _amostra(n=240, semente=0):
    """Amostra sintética com as 21 células e consumo crescente com moradores e idade."""
    rng = np.random.default_rng(semente)
    idades = rng.choice([25, 35, 45, 55, 65, 75, 85], size=n)
    moradores = rng.choice([1, 2, 3, 4, 5], size=n)
    arranjo = np.where(moradores == 1, UNIPESSOAL, np.where(moradores == 2, CASAL_OU_DUPLA, MULTIPESSOAL))
    consumo = 60 + 30 * moradores + 0.5 * idades + rng.gamma(2.0, 15.0, size=n)
    return pd.DataFrame(
        {
            "id_domicilio": np.arange(n),
            "sigla_uf": rng.choice(["DF", "SP", "BA"], size=n),
            "idade_chefe": idades,
            "arranjo_familiar": arranjo,
            "qtd_moradores": moradores,
            "consumo_total_kwh": consumo.round(),
            "peso_final": rng.uniform(100, 2000, size=n),
        }
    )


def test_pipeline_de_ml_e_deterministico_com_a_semente_fixa():
    fato, _ = projecao.preparar(_amostra())
    a = modelagem.avaliar(fato, repeticoes=2)
    b = modelagem.avaliar(fato, repeticoes=2)
    for nome in ("linha_de_base", "ml_rf", "ml_gb"):
        assert a[nome]["partes"] == b[nome]["partes"]
        assert a[nome]["importancia"] == b[nome]["importancia"]
    assert len(a["ml_rf"]["partes"]) == 5


def test_partes_sem_sobreposicao_e_codificador_ajustado_so_no_treino():
    # a UF "AP" aparece em um único domicílio: na parte em que ele é teste, o codificador não pode conhecê-la
    amostra = _amostra()
    amostra.loc[7, "sigla_uf"] = "AP"
    fato, _ = projecao.preparar(amostra)
    r = modelagem.avaliar(fato, modelos=("ml_gb",), repeticoes=1, detalhe=True)
    vistos = np.concatenate([d["teste"] for d in r["detalhes"]])
    assert sorted(vistos) == list(range(len(fato)))  # cada domicílio é teste exatamente uma vez
    posicao_ap = int(np.flatnonzero(fato["sigla_uf"].to_numpy() == "AP")[0])
    for d in r["detalhes"]:
        assert not set(d["treino"]) & set(d["teste"])
        categorias_uf = d["codificadores"]["ml_gb"].named_transformers_["categoricas"].categories_[1]
        assert ("AP" in categorias_uf) == (posicao_ap in d["treino"])


def test_linha_de_base_usa_so_a_media_do_treino():
    treino = pd.DataFrame({"celula": [C1, C1, C2]})
    base = modelagem.LinhaDeBase().ajustar(treino, np.array([100.0, 130.0, 300.0]), np.array([2.0, 1.0, 1.0]))
    teste = pd.DataFrame({"celula": [C1, C2, ("80+", UNIPESSOAL)]})
    # C1: (200 + 130) / 3 = 110; célula nova: média geral (200 + 130 + 300) / 4 = 157,5
    assert base.prever(teste).tolist() == pytest.approx([110, 300, 157.5])


def test_metricas_ponderadas_calculadas_a_mao():
    # erros 10 e -20 com pesos 3 e 1: MAE (30 + 20) / 4 = 12,5; RMSE raiz((300 + 400) / 4) = raiz(175)
    # média observada (3*100 + 200) / 4 = 125; SST 3*625 + 1*5625 = 7500; R² 1 - 700 / 7500
    m = modelagem.metricas(np.array([100.0, 200.0]), np.array([110.0, 180.0]), np.array([3.0, 1.0]))
    assert m["mae"] == pytest.approx(12.5)
    assert m["rmse"] == pytest.approx(175**0.5)
    assert m["r2"] == pytest.approx(1 - 700 / 7500)
    assert m["vies"] == pytest.approx((30 - 20) / 4)


def test_modelo_em_log_aplica_a_correcao_de_duan():
    fato, _ = projecao.preparar(_amostra())
    y, w = fato["consumo_total_kwh"].to_numpy(float), fato["peso_final"].to_numpy(float)
    modelo = modelagem.ModeloLog("ml_gb").ajustar(fato, y, w)
    z = modelo.pipeline.predict(fato[list(modelagem.VARIAVEIS)])
    esperado = np.average(np.exp(np.log1p(y) - z), weights=w)
    assert modelo.smearing == pytest.approx(esperado)
    assert modelo.prever(fato) == pytest.approx(np.exp(z) * esperado - 1)


def test_modelo_desconhecido_e_modelo_sem_ajuste():
    with pytest.raises(ValueError):
        modelagem.criar_modelo("svm")
    with pytest.raises(ValueError):
        modelagem.ModeloLog("ml_rf").prever(pd.DataFrame())


def test_gravar_avaliacao_grava_as_duas_saidas_citadas_no_tcc(tmp_path):
    fato, _ = projecao.preparar(_amostra())
    avaliacao = modelagem.avaliar(fato, modelos=("linha_de_base", "ml_gb"), repeticoes=1)
    modelagem.gravar_avaliacao(avaliacao, tmp_path)
    metricas = json.loads((tmp_path / "metricas_modelos.json").read_text(encoding="utf-8"))
    assert set(metricas) >= {"linha_de_base", "ml_gb", "configuracao"}
    assert "random_state=42" in metricas["configuracao"]["validacao"]
    importancia = pd.read_csv(tmp_path / "importancia_variaveis.csv")
    assert set(importancia["modelo"]) == {"linha_de_base", "ml_gb"}
    assert set(importancia["variavel"]) == set(modelagem.VARIAVEIS)
