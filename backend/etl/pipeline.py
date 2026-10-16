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

from etl import projecao
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
    historica: pd.DataFrame | None,
    pasta: Path,
) -> dict:
    """Gera as saídas em `pasta` e devolve um resumo. Sem banco: recebe o que carregar() leu.

    Só o método das taxas e o contrafactual. O experimento de machine learning, fora do escopo
    das projeções, tem comando próprio (python -m etl.modelagem).
    """
    pasta.mkdir(parents=True, exist_ok=True)
    derivado, rastro = executar(fato_bruto)
    fato, registro = projecao.preparar(derivado)
    rastro.append(registro)

    pop_faixa = projecao.populacao_por_faixa(pop)
    historica = historica if historica is not None else pd.DataFrame(columns=projecao.COLUNAS_HISTORICA.split(","))
    tendencia = projecao.tendencia_arranjos(historica, fato)
    _json(pasta / "tendencia_arranjos.json", tendencia)
    inclinacoes = {f: (b["unipessoal_sobre_multipessoal"], b["casal_sobre_multipessoal"]) for f, b in tendencia["inclinacoes_por_ano"].items()}
    ponte = projecao.Ponte(fato, pop_faixa, tendencia=inclinacoes)  # intensidade padrão (P13)
    projecao.sensibilidade_intensidade(fato, pop_faixa, inclinacoes, pop).to_csv(pasta / "sensibilidade_intensidade.csv", index=False)
    auditoria = projecao.auditar(fato_bruto, fato, registro, pop, pop_brasil, leitura)
    auditoria["ponte"] = projecao.validar_ponte(ponte, pop)
    rastro.append(
        {
            "etapa": "ponte e método das taxas",
            "fonte": "fato_consumo_domiciliar e projecoes_populacao_idade (27 UFs, Ambos)",
            "transformacao": "taxa de chefia de 2018 por faixa (P2) e tendência dos arranjos (P13); padronização "
            "direta com a TEC ponderada (P6); arranjos fixos em 2026; contrafactual com a composição de 2026 "
            "congelada (P10); consumo total calibrado pela população do IBGE (P12)",
        }
    )

    projecoes = [projecao.projetar_taxas(ponte), projecao.projetar_arranjos_fixos(ponte), projecao.projetar_contrafactual(ponte)]
    resultado = projecao.calibrar(pd.concat(projecoes, ignore_index=True), pop)
    resultado.to_csv(pasta / "projecoes_2026_2070.csv", index=False)

    fator = projecao.fator_cobertura(fato)
    projecao.sensibilidade_cobertura(resultado, fator).to_csv(pasta / "sensibilidade_cobertura.csv", index=False)
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
    projetar(*projecao.carregar(cliente), pasta=PASTA_SAIDA)
    print(f"saídas gravadas em {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
