"""Projeções de consumo residencial de 2026 a 2070 pelo método das taxas (orquestração do ETL).

A mesma ponte entre pessoas e domicílios da API (taxa de chefia total de 2018 constante, P2, e
tendência dos arranjos, P13) monta três cenários:

- taxas: padronização direta com a TEC ponderada da POF (método de Diógenes);
- taxas_arranjos_fixos: só o envelhecimento, com os arranjos congelados em 2026;
- contrafactual: a composição de domicílios de 2026 congelada (P10).

Este módulo só orquestra: lê o banco, chama as funções de app.calculo e app.dominio e monta as
tabelas que o pipeline grava. Nenhuma fórmula mora aqui. O ETL importa de app/, e app/ nunca importa daqui.
O experimento de machine learning, fora do escopo das projeções, fica em etl/modelagem.py.
"""

from collections.abc import Iterable, Mapping

import pandas as pd

from app.calculo import (
    CONTRAFACTUAL,
    TAXAS,
    TAXAS_ARRANJOS_FIXOS,
    Projecao,
    anos_de_tendencia,
    calibrar_intensidade,
    consumo_calibrado,
    consumo_por_pessoa,
    diferenca_percentual,
    estimar_tendencia,
    fator_calibracao,
    fator_cobertura as fator_de_cobertura,
    media_ponderada,
    parametros_celulas,
    projetar_proporcoes,
    validar_tendencia,
)
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    ANO_REFERENCIA_POF,
    ANOS_MEDIOS_POF,
    ARRANJOS,
    CASAL_OU_DUPLA,
    CATEGORIAS,
    FAIXAS_CHEFE,
    IDADE_IDOSO,
    INTENSIDADE_PADRAO,
    INTENSIDADES_SENSIBILIDADE,
    MINIMO_AMOSTRA,
    MULTIPESSOAL,
    SEXO_AMBOS,
    TOTAL_DOMICILIOS_POF,
    UFS,
    UNIPESSOAL,
    categoria_da_celula,
    faixa_do_chefe,
    populacao_por_faixa,
    proporcoes_por_edicao,
    somar_populacao,
)
from app.dados import Domicilio, DomicilioHistorico

ANOS = tuple(range(ANO_INICIAL, ANO_FINAL + 1))

# Total de referência do IBGE para validar a ponte (o da POF está em app.dominio)
DOMICILIOS_OCUPADOS_CENSO_2022 = 72_400_000  # Censo 2022: domicílios particulares permanentes ocupados (primeiros resultados)

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
    limpo["consumo_per_capita_kwh"] = [consumo_por_pessoa(c, m) for c, m in zip(limpo["consumo_total_kwh"], limpo["qtd_moradores"])]
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
        "cobertura_da_pof_pct": 100 / fator_de_cobertura(soma_pesos, TOTAL_DOMICILIOS_POF),
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


def _linha_taxas(ano: int, cenario: str, ponte: Ponte) -> dict:
    """Uma linha da tabela anual: o resumo de todas as células e o de cada categoria (Projecao.resumo)."""
    todos = ponte.projecao.resumo(ano, cenario)
    linha = {
        "ano": ano,
        "cenario": cenario,
        "domicilios": float(todos.domicilios),
        "moradores": todos.moradores,
        "consumo_total_kwh_mes": todos.consumo_total,
        "tbc_padronizada_kwh": todos.tbc_padronizada,
        "consumo_por_pessoa_kwh": todos.consumo_por_pessoa,
    }
    for ident, _, _ in CATEGORIAS:
        celulas = [c for c in ponte.celulas if categoria_da_celula(c) == ident]
        resumo = ponte.projecao.resumo(ano, cenario, celulas) if celulas else None
        linha[f"domicilios_{ident}"] = float(resumo.domicilios) if resumo else 0.0
        linha[f"consumo_total_kwh_mes_{ident}"] = float(resumo.consumo_total) if resumo else 0.0
    return linha


def projetar_taxas(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    return pd.DataFrame([_linha_taxas(a, TAXAS, ponte) for a in anos])


def projetar_arranjos_fixos(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    """Só o envelhecimento: as proporções de arranjo ficam nas de 2026."""
    return pd.DataFrame([_linha_taxas(a, TAXAS_ARRANJOS_FIXOS, ponte) for a in anos])


def projetar_contrafactual(ponte: Ponte, anos: Iterable[int] = ANOS) -> pd.DataFrame:
    """P10: o total de domicílios do ano segue a projeção; a distribuição entre as células fica na de 2026."""
    return pd.DataFrame([_linha_taxas(a, CONTRAFACTUAL, ponte) for a in anos])


def validar_ponte(ponte: Ponte, pop: Mapping[int, Mapping[int, int]], anos: Iterable[int] = (2022, ANO_INICIAL)) -> dict:
    """Domicílios projetados contra o Censo 2022 e moradores projetados contra a população do IBGE."""
    resultado = {}
    for ano in anos:
        resumo = ponte.projecao.resumo(ano)
        populacao = sum(pop[ano].values())
        resultado[str(ano)] = {
            "domicilios_projetados": resumo.domicilios,
            "moradores_projetados": resumo.moradores,
            "populacao_ibge": populacao,
            "moradores_menos_populacao_pct": diferenca_percentual(resumo.moradores, populacao),
        }
    if "2022" in resultado:
        resultado["censo_2022_domicilios_ocupados"] = DOMICILIOS_OCUPADOS_CENSO_2022
        resultado["ponte_2022_menos_censo_pct"] = diferenca_percentual(
            resultado["2022"]["domicilios_projetados"], DOMICILIOS_OCUPADOS_CENSO_2022
        )
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

    # de 2017,5 a 2026 vale o padrão; a intensidade só age depois de 2026 (a mesma regra da Projecao)
    projetadas = {
        str(intensidade): {
            str(ano): {
                f: projetar_proporcoes(
                    props[t17][f], tendencia.get(f), anos_de_tendencia(ano, ANO_INICIAL, t17, intensidade, INTENSIDADE_PADRAO), 1.0, ARRANJOS
                )
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
    """Análise de sensibilidade: fator único que leva a soma dos pesos ao total de domicílios da POF (P9)."""
    return fator_de_cobertura(float(fato["peso_final"].sum()), total)


def calibrar(projecoes: pd.DataFrame, pop: Mapping[int, Mapping[int, int]]) -> pd.DataFrame:
    """P12: consumo total calibrado = consumo por pessoa * população do IBGE no ano (27 UFs, "Ambos").

    O fator (população / moradores projetados) é único para todas as células: as
    colunas por categoria são multiplicadas pelo mesmo fator. O consumo total bruto
    fica nas colunas consumo_total_kwh_mes, só como diagnóstico.
    """
    saida = projecoes.copy()
    saida["populacao_ibge"] = [sum(pop[a].values()) for a in saida["ano"]]
    pares = list(zip(saida["populacao_ibge"], saida["moradores"]))
    saida["moradores_menos_populacao_pct"] = [diferenca_percentual(m, p) for p, m in pares]
    saida["fator_calibracao"] = [fator_calibracao(p, m) for p, m in pares]
    for sufixo in ("", *(f"_{ident}" for ident, _, _ in CATEGORIAS)):
        saida[f"consumo_total_calibrado_kwh_mes{sufixo}"] = [
            consumo_calibrado(c, p, m) for c, (p, m) in zip(saida[f"consumo_total_kwh_mes{sufixo}"], pares)
        ]
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
        pares = list(zip(saida["populacao_ibge"], saida["moradores"]))
        saida["moradores_menos_populacao_pct"] = [diferenca_percentual(m, p) for p, m in pares]
        saida["fator_calibracao"] = [fator_calibracao(p, m) for p, m in pares]
    saida.insert(0, "analise", f"sensibilidade: pesos multiplicados por {fator:.4f}".replace(".", ","))
    saida.insert(1, "fator_cobertura", fator)
    return saida

