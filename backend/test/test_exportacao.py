import codecs
import csv
import io
import xml.etree.ElementTree as ET
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.dados import obter_dados
from app.main import criar_app
from app.services.exportacao import COLUNAS
from test.dados_teste import RepositorioFalso

app = criar_app()
app.dependency_overrides[obter_dados] = RepositorioFalso
cliente = TestClient(app)


def _ler_csv(conteudo: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(conteudo.decode("utf-8-sig"))))  # o arquivo tem BOM


def _ler_xlsx(conteudo: bytes) -> list[list[str]]:
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo:
        arvore = ET.fromstring(arquivo.read("xl/worksheets/sheet1.xml"))
    linhas = []
    for row in arvore.findall(".//s:sheetData/s:row", ns):
        valores = []
        for celula in row.findall("s:c", ns):
            texto = celula.find(".//s:t", ns)
            numero = celula.find("s:v", ns)
            valores.append(texto.text if texto is not None else (numero.text if numero is not None else ""))
        linhas.append(valores)
    return linhas


def test_exporta_csv_do_ano_selecionado_com_coluna_de_origem():
    r = cliente.get("/exportar", params={"formato": "csv", "escopo": "ano", "ano": 2030})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert r.headers["content-disposition"] == 'attachment; filename="proced_Brasil_2030.csv"'
    linhas = _ler_csv(r.content)
    # quatro recortes e três cenários (taxas, só o envelhecimento e contrafactual), sem machine learning
    assert len(linhas) == 12
    assert {l["cenario"] for l in linhas} == {"taxas", "taxas_arranjos_fixos", "contrafactual"}
    assert tuple(linhas[0].keys()) == COLUNAS
    taxas_mono = next(l for l in linhas if l["recorte"] == "chefe_60_mais" and l["cenario"] == "taxas")
    assert taxas_mono["ano"] == "2030"
    assert taxas_mono["valor_tbc_kwh"] == "153.3"
    assert taxas_mono["consumo_total_calibrado_kwh_mes"] == "794545"
    assert taxas_mono["efeito_envelhecimento_kwh"] == "10.8"
    assert taxas_mono["fonte"].startswith("POF 2002 a 2003")


def test_exporta_serie_completa_em_csv_para_um_recorte():
    r = cliente.get(
        "/exportar",
        params={"formato": "csv", "escopo": "serie", "recorte": "chefe_60_mais", "localidade": "SP", "intensidade": 1.1, "k": 1.2},
    )
    assert r.status_code == 200
    assert r.headers["content-disposition"] == 'attachment; filename="proced_SP_2026_2070.csv"'
    linhas = _ler_csv(r.content)
    assert len(linhas) == 45 * 3
    assert {l["recorte"] for l in linhas} == {"chefe_60_mais"}
    assert {l["localidade"] for l in linhas} == {"SP"}
    assert linhas[0]["ano"] == "2026" and linhas[-1]["ano"] == "2070"
    assert linhas[0]["intensidade"] == "1.1" and linhas[0]["k"] == "1.2" and linhas[0]["simulacao"] == "true"


def test_exporta_xlsx_valido_com_cabecalho_e_dados():
    r = cliente.get("/exportar", params={"formato": "xlsx", "escopo": "ano", "ano": 2030, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.headers["content-disposition"] == 'attachment; filename="proced_Brasil_2030.xlsx"'
    linhas = _ler_xlsx(r.content)
    assert tuple(linhas[0]) == COLUNAS
    assert len(linhas) == 4  # cabeçalho e os três cenários
    assert "153.3" in linhas[1]
    assert any("POF 2002 a 2003" in v for v in linhas[1])


@pytest.mark.parametrize(
    "params",
    [
        {"formato": "pdf"},
        {"escopo": "mensal"},
        {"ano": 2020},
        {"ano": 2075},
        {"intensidade": 2.0},
        {"k": 0.1},
        {"localidade": "XX"},
    ],
)
def test_parametros_invalidos_retornam_422(params):
    assert cliente.get("/exportar", params=params).status_code == 422


def test_csv_tem_bom_utf8_para_o_excel_em_portugues():
    r = cliente.get("/exportar", params={"formato": "csv", "recorte": "chefe_60_mais"})
    assert r.content.startswith(codecs.BOM_UTF8)
    assert "Projeções".encode("utf-8") in r.content  # acento em UTF-8 depois do BOM


def test_os_dois_formatos_trazem_versao_do_modelo_e_data_de_geracao():
    from datetime import datetime

    from app.dominio import VERSAO_MODELO

    csv_ = _ler_csv(cliente.get("/exportar", params={"formato": "csv", "recorte": "chefe_60_mais"}).content)
    assert {l["versao_modelo"] for l in csv_} == {VERSAO_MODELO}
    assert len({l["gerado_em"] for l in csv_}) == 1  # a mesma data em todas as linhas
    assert datetime.fromisoformat(csv_[0]["gerado_em"]).tzinfo is not None
    xlsx = _ler_xlsx(cliente.get("/exportar", params={"formato": "xlsx", "recorte": "chefe_60_mais"}).content)
    cabecalho = xlsx[0]
    assert cabecalho[-2:] == ["versao_modelo", "gerado_em"]
    assert xlsx[1][cabecalho.index("versao_modelo")] == VERSAO_MODELO
    datetime.fromisoformat(xlsx[1][cabecalho.index("gerado_em")])


def test_data_de_geracao_pode_ser_fixada():
    from app.services.exportacao import montar_linhas

    linhas = montar_linhas(RepositorioFalso(), recorte=None, gerado_em="2026-10-16T10:00:00-03:00")
    assert {l["gerado_em"] for l in linhas} == {"2026-10-16T10:00:00-03:00"}


@pytest.mark.parametrize("valor, esperado", [(True, "true"), (False, "false"), (0, 0), (1, 1), (None, None), ("x", "x")])
def test_logico_escreve_true_e_false_em_minusculas_e_preserva_o_resto(valor, esperado):
    from app.services.exportacao import logico

    resultado = logico(valor)
    assert resultado == esperado and type(resultado) is type(esperado)


def test_valores_logicos_saem_em_minusculas_no_csv_e_no_xlsx():
    from app.services.exportacao import gerar_csv, gerar_xlsx

    linha = {c: None for c in COLUNAS} | {"ano": 2050, "simulacao": True, "baixa_confiabilidade": False}
    csv_lido = _ler_csv(gerar_csv([linha]))[0]
    assert csv_lido["simulacao"] == "true" and csv_lido["baixa_confiabilidade"] == "false"
    with zipfile.ZipFile(io.BytesIO(gerar_xlsx([linha]))) as arquivo:
        planilha = arquivo.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert 't="b"' not in planilha
    col = lambda nome: COLUNAS.index(nome) + 1  # noqa: E731
    from app.services.exportacao import _letra_coluna

    assert f'<c r="{_letra_coluna(col("simulacao"))}2" t="inlineStr"><is><t>true</t></is></c>' in planilha
    assert f'<c r="{_letra_coluna(col("baixa_confiabilidade"))}2" t="inlineStr"><is><t>false</t></is></c>' in planilha
    assert f'<c r="A2"><v>2050</v></c>' in planilha  # número continua número
