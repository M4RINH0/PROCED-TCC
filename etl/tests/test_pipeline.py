import pandas as pd
import pytest

import pipeline


def _etapa(nome, ordem):
    def etapa(dados):
        ordem.append(nome)
        base = dados if dados is not None else pd.DataFrame({"x": [1]})
        return base, {"etapa": nome, "fonte": "teste", "transformacao": f"passou por {nome}"}

    etapa.__name__ = nome
    return etapa


def test_ordem_padrao_das_etapas():
    nomes = [e.__name__ for e in pipeline.ETAPAS]
    assert nomes == ["extrair", "limpar", "derivar", "carregar"]


def test_executa_na_ordem_e_guarda_o_rastro():
    ordem = []
    dados, rastro = pipeline.executar([_etapa("a", ordem), _etapa("b", ordem)])
    assert ordem == ["a", "b"]
    assert [r["etapa"] for r in rastro] == ["a", "b"]
    assert list(dados["x"]) == [1]


def test_etapa_sem_rastro_completo_interrompe():
    def sem_fonte(dados):
        return dados, {"etapa": "x", "transformacao": "y"}

    with pytest.raises(ValueError, match="fonte"):
        pipeline.executar([sem_fonte])


def test_etapas_pendentes_avisam_em_vez_de_fingir_sucesso():
    with pytest.raises(NotImplementedError):
        pipeline.executar()
