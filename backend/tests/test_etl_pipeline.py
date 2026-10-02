import pandas as pd
import pytest

from etl import pipeline


def _etapa(nome, ordem):
    def etapa(dados):
        ordem.append(nome)
        base = dados if dados is not None else pd.DataFrame({"x": [1]})
        return base, {"etapa": nome, "fonte": "teste", "transformacao": f"passou por {nome}"}

    etapa.__name__ = nome
    return etapa


def test_etapas_padrao():
    assert [e.__name__ for e in pipeline.ETAPAS] == ["derivar"]


def test_executa_na_ordem_e_guarda_o_rastro():
    ordem = []
    dados, rastro = pipeline.executar(None, [_etapa("a", ordem), _etapa("b", ordem)])
    assert ordem == ["a", "b"]
    assert [r["etapa"] for r in rastro] == ["a", "b"]
    assert list(dados["x"]) == [1]


def test_etapa_sem_rastro_completo_interrompe():
    def sem_fonte(dados):
        return dados, {"etapa": "x", "transformacao": "y"}

    with pytest.raises(ValueError, match="fonte"):
        pipeline.executar(None, [sem_fonte])


def test_pipeline_padrao_deriva_as_colunas():
    entrada = pd.DataFrame({"qtd_moradores": [1, 3], "idade_chefe": [70, 40], "consumo_total_kwh": [100.0, 150.0]})
    saida, rastro = pipeline.executar(entrada)
    assert list(saida["arranjo_familiar"]) == ["Unipessoal (Mononuclear)", "Multipessoal (3+)"]
    assert list(saida["consumo_per_capita_kwh"]) == [100.0, 50.0]
    assert rastro[0]["etapa"] == "derivacao"
