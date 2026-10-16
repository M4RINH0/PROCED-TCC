"""Comparação de grupos (RF12): serviço, rota e exportação, com a base calculada à mão de dados_teste.

Domicílios projetados (taxa de chefia de 2018 constante por faixa, sem tendência na base de teste):
    2026 repete 2018: 60 a 69 -> 2 (uni e casal); 70 a 79 -> 2 (uni e multi); 80+ -> 1 (casal)
    2030: 75 anos 1.000 e 90 anos 500 -> 70 a 79 -> 4 (2 uni e 2 multi); 80+ -> 2
    mono_60 = 60 a 69 (2) + uni de 70 a 79 + casal de 80+: 4 em 2026 e 2 + 2 + 2 = 6 em 2030
    todos_60 = 5 em 2026 e 2 + 4 + 2 = 8 em 2030
Consumo total calibrado de mono_60 em 2026: bruto 100 + 120 + 150 + 200 = 570 kWh; a população
total de 2026 é 8.750 e os moradores projetados de todas as células são 8, fator 1.093,75;
570 * 1.093,75 = 623.437,5 -> 623.438.
"""

import codecs
import csv
import io

import pytest
from fastapi.testclient import TestClient

from app.calculo import indice, variacao
from app.dados import obter_dados
from app.dominio import CELULAS_DO_RECORTE, GRUPOS, RECORTE_DO_GRUPO, GrupoId, Recorte, celulas_do_grupo
from app.main import criar_app
from app.schemas.comparacao import FormaComparacao, IndicadorComparacao
from app.schemas.panorama import CenarioId
from app.services.comparacao import SEM_AMOSTRA, SEM_POR_PESSOA, obter_comparacao, ordem_de_crescimento, validar_grupos
from app.services.panorama import obter_projecao
from test.dados_teste import POPULACAO, RepositorioFalso

app = criar_app()
app.dependency_overrides[obter_dados] = RepositorioFalso
cliente = TestClient(app)


def _valores(resposta, grupo, anos=(2026, 2030, 2070)):
    serie = next(g for g in resposta.grupos if g.id == grupo)
    return [p.valor for p in serie.pontos if p.ano in anos]


# ---------- fórmulas e regras ----------


def test_indice_e_variacao_calculados_a_mao():
    assert indice(6, 4) == pytest.approx(150)
    assert indice(None, 4) is None and indice(5, 0) is None and indice(5, None) is None
    assert variacao(4, 6) == pytest.approx((2, 50))
    assert variacao(0, 3) == (3, None)  # sem base, sem variação percentual
    assert variacao(None, 3) == (None, None)


def test_ordem_de_crescimento_poe_o_maior_primeiro_e_ignora_sem_valor():
    assert ordem_de_crescimento([10.0, None, 30.0, -5.0]) == [2, None, 1, 3]
    assert ordem_de_crescimento([None, None]) == [None, None]


@pytest.mark.parametrize(
    "grupos",
    [[GrupoId.mono_60], list(GrupoId)[:7], [GrupoId.mono_60, GrupoId.mono_60]],
    ids=["um grupo", "sete grupos", "repetido"],
)
def test_validar_grupos_exige_de_2_a_6_sem_repeticao(grupos):
    with pytest.raises(ValueError):
        validar_grupos(grupos)


def test_agregados_tem_as_mesmas_celulas_dos_recortes_do_panorama():
    for grupo, recorte in RECORTE_DO_GRUPO.items():
        assert set(celulas_do_grupo(grupo)) == set(CELULAS_DO_RECORTE[recorte])
    # as seis células cobrem todos os domicílios, cada célula uma vez
    celulas = [c for g in GrupoId if not GRUPOS[g].agregado for c in celulas_do_grupo(g)]
    assert len(celulas) == len(set(celulas)) == len(CELULAS_DO_RECORTE[Recorte.todos_domicilios])


# ---------- serviço ----------


def test_domicilios_absolutos_e_indice_calculados_a_mao():
    absoluto = obter_comparacao([GrupoId.mono_60, GrupoId.todos_60], RepositorioFalso(), forma=FormaComparacao.absoluto)
    assert _valores(absoluto, GrupoId.mono_60) == [4, 6, 4]
    assert _valores(absoluto, GrupoId.todos_60) == [5, 8, 5]
    ind = obter_comparacao([GrupoId.mono_60, GrupoId.todos_60], RepositorioFalso())  # padrão: índice
    assert ind.forma == FormaComparacao.indice and ind.unidade == "domicílios"
    assert _valores(ind, GrupoId.mono_60) == [100.0, 150.0, 100.0]
    assert _valores(ind, GrupoId.todos_60) == [100.0, 160.0, 100.0]


def test_consumo_total_calibrado_calculado_a_mao():
    r = obter_comparacao([GrupoId.mono_60, GrupoId.todos_60], RepositorioFalso(), IndicadorComparacao.consumo_total, FormaComparacao.absoluto)
    assert _valores(r, GrupoId.mono_60, (2026,)) == [623438]
    assert r.unidade == "kWh/mês"


def test_tabela_com_2026_2050_2070_variacao_e_ordem():
    # 2070 com 75 anos 1.000 (o resto como em 2018): 70 a 79 -> 4 domicílios (2 uni e 2 multi)
    # mono_60: 4 em 2026 e 2 + 2 + 1 = 5 em 2070 (+1, +25%); todos_60: 5 e 2 + 4 + 1 = 7 (+2, +40%)
    populacao = {**POPULACAO, 2070: {**POPULACAO[2018], 75: 1000}}
    r = obter_comparacao([GrupoId.mono_60, GrupoId.todos_60], RepositorioFalso(populacao=populacao))
    mono, todos = r.tabela
    # sem população de 2050 na base de teste, a coluna fica sem valor
    assert (mono.valor_2026, mono.valor_2050, mono.valor_2070) == (4, None, 5)
    assert (mono.variacao_absoluta, mono.variacao_pct) == (1, 25.0)
    assert (todos.variacao_absoluta, todos.variacao_pct) == (2, 40.0)
    assert (mono.ordem, todos.ordem) == (2, 1)  # todos_60 cresce mais rápido


def test_consumo_por_pessoa_so_para_agregados():
    r = obter_comparacao([GrupoId.mono_60, GrupoId.cas_59], RepositorioFalso(), IndicadorComparacao.consumo_por_pessoa, FormaComparacao.absoluto)
    mono, casal = r.grupos
    assert mono.motivo_sem_valor is None and _valores(r, GrupoId.mono_60, (2030,)) == [153.3]
    assert casal.motivo_sem_valor == SEM_POR_PESSOA
    assert all(p.valor is None for p in casal.pontos)
    assert r.tabela[1].ordem is None


def test_grupo_sem_amostra_numa_faixa_fica_sem_valor_e_avisa():
    # a base de teste não tem unipessoal com chefe de 80 anos ou mais
    r = obter_comparacao([GrupoId.uni_60, GrupoId.mono_60], RepositorioFalso())
    uni = r.grupos[0]
    assert uni.motivo_sem_valor == SEM_AMOSTRA and all(p.valor is None for p in uni.pontos)
    assert uni.baixa_confiabilidade is True and uni.arranjo.value == "unipessoal" and uni.agregado is False


def test_agregados_batem_com_o_panorama_na_base_de_teste():
    r = obter_comparacao([GrupoId.mono_60, GrupoId.todos_60], RepositorioFalso(), IndicadorComparacao.consumo_total, FormaComparacao.absoluto)
    for grupo, recorte in ((GrupoId.mono_60, Recorte.chefe_60_mais), (GrupoId.todos_60, Recorte.chefe_60_mais_todos)):
        taxas = next(c for c in obter_projecao(2030, recorte, RepositorioFalso()).cenarios if c.id == CenarioId.taxas)
        assert _valores(r, grupo, (2030,)) == [taxas.consumo_total_calibrado_kwh_mes]


def test_cenario_e_controles_de_simulacao_chegam_a_resposta():
    r = obter_comparacao([GrupoId.mono_60, GrupoId.mono_59], RepositorioFalso(), cenario=CenarioId.contrafactual, k=1.2, intensidade=1.0)
    assert r.cenario == CenarioId.contrafactual and r.simulacao is True and (r.k, r.intensidade) == (1.2, 1.0)
    assert "IBGE" in r.fonte and "oficial" not in r.fonte


# ---------- rota ----------


def test_rota_devolve_a_comparacao():
    r = cliente.get("/comparacao", params={"grupos": "mono_60,todos_60", "forma": "absoluto"})
    assert r.status_code == 200
    corpo = r.json()
    assert [g["id"] for g in corpo["grupos"]] == ["mono_60", "todos_60"]
    assert [p["valor"] for p in corpo["grupos"][0]["pontos"][:1]] == [4]
    assert len(corpo["grupos"][0]["pontos"]) == 45


@pytest.mark.parametrize(
    "params",
    [
        {"grupos": "mono_60"},
        {"grupos": "mono_60,xyz"},
        {"grupos": "mono_60,mono_60"},
        {"grupos": "uni_60,cas_60,mul_60,uni_59,cas_59,mul_59,mono_60"},
        {"grupos": "mono_60,todos_60", "indicador": "renda"},
        {"grupos": "mono_60,todos_60", "forma": "log"},
        {"grupos": "mono_60,todos_60", "cenario": "ml_rf"},
        {"grupos": "mono_60,todos_60", "localidade": "XX"},
        {"grupos": "mono_60,todos_60", "k": 3},
        {},
    ],
)
def test_rota_rejeita_parametro_invalido(params):
    assert cliente.get("/comparacao", params=params).status_code == 422


# ---------- exportação (RF08) ----------


def _ler_csv(conteudo: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(conteudo.decode("utf-8-sig"))))


def test_exporta_a_comparacao_com_os_mesmos_valores_da_api():
    params = {"grupos": "mono_60,todos_60", "indicador": "participacao", "forma": "indice"}
    api = cliente.get("/comparacao", params=params).json()
    r = cliente.get("/exportar/comparacao", params={**params, "formato": "csv"})
    assert r.status_code == 200 and r.content.startswith(codecs.BOM_UTF8)
    assert r.headers["content-disposition"] == 'attachment; filename="proced_comparacao_Brasil_2026_2070.csv"'
    linhas = _ler_csv(r.content)
    assert len(linhas) == 2 * 45
    for grupo in api["grupos"]:
        for ponto in grupo["pontos"]:
            linha = next(l for l in linhas if l["grupo"] == grupo["id"] and int(l["ano"]) == ponto["ano"])
            for campo in ("valor", "valor_absoluto", "indice"):
                assert (float(linha[campo]) if linha[campo] else None) == ponto[campo]
    assert {l["baixa_confiabilidade"] for l in linhas} <= {"true", "false"}
    assert {l["versao_modelo"] for l in linhas} and len({l["gerado_em"] for l in linhas}) == 1


def test_exporta_a_comparacao_em_xlsx_e_valida_os_grupos():
    r = cliente.get("/exportar/comparacao", params={"grupos": "mono_60,todos_60", "formato": "xlsx"})
    assert r.status_code == 200 and r.content[:2] == b"PK"
    assert cliente.get("/exportar/comparacao", params={"grupos": "mono_60"}).status_code == 422
