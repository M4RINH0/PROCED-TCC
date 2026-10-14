"""Orquestra as etapas do ETL em ordem (RNF08).

Cada etapa recebe a tabela da anterior e devolve (tabela, registro). O registro
diz a fonte e a transformação aplicada, para manter a rastreabilidade.
A extração e a carga dos microdados ficam no BigQuery (docs/scripts). Rodado como
módulo (python -m etl.pipeline), lê o Supabase e grava as projeções de 2026 a 2070
em etl/saida/ (docs/etl.md, seção 5).
"""

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from etl import modelagem
from etl.derivacao import derivar

Etapa = Callable[[pd.DataFrame | None], tuple[pd.DataFrame, dict]]
ETAPAS: tuple[Etapa, ...] = (derivar,)


def executar(entrada: pd.DataFrame | None, etapas: Sequence[Etapa] = ETAPAS) -> tuple[pd.DataFrame | None, list[dict]]:
    dados = entrada
    rastro: list[dict] = []
    for etapa in etapas:
        dados, registro = etapa(dados)
        for campo in ("etapa", "fonte", "transformacao"):
            if not registro.get(campo):
                raise ValueError(f"a etapa {etapa.__name__} não registrou o campo {campo}")
        rastro.append(registro)
    return dados, rastro


# ---------- projeções de 2026 a 2070: python -m etl.pipeline ----------

PASTA_SAIDA = Path(__file__).parent / "saida"
CENARIOS = ("taxas", "ml_rf", "ml_gb", "contrafactual")


def _json(caminho: Path, conteudo) -> None:
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2, default=_serializavel), encoding="utf-8")


def _serializavel(valor):
    if isinstance(valor, (np.integer, np.floating, np.bool_)):
        return valor.item()
    if isinstance(valor, tuple):
        return list(valor)
    raise TypeError(f"não serializável: {type(valor)}")


def projetar(
    fato_bruto: pd.DataFrame,
    pop: dict,
    pop_brasil: dict,
    leitura: dict,
    pasta: Path,
    avaliar_ml: bool = True,
    projetar_ml: bool = False,
) -> dict:
    """Gera as saídas em `pasta` e devolve um resumo. Sem banco: recebe o que carregar() leu.

    O ML está pausado: por padrão, os modelos são avaliados (métricas e importância
    das variáveis), mas não entram nas projeções.
    """
    pasta.mkdir(parents=True, exist_ok=True)
    derivado, rastro = executar(fato_bruto)
    fato, registro = modelagem.preparar(derivado)
    rastro.append(registro)

    pop_faixa = modelagem.populacao_por_faixa(pop)
    ponte = modelagem.Ponte(fato, pop_faixa)
    auditoria = modelagem.auditar(fato_bruto, fato, registro, pop, pop_brasil, leitura)
    auditoria["ponte"] = modelagem.validar_ponte(ponte, pop)
    rastro.append(
        {
            "etapa": "ponte e método das taxas",
            "fonte": "fato_consumo_domiciliar e projecoes_populacao_idade (27 UFs, Ambos)",
            "transformacao": "taxas de chefia de 2018 por faixa e arranjo (P2); padronização direta com a TEC "
            "ponderada (P6); contrafactual com a composição de 2026 congelada (P10)",
        }
    )

    projecoes = [modelagem.projetar_taxas(ponte)]
    if avaliar_ml:
        avaliacao = modelagem.avaliar(fato)
        _json(pasta / "metricas_modelos.json", avaliacao)
        modelagem.importancia_tabela(avaliacao).to_csv(pasta / "importancia_variaveis.csv", index=False)
        rastro.append(
            {
                "etapa": "avaliação do machine learning",
                "fonte": "fato_consumo_domiciliar (POF 2017 a 2018)",
                "transformacao": "KFold com 5 partes e semente 42; alvo em log1p com correção de Duan; métricas "
                "ponderadas e importância por permutação",
            }
        )
    if projetar_ml:
        for nome in ("ml_rf", "ml_gb"):
            total, per_capita = modelagem.ajustar_e_prever(fato, nome)
            projecoes.append(modelagem.projetar_reponderacao(fato, total, per_capita, ponte, nome))
        rastro.append(
            {
                "etapa": "projeção do machine learning",
                "fonte": "modelos ajustados em toda a amostra",
                "transformacao": "reponderação da amostra para os domicílios projetados de cada célula",
            }
        )
    projecoes.append(modelagem.projetar_contrafactual(ponte))
    resultado = modelagem.adicionar_populacao(pd.concat(projecoes, ignore_index=True), pop)
    resultado.to_csv(pasta / "projecoes_2026_2070.csv", index=False)

    fator = modelagem.fator_cobertura(fato)
    modelagem.sensibilidade_cobertura(resultado, fator).to_csv(pasta / "sensibilidade_cobertura.csv", index=False)
    rastro.append(
        {
            "etapa": "sensibilidade da cobertura",
            "fonte": "POF 2017 a 2018 (68,9 milhões de domicílios)",
            "transformacao": f"pesos multiplicados por {fator:.4f} (P9); saída separada do resultado principal",
        }
    )
    auditoria["rastro"] = rastro
    _json(pasta / "auditoria.json", auditoria)
    return {"auditoria": auditoria, "projecoes": resultado}


def main() -> None:
    from app.config import DOTENV, carregar_configuracao
    from app.supabase import criar_cliente

    cliente = criar_cliente(carregar_configuracao(dotenv=DOTENV))
    projetar(*modelagem.carregar(cliente), pasta=PASTA_SAIDA)
    print(f"saídas gravadas em {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
