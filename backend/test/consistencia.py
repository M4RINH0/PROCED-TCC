"""Checagens de consistência entre os endpoints, usadas com a base sintética (test_consistencia.py)
e com o banco real (test_consistencia_integracao.py).

Cada checagem consulta a API pelo TestClient e compara o que telas diferentes mostram do mesmo
número. A tolerância cobre só o arredondamento que a API aplica a cada valor (inteiro no consumo
total e nos domicílios, duas casas na participação).
"""

import csv
import io

from app.calculo import CENARIOS, consumo_calibrado, consumo_total, moradores_projetados
from app.dominio import (
    CELULAS_DO_RECORTE,
    CATEGORIAS,
    RECORTE_DO_GRUPO,
    Recorte,
    base_da_localidade,
    categoria_da_celula,
    projecao_da_base,
    tendencia_dos_dados,
)
from app.schemas.simulador import ROTULO_FAIXA

ANOS = (2026, 2050, 2070)
ARRANJOS_SIM = {"Unipessoal (Mononuclear)": "unipessoal", "Casal ou Dupla": "casal_ou_dupla", "Multipessoal (3+)": "multipessoal"}
FAIXA_SIM = {rotulo: faixa.value for faixa, rotulo in ROTULO_FAIXA.items()}


def _sim(params):
    return {k: v for k, v in params.items() if k in ("localidade", "intensidade", "k")}


def serie(cliente, recorte, params):
    r = cliente.get("/projecoes/serie", params={"recorte": recorte.value, **_sim(params)})
    assert r.status_code == 200, r.text
    return {p["ano"]: {c["id"]: c for c in p["cenarios"]} | {"_ponto": p} for p in r.json()["pontos"]}


def celulas_do_simulador(cliente, ano, cenario, params):
    """As 21 células (faixa do chefe, arranjo) no Simulador; None nas sem amostra."""
    resultado = {}
    for faixa, faixa_sim in FAIXA_SIM.items():
        for arranjo, arranjo_sim in ARRANJOS_SIM.items():
            r = cliente.get(
                "/simulador",
                params={"ano": ano, "faixa": faixa_sim, "arranjo": arranjo_sim, "base": cenario, **_sim(params), "recalcular": True},
            )
            assert r.status_code == 200, r.text
            corpo = r.json()
            resultado[(faixa, arranjo)] = None if corpo["domicilios_projetados"] is None else corpo
    return resultado


def soma(valores):
    vs = [v for v in valores if v is not None]
    return sum(vs) if vs else None


# ---------- 1. consumo das células = consumo total do Panorama ----------


def checar_consumo_das_celulas(cliente, dados, params):
    """(a) Na projeção: soma de domicílios × consumo médio por domicílio das células, calibrada (P12),
    igual ao consumo total do Panorama em cada recorte. (b) Pela API: soma dos consumos totais das
    células do Simulador igual ao do Panorama."""
    localidade = params["localidade"]
    base = base_da_localidade(dados, localidade)
    projecao = projecao_da_base(base, tendencia_dos_dados(dados), params["intensidade"], params["k"])
    divergencias = []
    for ano in ANOS:
        for cenario in CENARIOS:
            todos = projecao.domicilios(ano, cenario)
            moradores_todos = moradores_projetados(todos, {c: base.celulas[c].moradores for c in todos})
            sim = celulas_do_simulador(cliente, ano, cenario, params)
            for recorte in Recorte:
                panorama = serie(cliente, recorte, params)[ano][cenario]["consumo_total_calibrado_kwh_mes"]
                celulas = [c for c in CELULAS_DO_RECORTE[recorte] if c in todos]
                bruto = consumo_total({c: todos[c] for c in celulas}, {c: base.celulas[c].consumo_domicilio for c in celulas})
                calculado = consumo_calibrado(bruto, projecao.populacao_total[ano], moradores_todos)
                pela_api = soma(sim[c]["consumo_total_calibrado_kwh_mes"] for c in CELULAS_DO_RECORTE[recorte] if sim.get(c))
                if panorama is None:
                    continue
                if abs(calculado - panorama) > 0.5:
                    divergencias.append(("projeção", ano, cenario, recorte.value, calculado, panorama))
                if pela_api is None or abs(pela_api - panorama) > len(CELULAS_DO_RECORTE[recorte]):
                    divergencias.append(("simulador", ano, cenario, recorte.value, pela_api, panorama))
    return divergencias


# ---------- 2. composição = proporções das células da projeção ----------


def checar_composicao(cliente, params):
    r = cliente.get("/arranjos/composicao", params=_sim(params))
    assert r.status_code == 200, r.text
    corpo = r.json()
    por_ano = {a: i for i, a in enumerate(corpo["anos"])}
    divergencias = []
    for ano in ANOS:
        sim = celulas_do_simulador(cliente, ano, "taxas", params)
        for categoria in corpo["categorias"]:
            composicao = categoria["participacao_pct"][por_ano[ano]]
            celulas = [c for c in sim if sim[c] and categoria_da_celula(c) == categoria["id"]]
            pela_projecao = soma(sim[c]["participacao_pct"] for c in celulas) or 0.0
            if abs(composicao - pela_projecao) > 0.01 * (len(celulas) + 1):
                divergencias.append((ano, categoria["id"], composicao, pela_projecao))
    assert {c["id"] for c in corpo["categorias"]} == {i for i, _, _ in CATEGORIAS}
    return divergencias


# ---------- 3. participação de 60+ na pirâmide = a do Panorama ----------


def checar_participacao_60_mais(cliente, params):
    r = cliente.get("/estrutura-etaria/piramides", params={"localidade": params["localidade"], "k": params["k"]})
    assert r.status_code == 200, r.text
    piramide = {p["ano"]: p["participacao_60_mais_pct"] for p in r.json()["piramides"]}
    panorama = serie(cliente, Recorte.todos_domicilios, params)
    divergencias = []
    for ano, ponto in panorama.items():
        p = ponto["_ponto"]["participacao_60_mais_pct"]
        if ano in piramide and p is not None and abs(piramide[ano] - p) > 0.01:
            divergencias.append((ano, piramide[ano], p))
    return divergencias


# ---------- 4. células do Simulador somam o total do ano ----------


def checar_totais_do_simulador(cliente, params):
    divergencias = []
    for ano in ANOS:
        for cenario in CENARIOS:
            sim = celulas_do_simulador(cliente, ano, cenario, params)
            presentes = [c for c in sim.values() if c]
            soma_dom = sum(c["domicilios_projetados"] for c in presentes)
            # o total do ano está implícito em cada célula: domicílios / participação. A participação vem
            # com duas casas (erro de até 0,005 ponto), então o total implícito erra até total * 0,005 / participação
            maior = max(presentes, key=lambda c: c["participacao_pct"])
            total_do_ano = maior["domicilios_projetados"] / (maior["participacao_pct"] / 100)
            limite = total_do_ano * 0.005 / maior["participacao_pct"] + len(presentes)
            if abs(soma_dom - total_do_ano) > limite:
                divergencias.append(("domicílios", ano, cenario, soma_dom, total_do_ano))
            comparacao = cliente.get(
                "/comparacao", params={"grupos": "todos_60,todos_59", "forma": "absoluto", "cenario": cenario, **_sim(params)}
            ).json()
            total_cmp = soma(next(p["valor"] for p in g["pontos"] if p["ano"] == ano) for g in comparacao["grupos"])
            if total_cmp is not None and abs(soma_dom - total_cmp) > len(presentes) + 2:
                divergencias.append(("domicílios na comparação", ano, cenario, soma_dom, total_cmp))
            soma_consumo = sum(c["consumo_total_calibrado_kwh_mes"] for c in presentes)
            todos = serie(cliente, Recorte.todos_domicilios, params)[ano][cenario]["consumo_total_calibrado_kwh_mes"]
            if todos is not None and abs(soma_consumo - todos) > len(presentes):
                divergencias.append(("consumo", ano, cenario, soma_consumo, todos))
    return divergencias


# ---------- 5. exportação = API ----------


def _numero(texto):
    return None if texto in ("", None) else float(texto)


def checar_exportacao(cliente, params):
    divergencias = []
    r = cliente.get("/exportar", params={"formato": "csv", "escopo": "serie", **_sim(params)})
    assert r.status_code == 200, r.text
    linhas = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    for recorte in Recorte:
        api = serie(cliente, recorte, params)
        for linha in (l for l in linhas if l["recorte"] == recorte.value):
            cenario = api[int(linha["ano"])][linha["cenario"]]
            ponto = api[int(linha["ano"])]["_ponto"]
            pares = [
                ("valor_tbc_kwh", cenario["valor"]),
                ("consumo_por_pessoa_kwh", cenario["consumo_por_pessoa_kwh"]),
                ("consumo_total_calibrado_kwh_mes", cenario["consumo_total_calibrado_kwh_mes"]),
                ("participacao_consumo_pct", cenario["participacao_consumo_pct"]),
                ("participacao_60_mais_pct", ponto["participacao_60_mais_pct"]),
                ("efeito_envelhecimento_total_kwh_mes", ponto["efeito_envelhecimento_total_kwh_mes"]),
                ("efeito_idade_kwh", ponto["efeito_idade_kwh"]),
                ("efeito_arranjos_participacao_pp", ponto["efeito_arranjos_participacao_pp"]),
            ]
            for coluna, esperado in pares:
                if _numero(linha[coluna]) != esperado:
                    divergencias.append(("exportar", recorte.value, linha["ano"], linha["cenario"], coluna, linha[coluna], esperado))
    grupos = "uni_60,cas_60,mul_60,mono_60,todos_59"
    for indicador in ("domicilios", "consumo_total", "participacao"):
        consulta = {"grupos": grupos, "indicador": indicador, "forma": "indice", **_sim(params)}
        api = cliente.get("/comparacao", params=consulta).json()
        arquivo = cliente.get("/exportar/comparacao", params={**consulta, "formato": "csv"})
        linhas_cmp = {(l["grupo"], int(l["ano"])): l for l in csv.DictReader(io.StringIO(arquivo.content.decode("utf-8-sig")))}
        for g in api["grupos"]:
            for p in g["pontos"]:
                linha = linhas_cmp[(g["id"], p["ano"])]
                for campo in ("valor", "valor_absoluto", "indice"):
                    if _numero(linha[campo]) != p[campo]:
                        divergencias.append(("exportar/comparacao", indicador, g["id"], p["ano"], campo, linha[campo], p[campo]))
    return divergencias


# ---------- 6. comparação = Panorama nos agregados equivalentes ----------

CAMPO_DO_INDICADOR = {
    "consumo_total": "consumo_total_calibrado_kwh_mes",
    "participacao": "participacao_consumo_pct",
    "consumo_por_pessoa": "consumo_por_pessoa_kwh",
}


def checar_comparacao_e_panorama(cliente, params):
    divergencias = []
    grupos = ",".join(g.value for g in RECORTE_DO_GRUPO)
    for cenario in CENARIOS:
        for indicador, campo in CAMPO_DO_INDICADOR.items():
            r = cliente.get(
                "/comparacao", params={"grupos": grupos, "indicador": indicador, "forma": "absoluto", "cenario": cenario, **_sim(params)}
            )
            assert r.status_code == 200, r.text
            for g in r.json()["grupos"]:
                recorte = next(rc for gid, rc in RECORTE_DO_GRUPO.items() if gid.value == g["id"])
                panorama = serie(cliente, recorte, params)
                for p in g["pontos"]:
                    esperado = panorama[p["ano"]][cenario][campo]
                    if p["valor"] != esperado:
                        divergencias.append((cenario, indicador, g["id"], p["ano"], p["valor"], esperado))
        # todos 60+ mais todos abaixo de 60 = todos os domicílios
        r = cliente.get(
            "/comparacao", params={"grupos": "todos_60,todos_59", "indicador": "consumo_total", "forma": "absoluto", "cenario": cenario, **_sim(params)}
        ).json()
        todos = serie(cliente, Recorte.todos_domicilios, params)
        for ano in ANOS:
            soma_grupos = soma(next(p["valor"] for p in g["pontos"] if p["ano"] == ano) for g in r["grupos"])
            esperado = todos[ano][cenario]["consumo_total_calibrado_kwh_mes"]
            if soma_grupos is not None and esperado is not None and abs(soma_grupos - esperado) > 1:
                divergencias.append((cenario, "todos_60 + todos_59", ano, soma_grupos, esperado))
    return divergencias
