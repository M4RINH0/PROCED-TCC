import pandas as pd
import pytest

from modules.derivacao import arranjo_familiar, consumo_per_capita, derivar, eh_60_mais, faixa_etaria_chefe


@pytest.mark.parametrize(
    "moradores, esperado",
    [(1, "Unipessoal (Mononuclear)"), (2, "Casal ou Dupla"), (3, "Multipessoal (3+)"), (9, "Multipessoal (3+)")],
)
def test_arranjo_por_numero_de_moradores(moradores, esperado):
    assert arranjo_familiar(moradores) == esperado


def test_arranjo_rejeita_domicilio_sem_morador():
    with pytest.raises(ValueError):
        arranjo_familiar(0)


@pytest.mark.parametrize("idade, esperado", [(59, False), (60, True), (61, True), (0, False)])
def test_limite_dos_60_anos(idade, esperado):
    assert eh_60_mais(idade) is esperado


@pytest.mark.parametrize(
    "idade, faixa",
    [(18, "até 29"), (29, "até 29"), (30, "30 a 39"), (59, "50 a 59"), (60, "60 a 69"), (69, "60 a 69"),
     (70, "70 a 79"), (79, "70 a 79"), (80, "80+"), (104, "80+")],
)
def test_faixa_etaria_do_chefe_nos_limites(idade, faixa):
    assert faixa_etaria_chefe(idade) == faixa


@pytest.mark.parametrize("funcao", [eh_60_mais, faixa_etaria_chefe])
def test_idade_negativa_e_rejeitada(funcao):
    with pytest.raises(ValueError):
        funcao(-1)


def test_consumo_per_capita_confere_com_linha_do_banco():
    # linha real: 4 moradores, 13 kWh no total, 3,25 kWh per capita (13 / 4)
    assert consumo_per_capita(13, 4) == pytest.approx(3.25)


def test_consumo_per_capita_rejeita_entradas_invalidas():
    with pytest.raises(ValueError):
        consumo_per_capita(10, 0)
    with pytest.raises(ValueError):
        consumo_per_capita(-1, 2)


def test_derivar_acrescenta_colunas_e_registra_a_transformacao():
    df = pd.DataFrame({"qtd_moradores": [1, 2, 4], "idade_chefe": [72, 45, 60], "consumo_total_kwh": [90.0, 150.0, 200.0]})
    saida, registro = derivar(df)
    assert list(saida["arranjo_familiar"]) == ["Unipessoal (Mononuclear)", "Casal ou Dupla", "Multipessoal (3+)"]
    assert list(saida["is_60_mais"]) == [True, False, True]
    assert list(saida["faixa_etaria_chefe"]) == ["70 a 79", "40 a 49", "60 a 69"]
    assert list(saida["consumo_per_capita_kwh"]) == pytest.approx([90.0, 75.0, 50.0])
    assert registro["etapa"] == "derivacao" and registro["linhas"] == 3
    assert "arranjo_familiar" not in df.columns  # não altera a entrada


def test_derivar_exige_colunas():
    with pytest.raises(ValueError, match="idade_chefe"):
        derivar(pd.DataFrame({"qtd_moradores": [1], "consumo_total_kwh": [1.0]}))
