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
    return list(csv.DictReader(io.StringIO(conteudo.decode("utf-8"))))


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
    assert len(linhas) == 20
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
    assert len(linhas) == 45 * 5
    assert {l["recorte"] for l in linhas} == {"chefe_60_mais"}
    assert {l["localidade"] for l in linhas} == {"SP"}
    assert linhas[0]["ano"] == "2026" and linhas[-1]["ano"] == "2070"
    assert linhas[0]["intensidade"] == "1.1" and linhas[0]["k"] == "1.2" and linhas[0]["simulacao"] == "True"


def test_exporta_xlsx_valido_com_cabecalho_e_dados():
    r = cliente.get("/exportar", params={"formato": "xlsx", "escopo": "ano", "ano": 2030, "recorte": "chefe_60_mais"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.headers["content-disposition"] == 'attachment; filename="proced_Brasil_2030.xlsx"'
    linhas = _ler_xlsx(r.content)
    assert tuple(linhas[0]) == COLUNAS
    assert len(linhas) == 6
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
