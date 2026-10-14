"""Projeções de consumo residencial de 2026 a 2070, em nível Brasil.

Dois métodos usam a mesma ponte entre pessoas e domicílios (taxas de chefia de
2018 constantes, premissa P2) e diferem só em como estimam o consumo de cada
perfil de domicílio:

- taxas: padronização direta com a TEC ponderada da POF (método de Diógenes);
- ml_rf e ml_gb: Random Forest e Gradient Boosting estimam o consumo de cada
  domicílio da POF, e a projeção reponderá a amostra para reproduzir os
  domicílios projetados de cada célula (faixa do chefe e arranjo).

O contrafactual é o método das taxas com a composição de domicílios de 2026
congelada; a diferença entre taxas e contrafactual é o efeito do envelhecimento.

O ML não prevê o futuro: a POF é um retrato de um único momento. O modelo estima
o consumo por perfil, e o futuro vem da projeção demográfica do IBGE.

Fórmulas puras em app.calculo; regras de domínio em app.dominio. O ETL importa
de app/, e app/ nunca importa daqui.
"""

import math
from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.calculo import (
    CONTRAFACTUAL,
    TAXAS,
    TAXAS_ARRANJOS_FIXOS,
    Projecao,
    consumo_por_pessoa,
    consumo_total,
    calibrar_intensidade,
    estimar_tendencia,
    fator_calibracao,
    media_ponderada,
    moradores_projetados,
    parametros_celulas,
    projetar_proporcoes,
    reponderar,
    tbc_pd,
    validar_tendencia,
)
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    CASAL_OU_DUPLA,
    FAIXAS_CHEFE,
    ANOS_MEDIOS_POF,
    ARRANJOS,
    INTENSIDADE_PADRAO,
    INTENSIDADES_SENSIBILIDADE,
    IDADE_IDOSO,
    MINIMO_AMOSTRA,
    MULTIPESSOAL,
    SEXO_AMBOS,
    TOTAL_DOMICILIOS_POF,
    UFS,
    UNIPESSOAL,
    faixa_do_chefe,
    populacao_por_faixa,
    proporcoes_por_edicao,
    somar_populacao,
)
from app.dados import Domicilio, DomicilioHistorico

ANOS = tuple(range(ANO_INICIAL, ANO_FINAL + 1))

# Total de referência do IBGE para validar a ponte (o da POF está em app.dominio)
DOMICILIOS_OCUPADOS_CENSO_2022 = 72_400_000  # Censo 2022: domicílios particulares permanentes ocupados (primeiros resultados)

# Mesmos identificadores da composição de domicílios da API
CATEGORIAS = (
    ("uni_60", UNIPESSOAL, True),
    ("cas_60", CASAL_OU_DUPLA, True),
    ("mul_60", MULTIPESSOAL, True),
    ("uni_59", UNIPESSOAL, False),
    ("cas_59", CASAL_OU_DUPLA, False),
    ("mul_59", MULTIPESSOAL, False),
)

COLUNAS_FATO = (
    "id_domicilio,sigla_uf,qtd_moradores,arranjo_familiar,idade_chefe,"
    "consumo_total_kwh,consumo_per_capita_kwh,peso_final"
)


# ---------- leitura (única parte que acessa o banco) ----------


COLUNAS_HISTORICA = "ano_pof,id_domicilio,arranjo_familiar,idade_chefe,peso_final,energia_rede_geral"


def carregar(cliente) -> tuple[pd.DataFrame, dict, dict, dict, pd.DataFrame]:
    """Lê a tabela fato, as POFs anteriores e a projeção das 27 UFs (e a linha Brasil, só para conferência).

    Devolve (fato, população das UFs, população da linha Brasil, linhas lidas contra o count do banco,
    POFs 2002 a 2003 e 2008 a 2009).
    """
    filtros_ufs = {"localidade": f"in.({','.join(UFS)})", "sexo": f"eq.{SEXO_AMBOS}", "ano": f"gte.{ANO_REFERENCIA_POF}"}
    filtros_brasil = {"localidade": "eq.Brasil", "sexo": f"eq.{SEXO_AMBOS}", "ano": f"gte.{ANO_REFERENCIA_POF}"}
    fato = cliente.selecionar("fato_consumo_domiciliar", COLUNAS_FATO, {"order": "id_domicilio.asc"})
    ufs = cliente.selecionar("projecoes_populacao_idade", "localidade,sexo,ano,idade,populacao", {**filtros_ufs, "order": "id.asc"})
    brasil = cliente.selecionar("projecoes_populacao_idade", "localidade,sexo,ano,idade,populacao", {**filtros_brasil, "order": "id.asc"})
    historica = cliente.selecionar("fato_consumo_pof_historica", COLUNAS_HISTORICA, {"order": "ano_pof.asc,id_domicilio.asc"})
    leitura = {
        "fato_consumo_pof_historica": {"lidas": len(historica), "no_banco": cliente.contar("fato_consumo_pof_historica")},
        "fato_consumo_domiciliar": {"lidas": len(fato), "no_banco": cliente.contar("fato_consumo_domiciliar")},
        "projecoes_populacao_idade (27 UFs, Ambos, 2018 a 2070)": {
            "lidas": len(ufs),
            "no_banco": cliente.contar("projecoes_populacao_idade", filtros_ufs),
        },
        "projecoes_populacao_idade (linha Brasil, Ambos, 2018 a 2070)": {
            "lidas": len(brasil),
            "no_banco": cliente.contar("projecoes_populacao_idade", filtros_brasil),
        },
    }
    for tabela, n in leitura.items():
        if n["lidas"] != n["no_banco"]:
            raise ValueError(f"{tabela}: foram lidas {n['lidas']} de {n['no_banco']} linhas")
    return pd.DataFrame(fato), somar_populacao(ufs, UFS), _linha_brasil(brasil), leitura, pd.DataFrame(historica)


def _linha_brasil(linhas: Iterable[dict]) -> dict[int, dict[int, int]]:
    """A linha de total "Brasil", lida só para conferir a soma das UFs; nunca entra nos cálculos."""
    populacao: dict[int, dict[int, int]] = {}
    for l in linhas:
        populacao.setdefault(int(l["ano"]), {})[int(l["idade"])] = int(l["populacao"])
    return populacao


# ---------- preparação e auditoria ----------


def preparar(fato: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Aplica a P8 (id repetido fica com o chefe de maior idade) e acrescenta faixa e célula."""
    faltando = {"id_domicilio", "idade_chefe", "arranjo_familiar", "peso_final", "consumo_total_kwh", "qtd_moradores"} - set(
        fato.columns
    )
    if faltando:
        raise ValueError(f"colunas ausentes: {sorted(faltando)}")
    if fato["peso_final"].isna().any() or (fato["peso_final"] <= 0).any():
        raise ValueError("peso_final ausente ou não positivo")
    ordem = fato.sort_values(["id_domicilio", "idade_chefe"], ascending=[True, False], kind="stable")
    limpo = fato.loc[sorted(ordem.drop_duplicates("id_domicilio").index)].copy()
    limpo["faixa"] = [_rotulo(i) for i in limpo["idade_chefe"]]
    if limpo["faixa"].isna().any():
        raise ValueError("há chefe abaixo da idade mínima das faixas")
    limpo["chefe_60_mais"] = limpo["idade_chefe"] >= IDADE_IDOSO
    limpo["consumo_per_capita_kwh"] = limpo["consumo_total_kwh"] / limpo["qtd_moradores"]
    limpo["celula"] = list(zip(limpo["faixa"], limpo["arranjo_familiar"]))
    repetidos = fato["id_domicilio"][fato["id_domicilio"].duplicated(keep=False)]
    registro = {
        "etapa": "preparacao (P8)",
        "fonte": "fato_consumo_domiciliar (POF 2017 a 2018)",
        "transformacao": "id_domicilio repetido fica só com o chefe de maior idade; faixa etária do chefe e "
        "célula (faixa, arranjo); consumo per capita = consumo total / moradores",
        "linhas_entrada": len(fato),
        "domicilios_repetidos": int(repetidos.nunique()),
        "linhas_dos_repetidos": int(len(repetidos)),
        "linhas_removidas": len(fato) - len(limpo),
        "linhas": len(limpo),
    }
    return limpo, registro


def _rotulo(idade: int) -> str | None:
    faixa = faixa_do_chefe(int(idade))
    return None if faixa is None else faixa.rotulo


def tabela_celulas(fato: pd.DataFrame) -> pd.DataFrame:
    """Por faixa e arranjo: amostra, domicílios ponderados e médias ponderadas."""
    linhas = []
    for (faixa, arranjo), g in fato.groupby(["faixa", "arranjo_familiar"], sort=False):
        w = g["peso_final"]
        linhas.append(
            {
                "faixa": faixa,
                "arranjo": arranjo,
                "amostra": len(g),
                "domicilios_ponderados": float(w.sum()),
                "consumo_domicilio_kwh": media_ponderada(g["consumo_total_kwh"], w),
                "consumo_per_capita_kwh": media_ponderada(g["consumo_per_capita_kwh"], w),
                "moradores": media_ponderada(g["qtd_moradores"], w),
                "baixa_amostra": len(g) < MINIMO_AMOSTRA,
            }
        )
    ordem_faixa = {f.rotulo: i for i, f in enumerate(FAIXAS_CHEFE)}
    ordem_arranjo = {UNIPESSOAL: 0, CASAL_OU_DUPLA: 1, MULTIPESSOAL: 2}
    tabela = pd.DataFrame(linhas)
    return tabela.sort_values(
        ["faixa", "arranjo"], key=lambda s: s.map(ordem_faixa if s.name == "faixa" else ordem_arranjo)
    ).reset_index(drop=True)


def auditar(bruto: pd.DataFrame, limpo: pd.DataFrame, registro_p8: dict, pop_ufs: dict, pop_brasil: dict, leitura: dict) -> dict:
    soma_pesos = float(limpo["peso_final"].sum())
    celulas = tabela_celulas(limpo)
    diferencas = [
        abs(pop_ufs.get(ano, {}).get(idade, 0) - p) for ano, idades in pop_brasil.items() for idade, p in idades.items()
    ]
    return {
        "linhas_lidas": leitura,
        "peso_final_ausente_ou_nao_positivo": int((bruto["peso_final"].isna() | (bruto["peso_final"] <= 0)).sum()),
        "p8_domicilios_repetidos": {k: registro_p8[k] for k in ("domicilios_repetidos", "linhas_dos_repetidos", "linhas_removidas")},
        "linhas_depois_da_p8": len(limpo),
        "chefes_com_menos_de_18_anos": int((limpo["idade_chefe"] < 18).sum()),
        "domicilios_acima_de_1000_kwh": int((limpo["consumo_total_kwh"] > 1000).sum()),
        "consumo_kwh_ausente_ou_zero": int((limpo["consumo_total_kwh"].isna() | (limpo["consumo_total_kwh"] <= 0)).sum()),
        "soma_dos_pesos": soma_pesos,
        "total_domicilios_pof_ibge": TOTAL_DOMICILIOS_POF,
        "cobertura_da_pof_pct": soma_pesos / TOTAL_DOMICILIOS_POF * 100,
        "soma_das_ufs_confere_com_brasil": bool(diferencas) and max(diferencas) == 0,
        "celulas": celulas.to_dict(orient="records"),
        "celulas_com_menos_de_30": int(celulas["baixa_amostra"].sum()),
    }


# ---------- ponte comum e método das taxas ----------
# A projeção é a mesma da API (app.calculo.Projecao); aqui só se monta a tabela anual.


class Ponte:
    """Parâmetros das células fixados em 2018 (taxa de chefia, TEC, consumo e moradores médios) e a projeção."""

    def __init__(
        self,
        fato: pd.DataFrame,
        pop_faixa: Mapping[int, Mapping[str, int]],
        fator: float = 1.0,
        tendencia: Mapping[str, tuple[float, float]] | None = None,
        intensidade: float = INTENSIDADE_PADRAO,
    ):
        if ANO_REFERENCIA_POF not in pop_faixa:
            raise ValueError(f"falta a população de {ANO_REFERENCIA_POF}")
        if fator <= 0:
            raise ValueError("o fator de cobertura precisa ser positivo")
        celulas = parametros_celulas(
            zip(
                fato["celula"],
                fato["peso_final"] * fator,
                fato["consumo_total_kwh"],
                fato["consumo_per_capita_kwh"],
                fato["qtd_moradores"],
            )
        )
        self.projecao = Projecao(
            celulas, pop_faixa, ANO_REFERENCIA_POF, ANO_INICIAL, None, tendencia, intensidade, ARRANJOS,
            intensidade_ate_base=INTENSIDADE_PADRAO,
        )
        self.celulas = list(celulas)
        self.chefia = self.projecao.chefia
        self.tec = {c: p.tec for c, p in celulas.items()}
        self.consumo_domicilio = {c: p.consumo_domicilio for c, p in celulas.items()}
        self.moradores = {c: p.moradores for c, p in celulas.items()}

    def domicilios(self, ano: int, cenario: str = TAXAS) -> dict[tuple[str, str], float]:
        return self.projecao.domicilios(ano, cenario)


def _categoria(celula: tuple[str, str]) -> str:
    faixa, arranjo = celula
    idoso = next(f for f in FAIXAS_CHEFE if f.rotulo == faixa).minima >= IDADE_IDOSO
    return next(i for i, a, v in CATEGORIAS if a == arranjo and v == idoso)


def _linha_taxas(ano: int, cenario: str, ponte: Ponte, ndom: Mapping) -> dict:
    total = consumo_total(ndom, ponte.consumo_domicilio)
    moradores = moradores_projetados(ndom, ponte.moradores)
    linha = {
        "ano": ano,
        "cenario": cenario,
        "domicilios": float(sum(ndom.values())),
        "moradores": moradores,
        "consumo_total_kwh_mes": total,
        "tbc_padronizada_kwh": tbc_pd(ponte.tec, ndom),
        "consumo_por_pessoa_kwh": consumo_por_pessoa(total, moradores),
    }
    for ident, _, _ in CATEGORIAS:
        sub = {c: n for c, n in ndom.items() if _categoria(c) == ident}
        linha[f"domicilios_{ident}"] = float(sum(sub.values()))
        linha[f"consumo_total_kwh_mes_{ident}"] = float(consumo_total(sub, {c: ponte.consumo_domicilio[c] for c in sub}))
    return linha


def projetar_taxas(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    return pd.DataFrame([_linha_taxas(a, TAXAS, ponte, ponte.domicilios(a)) for a in anos])


def projetar_arranjos_fixos(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    """Só o envelhecimento: as proporções de arranjo ficam nas de 2026."""
    return pd.DataFrame([_linha_taxas(a, TAXAS_ARRANJOS_FIXOS, ponte, ponte.domicilios(a, TAXAS_ARRANJOS_FIXOS)) for a in anos])


def projetar_contrafactual(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    """P10: o total de domicílios do ano segue a projeção; a distribuição entre as células fica na de 2026."""
    return pd.DataFrame([_linha_taxas(a, CONTRAFACTUAL, ponte, ponte.domicilios(a, CONTRAFACTUAL)) for a in anos])


def validar_ponte(ponte: Ponte, pop: Mapping[int, Mapping[int, int]], anos: Iterable[int] = (2022, ANO_INICIAL)) -> dict:
    """Domicílios projetados contra o Censo 2022 e moradores projetados contra a população do IBGE."""
    resultado = {}
    for ano in anos:
        ndom = ponte.domicilios(ano)
        moradores = moradores_projetados(ndom, ponte.moradores)
        populacao = sum(pop[ano].values())
        resultado[str(ano)] = {
            "domicilios_projetados": sum(ndom.values()),
            "moradores_projetados": moradores,
            "populacao_ibge": populacao,
            "moradores_menos_populacao_pct": (moradores / populacao - 1) * 100,
        }
    if "2022" in resultado:
        resultado["censo_2022_domicilios_ocupados"] = DOMICILIOS_OCUPADOS_CENSO_2022
        resultado["ponte_2022_menos_censo_pct"] = (
            resultado["2022"]["domicilios_projetados"] / DOMICILIOS_OCUPADOS_CENSO_2022 - 1
        ) * 100
    return resultado


# ---------- tendência dos arranjos (P13) ----------


def historicos_da_tabela(historica: pd.DataFrame) -> list[DomicilioHistorico]:
    return [
        DomicilioHistorico(int(a), arr, int(i), float(p), bool(r))
        for a, arr, i, p, r in zip(
            historica["ano_pof"], historica["arranjo_familiar"], historica["idade_chefe"], historica["peso_final"], historica["energia_rede_geral"]
        )
    ]


def atuais_da_fato(fato: pd.DataFrame) -> list[Domicilio]:
    return [
        Domicilio(arr, int(i), float(pc), peso=float(p))
        for arr, i, pc, p in zip(fato["arranjo_familiar"], fato["idade_chefe"], fato["consumo_per_capita_kwh"], fato["peso_final"])
    ]


def tendencia_arranjos(historica: pd.DataFrame, fato: pd.DataFrame, anos_projetados: Iterable[int] = (2026, 2050, 2070)) -> dict:
    """Proporções por edição, inclinações, validação fora do tempo e proporções projetadas (P13).

    Validação: inclinação estimada com 2002 e 2008, ancorada no observado de 2008, prevendo 2017.
    """
    props = proporcoes_por_edicao(historicos_da_tabela(historica), atuais_da_fato(fato))
    tendencia = estimar_tendencia(props, ARRANJOS)
    t02, t08, t17 = (ANOS_MEDIOS_POF[a] for a in (2002, 2008, 2017))
    validacao, calibracao = {}, {}
    if {t02, t08, t17} <= set(props):
        validacao = validar_tendencia(props, ARRANJOS, (t02, t08), t17)
        pesos = fato.groupby("faixa")["peso_final"].sum().to_dict()
        if any(f in pesos for f in props[t17]) and estimar_tendencia({t: props[t] for t in (t02, t08)}, ARRANJOS):
            melhor, curva = calibrar_intensidade(props, ARRANJOS, (t02, t08), t17, pesos, [i / 100 for i in range(151)])
            calibracao = {
                "intensidade_otima": melhor,
                "intensidade_padrao": INTENSIDADE_PADRAO,
                "erro_medio_absoluto_pp": {str(i): curva[i] for i in (0.0, 0.5, 0.56, 0.6, 1.0, 1.5) if i in curva},
                "regra": "erro médio absoluto da previsão de 2017 (inclinação de 2002 e 2008, ancorada em 2008), "
                "cada faixa pesando pelos seus domicílios ponderados de 2017",
            }

    def anos_de_tendencia(ano: int, intensidade: float) -> float:
        # de 2017,5 a 2026 vale o padrão; a intensidade só age depois de 2026
        return INTENSIDADE_PADRAO * (min(ano, ANO_INICIAL) - t17) + intensidade * max(0, ano - ANO_INICIAL)

    projetadas = {
        str(intensidade): {
            str(ano): {
                f: projetar_proporcoes(props[t17][f], tendencia.get(f), anos_de_tendencia(ano, intensidade), 1.0, ARRANJOS)
                for f in props.get(t17, {})
            }
            for ano in anos_projetados
        }
        for intensidade in (INTENSIDADE_PADRAO, *INTENSIDADES_SENSIBILIDADE)
    }
    return {
        "proporcoes_por_edicao": {str(t): p for t, p in props.items()},
        "inclinacoes_por_ano": {f: {"unipessoal_sobre_multipessoal": b[0], "casal_sobre_multipessoal": b[1]} for f, b in tendencia.items()},
        "validacao_fora_do_tempo_pp": validacao,
        "calibracao_da_intensidade": calibracao,
        "proporcoes_projetadas": projetadas,
        "regras": "domicílios fora da rede geral excluídos (P13); inclinação nacional por mínimos quadrados nas edições "
        "de 2002,5, 2008,5 e 2017,5; projeção ancorada no observado de 2017,5; de 2017,5 a 2026 vale a intensidade "
        "padrão, e a intensidade escolhida só age depois de 2026",
    }


def sensibilidade_intensidade(fato: pd.DataFrame, pop_faixa, tendencia, pop) -> pd.DataFrame:
    """Faixa de sensibilidade da tendência dos arranjos: o cenário taxas com as intensidades 0,5 e 1.

    Só `taxas` muda com a intensidade: arranjos fixos e contrafactual usam as proporções de 2026.
    """
    partes = []
    for intensidade in INTENSIDADES_SENSIBILIDADE:
        ponte = Ponte(fato, pop_faixa, tendencia=tendencia, intensidade=intensidade)
        tabela = calibrar(projetar_taxas(ponte), pop)
        tabela.insert(0, "analise", f"sensibilidade: intensidade da tendência {intensidade}".replace(".", ","))
        tabela.insert(1, "intensidade", intensidade)
        partes.append(tabela)
    return pd.concat(partes, ignore_index=True)


def fator_cobertura(fato: pd.DataFrame, total: float = TOTAL_DOMICILIOS_POF) -> float:
    """Análise de sensibilidade: fator único que leva a soma dos pesos ao total de domicílios da POF."""
    return total / float(fato["peso_final"].sum())


def calibrar(projecoes: pd.DataFrame, pop: Mapping[int, Mapping[int, int]]) -> pd.DataFrame:
    """P12: consumo total calibrado = consumo por pessoa * população do IBGE no ano (27 UFs, "Ambos").

    O fator (população / moradores projetados) é único para todas as células: as
    colunas por categoria são multiplicadas pelo mesmo fator. O consumo total bruto
    fica nas colunas consumo_total_kwh_mes, só como diagnóstico.
    """
    saida = projecoes.copy()
    saida["populacao_ibge"] = [sum(pop[a].values()) for a in saida["ano"]]
    saida["moradores_menos_populacao_pct"] = (saida["moradores"] / saida["populacao_ibge"] - 1) * 100
    saida["fator_calibracao"] = [fator_calibracao(p, m) for p, m in zip(saida["populacao_ibge"], saida["moradores"])]
    saida["consumo_total_calibrado_kwh_mes"] = saida["consumo_total_kwh_mes"] * saida["fator_calibracao"]
    for ident, _, _ in CATEGORIAS:
        saida[f"consumo_total_calibrado_kwh_mes_{ident}"] = saida[f"consumo_total_kwh_mes_{ident}"] * saida["fator_calibracao"]
    return saida


def sensibilidade_cobertura(projecoes: pd.DataFrame, fator: float) -> pd.DataFrame:
    """Sensibilidade (nunca resultado principal): domicílios, moradores e consumo total bruto multiplicados pelo fator.

    Como o fator é único, as taxas de chefia sobem na mesma proporção em todas as
    células: a TBC padronizada, o consumo por pessoa e o consumo total calibrado (P12) não mudam.
    """
    escalaveis = [c for c in projecoes.columns if c.startswith(("domicilios", "consumo_total_kwh_mes")) or c == "moradores"]
    saida = projecoes.copy()
    saida[escalaveis] = saida[escalaveis] * fator
    if "populacao_ibge" in saida:
        saida["moradores_menos_populacao_pct"] = (saida["moradores"] / saida["populacao_ibge"] - 1) * 100
        saida["fator_calibracao"] = saida["fator_calibracao"] / fator
    saida.insert(0, "analise", f"sensibilidade: pesos multiplicados por {fator:.4f}".replace(".", ","))
    saida.insert(1, "fator_cobertura", fator)
    return saida


# ---------- método B: machine learning ----------

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
    categorias = np.array([_categoria(c) for c in celulas])
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
