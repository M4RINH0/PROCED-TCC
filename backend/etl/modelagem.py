"""Experimento de machine learning, fora do escopo das projeções (registro citado no TCC).

Random Forest e Gradient Boosting (HistGradientBoostingRegressor) estimaram o consumo de cada
domicílio da POF 2017 a 2018 a partir da idade do chefe, do arranjo, dos moradores e da UF, contra
a linha de base obrigatória (média ponderada da célula). O ML saiu das projeções e do site por três
motivos: baixo poder explicativo (R² perto do da linha de base), ausência de série temporal (a POF é
um retrato de um único momento, e o ML não prevê o futuro) e equivalência com o método das taxas sob
reponderação (com a média da célula como previsão, a reponderação reproduz exatamente o método A).

O experimento fica fora do pipeline padrão (python -m etl.pipeline). Para reproduzir a avaliação:

    python -m etl.modelagem

que lê o Supabase e regrava etl/saida/metricas_modelos.json e etl/saida/importancia_variaveis.csv.
Regras: KFold com 5 partes, shuffle=True, random_state=42, pré-processamento ajustado dentro de cada
parte, alvo em log1p com correção de Duan, métricas e ajuste ponderados por peso_final e importância
por permutação.
"""

import json
import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.calculo import consumo_por_pessoa, reponderar
from app.dominio import CATEGORIAS, categoria_da_celula
from etl.projecao import ANOS, Ponte, _rotulo

VARIAVEIS_NUMERICAS = ("idade_chefe", "qtd_moradores")
VARIAVEIS_CATEGORICAS = ("arranjo_familiar", "sigla_uf")
VARIAVEIS = VARIAVEIS_NUMERICAS + VARIAVEIS_CATEGORICAS
SEMENTE = 42
PARTES = 5

# Hiperparâmetros fixados antes de qualquer avaliação, sem busca: o ML não é ajustado para "ganhar".
PARAMETROS = {
    "ml_rf": {"n_estimators": 300, "min_samples_leaf": 10, "n_jobs": -1},
    "ml_gb": {},  # padrão do scikit-learn
}


def criar_modelo(nome: str) -> Pipeline:
    """Pré-processamento e regressor num único Pipeline: tudo é ajustado só com a parte de treino."""
    if nome == "ml_rf":
        regressor = RandomForestRegressor(random_state=SEMENTE, **PARAMETROS["ml_rf"])
    elif nome == "ml_gb":
        regressor = HistGradientBoostingRegressor(random_state=SEMENTE, **PARAMETROS["ml_gb"])
    else:
        raise ValueError(f"modelo desconhecido: {nome}")
    codificador = ColumnTransformer(
        [
            ("categoricas", OneHotEncoder(handle_unknown="ignore", sparse_output=False), list(VARIAVEIS_CATEGORICAS)),
            ("numericas", "passthrough", list(VARIAVEIS_NUMERICAS)),
        ]
    )
    return Pipeline([("codificador", codificador), ("regressor", regressor)])


class ModeloLog:
    """Ajusta em log1p(consumo) e volta à escala original com a correção de Duan (smearing):

        y_hat = exp(z_hat) * S - 1,   S = soma(peso * exp(residuo)) / soma(peso)

    com os resíduos em log da própria amostra de treino.
    """

    def __init__(self, nome: str):
        self.nome = nome
        self.pipeline = criar_modelo(nome)
        self.smearing: float | None = None

    def ajustar(self, X: pd.DataFrame, y: np.ndarray, peso: np.ndarray) -> "ModeloLog":
        z = np.log1p(y)
        self.pipeline.fit(X[list(VARIAVEIS)], z, regressor__sample_weight=peso)
        # A previsão em paralelo soma as árvores em ordem variável e muda a última casa decimal;
        # com uma linha de execução, o resultado é idêntico a cada execução.
        self.pipeline.named_steps["regressor"].set_params(**({"n_jobs": 1} if self.nome == "ml_rf" else {}))
        residuo = z - self.pipeline.predict(X[list(VARIAVEIS)])
        self.smearing = float(np.average(np.exp(residuo), weights=peso))
        return self

    def prever(self, X: pd.DataFrame) -> np.ndarray:
        if self.smearing is None:
            raise ValueError("o modelo ainda não foi ajustado")
        return np.exp(self.pipeline.predict(X[list(VARIAVEIS)])) * self.smearing - 1


class LinhaDeBase:
    """Média ponderada do consumo por domicílio em cada célula (faixa, arranjo) da parte de treino."""

    nome = "linha_de_base"

    def ajustar(self, X: pd.DataFrame, y: np.ndarray, peso: np.ndarray) -> "LinhaDeBase":
        tabela = pd.DataFrame({"celula": list(X["celula"]), "yw": y * peso, "w": peso}).groupby("celula")[["yw", "w"]].sum()
        self.media = (tabela["yw"] / tabela["w"]).to_dict()
        self.geral = float(np.average(y, weights=peso))
        return self

    def prever(self, X: pd.DataFrame) -> np.ndarray:
        return np.array([self.media.get(c, self.geral) for c in X["celula"]])


def novo_modelo(nome: str):
    return LinhaDeBase() if nome == "linha_de_base" else ModeloLog(nome)


def metricas(y: np.ndarray, previsto: np.ndarray, peso: np.ndarray) -> dict:
    """MAE, RMSE e R² ponderados pelo peso amostral, em kWh/mês por domicílio; viés = média de previsto menos observado."""
    erro = previsto - y
    media = np.average(y, weights=peso)
    return {
        "mae": float(np.average(np.abs(erro), weights=peso)),
        "rmse": float(math.sqrt(np.average(erro**2, weights=peso))),
        "r2": float(1 - np.sum(peso * erro**2) / np.sum(peso * (y - media) ** 2)),
        "vies": float(np.average(erro, weights=peso)),
    }


def _importancia(modelo, X: pd.DataFrame, y: np.ndarray, peso: np.ndarray, repeticoes: int, rng: np.random.Generator) -> dict:
    """Importância por permutação: aumento do MAE ponderado ao embaralhar cada variável na parte de teste.

    Cada variável é embaralhada sozinha. Na linha de base, a célula é refeita a partir
    da idade e do arranjo embaralhados.
    """
    base = metricas(y, modelo.prever(X), peso)["mae"]
    resultado = {}
    for variavel in VARIAVEIS:
        aumentos = []
        for _ in range(repeticoes):
            embaralhado = X.copy()
            embaralhado[variavel] = rng.permutation(embaralhado[variavel].to_numpy())
            if variavel in ("idade_chefe", "arranjo_familiar") and "celula" in embaralhado:
                embaralhado["celula"] = list(zip([_rotulo(i) for i in embaralhado["idade_chefe"]], embaralhado["arranjo_familiar"]))
            aumentos.append(metricas(y, modelo.prever(embaralhado), peso)["mae"] - base)
        resultado[variavel] = float(np.mean(aumentos))
    return resultado


def avaliar(
    fato: pd.DataFrame,
    modelos: Iterable[str] = ("linha_de_base", "ml_rf", "ml_gb"),
    partes: int = PARTES,
    semente: int = SEMENTE,
    repeticoes: int = 5,
    detalhe: bool = False,
) -> dict:
    """Validação cruzada KFold (embaralhada, semente fixa) com métricas ponderadas por parte."""
    modelos = list(modelos)
    X = fato.reset_index(drop=True)
    y = X["consumo_total_kwh"].to_numpy(dtype=float)
    w = X["peso_final"].to_numpy(dtype=float)
    divisao = KFold(n_splits=partes, shuffle=True, random_state=semente)
    resultado = {m: {"partes": [], "importancia_partes": []} for m in modelos}
    detalhes = []
    for parte, (treino, teste) in enumerate(divisao.split(X)):
        info = {"parte": parte, "treino": treino, "teste": teste, "codificadores": {}}
        for nome in modelos:
            modelo = novo_modelo(nome).ajustar(X.iloc[treino], y[treino], w[treino])
            m = metricas(y[teste], modelo.prever(X.iloc[teste]), w[teste])
            if isinstance(modelo, ModeloLog):
                m["smearing"] = modelo.smearing
                info["codificadores"][nome] = modelo.pipeline.named_steps["codificador"]
            resultado[nome]["partes"].append(m)
            rng = np.random.default_rng(semente + parte)
            resultado[nome]["importancia_partes"].append(
                _importancia(modelo, X.iloc[teste].reset_index(drop=True), y[teste], w[teste], repeticoes, rng)
            )
        detalhes.append(info)
    for nome in modelos:
        partes_m = resultado[nome]["partes"]
        resultado[nome]["media"] = {k: float(np.mean([p[k] for p in partes_m])) for k in ("mae", "rmse", "r2", "vies")}
        resultado[nome]["desvio"] = {k: float(np.std([p[k] for p in partes_m], ddof=1)) for k in ("mae", "rmse", "r2", "vies")}
        imp = resultado[nome]["importancia_partes"]
        resultado[nome]["importancia"] = {
            v: {"media": float(np.mean([i[v] for i in imp])), "desvio": float(np.std([i[v] for i in imp], ddof=1))}
            for v in VARIAVEIS
        }
    resultado["configuracao"] = {
        "validacao": f"KFold com {partes} partes, shuffle=True, random_state={semente}",
        "alvo": "consumo_total_kwh (kWh/mês por domicílio); modelos de ML em log1p com correção de Duan",
        "pesos": "peso_final no ajuste e nas métricas",
        "variaveis": list(VARIAVEIS),
        "hiperparametros": PARAMETROS,
        "importancia": f"permutação na parte de teste, {repeticoes} repetições, aumento do MAE ponderado",
    }
    if detalhe:
        resultado["detalhes"] = detalhes
    return resultado


def importancia_tabela(avaliacao: dict) -> pd.DataFrame:
    linhas = []
    for nome, r in avaliacao.items():
        if nome in ("configuracao", "detalhes"):
            continue
        for variavel, v in r["importancia"].items():
            linhas.append({"modelo": nome, "variavel": variavel, "aumento_mae_kwh_media": v["media"], "aumento_mae_kwh_desvio": v["desvio"]})
    return pd.DataFrame(linhas)


# ---------- projeção por reponderação da amostra ----------


def projetar_reponderacao(
    fato: pd.DataFrame,
    previsao_total: np.ndarray,
    previsao_per_capita: np.ndarray,
    ponte: Ponte,
    cenario: str,
    anos: Iterable[int] = ANOS,
) -> pd.DataFrame:
    """A cada ano, o peso de cada domicílio é ajustado para que a sua célula some os domicílios projetados.

    consumo total = soma(peso' * previsão do consumo do domicílio)
    TBC padronizada = soma(peso' * previsão per capita) / soma(peso')
    Com a média da célula como previsão, reproduz exatamente o método das taxas.
    """
    celulas = list(fato["celula"])
    categorias = np.array([categoria_da_celula(c) for c in celulas])
    pesos = fato["peso_final"].to_numpy(dtype=float)
    moradores = fato["qtd_moradores"].to_numpy(dtype=float)
    previsao_total = np.asarray(previsao_total, dtype=float)
    previsao_per_capita = np.asarray(previsao_per_capita, dtype=float)
    linhas = []
    for ano in anos:
        w = np.array(reponderar(pesos, celulas, ponte.domicilios(ano)))
        total = float(np.sum(w * previsao_total))
        n_moradores = float(np.sum(w * moradores))
        linha = {
            "ano": ano,
            "cenario": cenario,
            "domicilios": float(w.sum()),
            "moradores": n_moradores,
            "consumo_total_kwh_mes": total,
            "tbc_padronizada_kwh": float(np.sum(w * previsao_per_capita) / w.sum()),
            "consumo_por_pessoa_kwh": consumo_por_pessoa(total, n_moradores),
        }
        for ident, _, _ in CATEGORIAS:
            m = categorias == ident
            linha[f"domicilios_{ident}"] = float(w[m].sum())
            linha[f"consumo_total_kwh_mes_{ident}"] = float(np.sum(w[m] * previsao_total[m]))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def ajustar_e_prever(fato: pd.DataFrame, nome: str) -> tuple[np.ndarray, np.ndarray]:
    """Ajusta o modelo em toda a amostra e prevê o consumo de cada domicílio (total e per capita)."""
    y = fato["consumo_total_kwh"].to_numpy(dtype=float)
    w = fato["peso_final"].to_numpy(dtype=float)
    modelo = novo_modelo(nome).ajustar(fato, y, w)
    total = modelo.prever(fato)
    return total, total / fato["qtd_moradores"].to_numpy(dtype=float)


# ---------- reprodução da avaliação: python -m etl.modelagem ----------


def gravar_avaliacao(avaliacao: dict, pasta: Path) -> None:
    """Grava as métricas e a importância das variáveis, as duas saídas citadas no TCC."""
    (pasta / "metricas_modelos.json").write_text(
        json.dumps(avaliacao, ensure_ascii=False, indent=2, default=_serializavel), encoding="utf-8"
    )
    importancia_tabela(avaliacao).to_csv(pasta / "importancia_variaveis.csv", index=False)


def _serializavel(valor):
    if isinstance(valor, (np.integer, np.floating, np.bool_)):
        return valor.item()
    if isinstance(valor, tuple):
        return list(valor)
    raise TypeError(f"não serializável: {type(valor)}")


def main() -> None:
    from app.config import DOTENV, carregar_configuracao
    from app.supabase import criar_cliente
    from etl.pipeline import PASTA_SAIDA, executar
    from etl.projecao import carregar, preparar

    cliente = criar_cliente(carregar_configuracao(dotenv=DOTENV))
    fato_bruto = carregar(cliente)[0]
    derivado, _ = executar(fato_bruto)
    fato, _ = preparar(derivado)
    gravar_avaliacao(avaliar(fato), PASTA_SAIDA)
    print(f"avaliação do machine learning gravada em {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
