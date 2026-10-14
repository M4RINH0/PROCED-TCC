import json

import numpy as np
import pandas as pd
import pytest

from app.calculo import media_ponderada
from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UFS, UNIPESSOAL
from etl import modelagem, pipeline

# ---------- conjunto mínimo calculado à mão ----------
# id  idade  arranjo  moradores  consumo  peso
#  1    65    uni         1        100      2
#  2    67    uni         1        130      1
#  3    35    multi       3        300      3
#  4    38    multi       4        200      1
#  4    33    multi       4        200      1    repetido: pela P8 fica a linha do chefe de 38 anos
# c1 = (60 a 69, uni): soma dos pesos 3, TEC 110, consumo por domicílio 110, moradores 1
# c2 = (30 a 39, multi): soma dos pesos 4, TEC 87,5, consumo por domicílio 275, moradores 3,25
MINIMO = pd.DataFrame(
    {
        "id_domicilio": [1, 2, 3, 4, 4],
        "sigla_uf": ["DF"] * 5,
        "idade_chefe": [65, 67, 35, 38, 33],
        "arranjo_familiar": [UNIPESSOAL, UNIPESSOAL, MULTIPESSOAL, MULTIPESSOAL, MULTIPESSOAL],
        "qtd_moradores": [1, 1, 3, 4, 4],
        "consumo_total_kwh": [100.0, 130.0, 300.0, 200.0, 200.0],
        "peso_final": [2.0, 1.0, 3.0, 1.0, 1.0],
    }
)
# população por idade: 2018 -> 300 (65 anos) e 400 (35 anos); 2026 -> 450 e 300; 2050 -> 600 e 200
POP = {2018: {65: 300, 35: 400}, 2026: {65: 450, 35: 300}, 2050: {65: 600, 35: 200}}
C1, C2 = ("60 a 69", UNIPESSOAL), ("30 a 39", MULTIPESSOAL)


def _ponte():
    fato, _ = modelagem.preparar(MINIMO)
    return fato, modelagem.Ponte(fato, modelagem.populacao_por_faixa(POP))


def test_preparar_aplica_p8_e_monta_as_celulas():
    fato, registro = modelagem.preparar(MINIMO)
    assert list(fato["id_domicilio"]) == [1, 2, 3, 4]
    assert fato.loc[fato["id_domicilio"] == 4, "idade_chefe"].item() == 38
    assert registro["linhas_removidas"] == 1 and registro["domicilios_repetidos"] == 1
    assert list(fato["celula"]) == [C1, C1, C2, C2]
    assert list(fato["consumo_per_capita_kwh"]) == [100, 130, 100, 50]


def test_preparar_rejeita_peso_ausente_ou_colunas_faltando():
    sem_peso = MINIMO.assign(peso_final=[1.0, np.nan, 1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="peso_final"):
        modelagem.preparar(sem_peso)
    with pytest.raises(ValueError, match="colunas ausentes"):
        modelagem.preparar(MINIMO.drop(columns="peso_final"))


def test_tabela_das_celulas_ponderada_e_com_aviso_de_amostra_pequena():
    fato, _ = modelagem.preparar(MINIMO)
    t = modelagem.tabela_celulas(fato).set_index(["faixa", "arranjo"])
    assert t.loc[C2, "domicilios_ponderados"] == 4 and t.loc[C2, "amostra"] == 2
    assert t.loc[C1, "consumo_per_capita_kwh"] == pytest.approx(110)
    assert t.loc[C2, "consumo_per_capita_kwh"] == pytest.approx(87.5)
    assert t.loc[C2, "consumo_domicilio_kwh"] == pytest.approx(275)
    assert t.loc[C2, "moradores"] == pytest.approx(3.25)
    assert t["baixa_amostra"].all()  # 2 domicílios por célula, menos de 30


def test_taxa_de_chefia_vezes_populacao_de_2018_reproduz_a_soma_dos_pesos_da_celula():
    _, ponte = _ponte()
    assert ponte.chefia == pytest.approx({C1: 0.01, C2: 0.01})
    assert ponte.domicilios(2018) == pytest.approx({C1: 3, C2: 4})


def test_metodo_das_taxas_em_2050():
    # ndom = 6 e 2; consumo 6*110 + 2*275 = 1210; TBC (110*6 + 87,5*2) / 8 = 104,375
    # moradores 6 + 2*3,25 = 12,5; consumo por pessoa 1210 / 12,5 = 96,8
    _, ponte = _ponte()
    linha = modelagem.projetar_taxas(ponte, [2050]).iloc[0]
    assert linha["domicilios"] == pytest.approx(8)
    assert linha["consumo_total_kwh_mes"] == pytest.approx(1210)
    assert linha["tbc_padronizada_kwh"] == pytest.approx(104.375)
    assert linha["moradores"] == pytest.approx(12.5)
    assert linha["consumo_por_pessoa_kwh"] == pytest.approx(96.8)
    assert linha["consumo_total_kwh_mes_uni_60"] == pytest.approx(660)
    assert linha["consumo_total_kwh_mes_mul_59"] == pytest.approx(550)
    assert linha["domicilios_cas_60"] == 0


def test_padronizacao_com_a_composicao_do_ano_base_reproduz_a_tbc_observada():
    fato, ponte = _ponte()
    linha = modelagem.projetar_taxas(ponte, [2018]).iloc[0]
    assert linha["tbc_padronizada_kwh"] == pytest.approx(media_ponderada(fato["consumo_per_capita_kwh"], fato["peso_final"]))


def test_contrafactual_congela_a_composicao_de_2026():
    # 2026: ndom 4,5 e 3 (60% e 40%); 2050: total 8 -> 4,8 e 3,2
    # TBC (110*0,6 + 87,5*0,4) = 101 em todos os anos; consumo 2050 = 4,8*110 + 3,2*275 = 1408
    _, ponte = _ponte()
    c = modelagem.projetar_contrafactual(ponte, [2026, 2050]).set_index("ano")
    assert c["tbc_padronizada_kwh"].tolist() == pytest.approx([101, 101])
    assert c.loc[2050, "domicilios"] == pytest.approx(8)
    assert c.loc[2050, "consumo_total_kwh_mes"] == pytest.approx(1408)
    assert (c["cenario"] == "contrafactual").all()


def test_contrafactual_e_igual_ao_metodo_das_taxas_no_ano_base():
    _, ponte = _ponte()
    t = modelagem.projetar_taxas(ponte, [2026]).drop(columns="cenario")
    c = modelagem.projetar_contrafactual(ponte, [2026]).drop(columns="cenario")
    pd.testing.assert_frame_equal(t, c)


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
    t = modelagem.projetar_taxas(ponte, anos)
    pd.testing.assert_frame_equal(r, t, check_exact=False, rtol=1e-12)


def test_validar_ponte_compara_com_censo_e_populacao():
    _, ponte = _ponte()
    v = modelagem.validar_ponte(ponte, POP, anos=(2026,))
    # 2026: ndom 4,5 e 3; moradores 4,5 + 3*3,25 = 14,25; população 750
    assert v["2026"]["domicilios_projetados"] == pytest.approx(7.5)
    assert v["2026"]["moradores_projetados"] == pytest.approx(14.25)
    assert v["2026"]["moradores_menos_populacao_pct"] == pytest.approx((14.25 / 750 - 1) * 100)


def test_validar_ponte_exige_2022_para_comparar_com_o_censo():
    _, ponte = _ponte()
    with pytest.raises(KeyError):
        modelagem.validar_ponte(ponte, POP)  # POP não tem 2022


def test_sensibilidade_multiplica_so_as_quantidades_e_fica_rotulada():
    _, ponte = _ponte()
    t = modelagem.projetar_taxas(ponte, [2050])
    s = modelagem.sensibilidade_cobertura(t, 2.0).iloc[0]
    assert s["analise"].startswith("sensibilidade")
    assert s["consumo_total_kwh_mes"] == pytest.approx(2420) and s["domicilios"] == pytest.approx(16)
    assert s["consumo_total_kwh_mes_uni_60"] == pytest.approx(1320)
    assert s["tbc_padronizada_kwh"] == pytest.approx(104.375)
    assert s["consumo_por_pessoa_kwh"] == pytest.approx(96.8)
    assert "analise" not in t.columns  # o resultado principal fica intocado


def test_calibracao_pela_populacao_do_ibge():
    # 2050: consumo 1210 e moradores 12,5; população 800 -> fator 64; calibrado 1210 * 64 = 96,8 * 800 = 77.440
    _, ponte = _ponte()
    c = modelagem.calibrar(modelagem.projetar_taxas(ponte, [2050]), POP).iloc[0]
    assert c["populacao_ibge"] == 800 and c["fator_calibracao"] == pytest.approx(64)
    assert c["consumo_total_calibrado_kwh_mes"] == pytest.approx(77440)
    assert c["consumo_total_calibrado_kwh_mes"] == pytest.approx(c["consumo_por_pessoa_kwh"] * 800)
    assert c["consumo_total_calibrado_kwh_mes_uni_60"] == pytest.approx(660 * 64)
    assert c["consumo_total_kwh_mes"] == pytest.approx(1210)  # o bruto continua, como diagnóstico
    assert c["moradores_menos_populacao_pct"] == pytest.approx((12.5 / 800 - 1) * 100)


def test_sensibilidade_nao_muda_o_calibrado_e_refaz_a_comparacao_com_a_populacao():
    _, ponte = _ponte()
    calibrado = modelagem.calibrar(modelagem.projetar_taxas(ponte, [2050]), POP)
    s = modelagem.sensibilidade_cobertura(calibrado, 2.0).iloc[0]
    assert s["consumo_total_calibrado_kwh_mes"] == pytest.approx(77440)
    assert s["moradores"] == pytest.approx(25) and s["fator_calibracao"] == pytest.approx(32)
    assert s["moradores_menos_populacao_pct"] == pytest.approx((25 / 800 - 1) * 100)


def test_fator_de_cobertura():
    fato, _ = modelagem.preparar(MINIMO)
    assert modelagem.fator_cobertura(fato, total=14) == pytest.approx(2.0)  # 14 / 7


def test_ponte_rejeita_fator_invalido_e_falta_de_2018():
    fato, _ = modelagem.preparar(MINIMO)
    with pytest.raises(ValueError):
        modelagem.Ponte(fato, modelagem.populacao_por_faixa(POP), fator=0)
    with pytest.raises(ValueError, match="2018"):
        modelagem.Ponte(fato, modelagem.populacao_por_faixa({2026: POP[2026]}))


# ---------- leitura ----------


# POFs anteriores, faixa de 60 a 69 (proporções por edição, todas na rede geral menos um registro):
# 2002: uni 1, multi 3 (25% e 75%); 2008: uni 2, multi 2 (50% e 50%); um casal de 2008 fora da rede geral sai
HISTORICA = pd.DataFrame(
    {
        "ano_pof": [2002, 2002, 2008, 2008, 2008],
        "id_domicilio": ["a", "b", "c", "d", "e"],
        "arranjo_familiar": [UNIPESSOAL, MULTIPESSOAL, UNIPESSOAL, MULTIPESSOAL, CASAL_OU_DUPLA],
        "idade_chefe": [65, 66, 67, 68, 69],
        "peso_final": [1.0, 3.0, 2.0, 2.0, 50.0],
        "energia_rede_geral": [True, True, True, True, False],
    }
)


class ClienteFalso:
    """Imita o Supabase: a projeção traz linhas de total (Brasil, região) e os três sexos."""

    def __init__(self, contagem_errada=False):
        self.contagem_errada = contagem_errada
        self.pop = [
            {"localidade": "DF", "sexo": "Ambos", "ano": 2018, "idade": 65, "populacao": 10},
            {"localidade": "GO", "sexo": "Ambos", "ano": 2018, "idade": 65, "populacao": 5},
        ]
        self.brasil = [{"localidade": "Brasil", "sexo": "Ambos", "ano": 2018, "idade": 65, "populacao": 15}]
        self.historica = HISTORICA.to_dict(orient="records")

    def selecionar(self, tabela, colunas, filtros=None):
        if tabela == "fato_consumo_domiciliar":
            return MINIMO.to_dict(orient="records")
        if tabela == "fato_consumo_pof_historica":
            return self.historica
        if filtros["localidade"] == "eq.Brasil":
            return self.brasil
        assert filtros["localidade"] == f"in.({','.join(UFS)})" and filtros["sexo"] == "eq.Ambos"
        return self.pop

    def contar(self, tabela, filtros=None):
        if tabela == "fato_consumo_domiciliar":
            return len(MINIMO) + (1 if self.contagem_errada else 0)
        if tabela == "fato_consumo_pof_historica":
            return len(HISTORICA)
        return 1 if filtros["localidade"] == "eq.Brasil" else 2


def test_carregar_le_as_ufs_e_confere_as_linhas_com_o_banco():
    fato, pop, brasil, leitura, historica = modelagem.carregar(ClienteFalso())
    assert len(fato) == 5 and pop == {2018: {65: 15}} and brasil == {2018: {65: 15}}
    assert all(n["lidas"] == n["no_banco"] for n in leitura.values())
    assert len(historica) == 5 and "fato_consumo_pof_historica" in leitura


def test_carregar_falha_se_faltar_linha():
    with pytest.raises(ValueError, match="5 de 6"):
        modelagem.carregar(ClienteFalso(contagem_errada=True))


def test_auditoria_conta_e_confere_as_ufs_com_o_brasil():
    fato_bruto, pop, brasil, leitura, historica = modelagem.carregar(ClienteFalso())
    fato, registro = modelagem.preparar(fato_bruto)
    a = modelagem.auditar(fato_bruto, fato, registro, pop, brasil, leitura)
    assert a["soma_das_ufs_confere_com_brasil"] is True
    assert a["p8_domicilios_repetidos"]["linhas_removidas"] == 1
    assert a["soma_dos_pesos"] == 7 and a["celulas_com_menos_de_30"] == 2
    assert a["chefes_com_menos_de_18_anos"] == 0 and a["domicilios_acima_de_1000_kwh"] == 0
    divergente = modelagem.auditar(fato_bruto, fato, registro, pop, {2018: {65: 16}}, leitura)
    assert divergente["soma_das_ufs_confere_com_brasil"] is False


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
    fato, _ = modelagem.preparar(_amostra())
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
    fato, _ = modelagem.preparar(amostra)
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
    fato, _ = modelagem.preparar(_amostra())
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


# ---------- saídas do pipeline ----------


def test_pipeline_gera_as_saidas_sem_ml(tmp_path):
    fato_bruto, pop, brasil, leitura, historica = modelagem.carregar(ClienteFalso())
    pop = {**POP}
    pop[2022] = {65: 400, 35: 350}
    pop.update({a: POP[2050] for a in range(2026, 2071)})
    resumo = pipeline.projetar(fato_bruto, pop, {2018: {65: 300, 35: 400}}, leitura, historica, tmp_path, avaliar_ml=False)
    projecoes = pd.read_csv(tmp_path / "projecoes_2026_2070.csv")
    assert set(projecoes["cenario"]) == {"taxas", "taxas_arranjos_fixos", "contrafactual"}
    assert (tmp_path / "tendencia_arranjos.json").exists()
    assert "consumo_total_calibrado_kwh_mes" in projecoes and "fator_calibracao" in projecoes
    assert projecoes["ano"].min() == 2026 and projecoes["ano"].max() == 2070
    sensibilidade = pd.read_csv(tmp_path / "sensibilidade_cobertura.csv")
    assert sensibilidade["analise"].str.startswith("sensibilidade").all()
    auditoria = json.loads((tmp_path / "auditoria.json").read_text(encoding="utf-8"))
    assert [r["etapa"] for r in auditoria["rastro"]][:2] == ["derivacao", "preparacao (P8)"]
    assert resumo["auditoria"]["linhas_depois_da_p8"] == 4



# ---------- tendência dos arranjos no ETL (P13) ----------


def test_tendencia_arranjos_resume_edicoes_inclinacoes_e_projecoes():
    # MINIMO (2017): 60 a 69 só tem unipessoais, então a faixa fica sem os três arranjos e sem tendência;
    # o resumo traz as proporções por edição mesmo assim
    fato, _ = modelagem.preparar(MINIMO)
    t = modelagem.tendencia_arranjos(HISTORICA, fato)
    assert t["proporcoes_por_edicao"]["2002.5"]["60 a 69"] == pytest.approx({UNIPESSOAL: 0.25, MULTIPESSOAL: 0.75})
    # o casal de 2008 está fora da rede geral e sai
    assert t["proporcoes_por_edicao"]["2008.5"]["60 a 69"] == pytest.approx({UNIPESSOAL: 0.5, MULTIPESSOAL: 0.5})
    assert t["inclinacoes_por_ano"] == {}
    assert set(t["proporcoes_projetadas"]) == {"1.0", "0.5"}


def test_ponte_com_tendencia_e_arranjos_fixos():
    # F: casal e multipessoal em 2017 e um unipessoal; com a tendência, os unipessoais crescem
    fato, _ = modelagem.preparar(
        pd.DataFrame(
            {
                "id_domicilio": [1, 2, 3],
                "sigla_uf": ["DF"] * 3,
                "idade_chefe": [65, 66, 67],
                "arranjo_familiar": [UNIPESSOAL, CASAL_OU_DUPLA, MULTIPESSOAL],
                "qtd_moradores": [1, 2, 3],
                "consumo_total_kwh": [120.0, 160.0, 150.0],
                "peso_final": [1.0, 1.0, 2.0],
            }
        )
    )
    pop_faixa = modelagem.populacao_por_faixa({2018: {65: 400}, 2026: {65: 400}, 2050: {65: 800}})
    ponte = modelagem.Ponte(fato, pop_faixa, tendencia={"60 a 69": (0.02, 0.01)})
    t = modelagem.projetar_taxas(ponte, [2026, 2050]).set_index("ano")
    f = modelagem.projetar_arranjos_fixos(ponte, [2026, 2050]).set_index("ano")
    c = modelagem.projetar_contrafactual(ponte, [2026, 2050]).set_index("ano")
    assert t.loc[2026, "tbc_padronizada_kwh"] == pytest.approx(f.loc[2026, "tbc_padronizada_kwh"])
    assert t.loc[2026, "tbc_padronizada_kwh"] == pytest.approx(c.loc[2026, "tbc_padronizada_kwh"])
    assert t.loc[2050, "domicilios_uni_60"] > f.loc[2050, "domicilios_uni_60"]
    # chefia total constante: 4 / 400 * 800 = 8 domicílios nos três cenários
    assert t.loc[2050, "domicilios"] == pytest.approx(8) and f.loc[2050, "domicilios"] == pytest.approx(8)
    assert (f["cenario"] == "taxas_arranjos_fixos").all()
