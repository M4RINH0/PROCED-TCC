import csv
import io
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

from app.dominio import ANO_FINAL, ANO_INICIAL, BRASIL, INTENSIDADE_PADRAO, K_PADRAO, Recorte
from app.schemas.exportacao import EscopoExportacao, FormatoExportacao
from app.schemas.panorama import Cenario, PontoSerie, SerieResposta
from app.services.panorama import obter_serie

COLUNAS = (
    "ano",
    "localidade",
    "recorte",
    "cenario",
    "unidade",
    "valor_tbc_kwh",
    "consumo_por_pessoa_kwh",
    "consumo_total_calibrado_kwh_mes",
    "participacao_consumo_pct",
    "variacao_kwh",
    "variacao_pct",
    "participacao_60_mais_pct",
    "efeito_envelhecimento_kwh",
    "efeito_idade_kwh",
    "efeito_arranjos_kwh",
    "efeito_envelhecimento_total_kwh_mes",
    "efeito_idade_total_kwh_mes",
    "efeito_arranjos_total_kwh_mes",
    "efeito_envelhecimento_participacao_pp",
    "efeito_idade_participacao_pp",
    "efeito_arranjos_participacao_pp",
    "intensidade",
    "k",
    "simulacao",
    "domicilios_amostra",
    "baixa_confiabilidade",
    "fonte",
)

TIPOS_MIDIA = {
    FormatoExportacao.csv: "text/csv; charset=utf-8",
    FormatoExportacao.xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Projecoes" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

WORKBOOK_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>"""


@dataclass(frozen=True)
class ArquivoExportado:
    conteudo: bytes
    media_type: str
    nome_arquivo: str


def _inteiro(valor: float | None) -> int | None:
    return None if valor is None else round(valor)


def _linha_cenario(serie: SerieResposta, ponto: PontoSerie, cenario: Cenario) -> dict[str, object]:
    return {
        "ano": ponto.ano,
        "localidade": serie.localidade,
        "recorte": serie.recorte.value,
        "cenario": cenario.id.value,
        "unidade": serie.unidade,
        "valor_tbc_kwh": cenario.valor,
        "consumo_por_pessoa_kwh": cenario.consumo_por_pessoa_kwh,
        "consumo_total_calibrado_kwh_mes": _inteiro(cenario.consumo_total_calibrado_kwh_mes),
        "participacao_consumo_pct": cenario.participacao_consumo_pct,
        "variacao_kwh": cenario.variacao_kwh,
        "variacao_pct": cenario.variacao_pct,
        "participacao_60_mais_pct": ponto.participacao_60_mais_pct,
        "efeito_envelhecimento_kwh": ponto.efeito_envelhecimento_kwh,
        "efeito_idade_kwh": ponto.efeito_idade_kwh,
        "efeito_arranjos_kwh": ponto.efeito_arranjos_kwh,
        "efeito_envelhecimento_total_kwh_mes": _inteiro(ponto.efeito_envelhecimento_total_kwh_mes),
        "efeito_idade_total_kwh_mes": _inteiro(ponto.efeito_idade_total_kwh_mes),
        "efeito_arranjos_total_kwh_mes": _inteiro(ponto.efeito_arranjos_total_kwh_mes),
        "efeito_envelhecimento_participacao_pp": ponto.efeito_envelhecimento_participacao_pp,
        "efeito_idade_participacao_pp": ponto.efeito_idade_participacao_pp,
        "efeito_arranjos_participacao_pp": ponto.efeito_arranjos_participacao_pp,
        "intensidade": serie.intensidade,
        "k": serie.k,
        "simulacao": serie.simulacao,
        "domicilios_amostra": serie.domicilios_amostra,
        "baixa_confiabilidade": serie.baixa_confiabilidade,
        "fonte": serie.fonte,
    }


def montar_linhas(
    dados,
    escopo: EscopoExportacao = EscopoExportacao.ano,
    ano: int = ANO_FINAL,
    recorte: Recorte | None = None,
    localidade: str = BRASIL,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
) -> list[dict[str, object]]:
    recortes = [recorte] if recorte is not None else list(Recorte)
    linhas: list[dict[str, object]] = []
    for item in recortes:
        serie = obter_serie(item, dados, localidade, intensidade, k)
        pontos = [p for p in serie.pontos if p.ano == ano] if escopo == EscopoExportacao.ano else serie.pontos
        for ponto in pontos:
            for cenario in ponto.cenarios:
                linhas.append(_linha_cenario(serie, ponto, cenario))
    return linhas


def gerar_csv(linhas: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUNAS, lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    return buffer.getvalue().encode("utf-8")


def _letra_coluna(indice: int) -> str:
    letras = ""
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _celula_xml(linha: int, coluna: int, valor: object) -> str:
    if valor is None:
        return ""
    ref = f"{_letra_coluna(coluna)}{linha}"
    if isinstance(valor, bool):
        return f'<c r="{ref}" t="b"><v>{1 if valor else 0}</v></c>'
    if isinstance(valor, (int, float)):
        return f'<c r="{ref}"><v>{valor}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(valor))}</t></is></c>'


def _planilha_xml(linhas: list[dict[str, object]]) -> str:
    todas = [COLUNAS, *([linha.get(c) for c in COLUNAS] for linha in linhas)]
    linhas_xml = []
    for indice_linha, valores in enumerate(todas, start=1):
        celulas = "".join(_celula_xml(indice_linha, indice_col, v) for indice_col, v in enumerate(valores, start=1))
        linhas_xml.append(f'<row r="{indice_linha}">{celulas}</row>')
    corpo = "".join(linhas_xml)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{corpo}</sheetData>"
        "</worksheet>"
    )


def gerar_xlsx(linhas: list[dict[str, object]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as arquivo:
        arquivo.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        arquivo.writestr("_rels/.rels", RELS_XML)
        arquivo.writestr("xl/workbook.xml", WORKBOOK_XML)
        arquivo.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
        arquivo.writestr("xl/styles.xml", STYLES_XML)
        arquivo.writestr("xl/worksheets/sheet1.xml", _planilha_xml(linhas))
    return buffer.getvalue()


def nome_arquivo(formato: FormatoExportacao, escopo: EscopoExportacao, ano: int, localidade: str) -> str:
    periodo = str(ano) if escopo == EscopoExportacao.ano else f"{ANO_INICIAL}_{ANO_FINAL}"
    local_limpo = localidade.replace(" ", "_")
    return f"proced_{local_limpo}_{periodo}.{formato.value}"


def exportar_dados(
    dados,
    formato: FormatoExportacao = FormatoExportacao.csv,
    escopo: EscopoExportacao = EscopoExportacao.ano,
    ano: int = ANO_FINAL,
    recorte: Recorte | None = None,
    localidade: str = BRASIL,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
) -> ArquivoExportado:
    linhas = montar_linhas(dados, escopo, ano, recorte, localidade, intensidade, k)
    conteudo = gerar_csv(linhas) if formato == FormatoExportacao.csv else gerar_xlsx(linhas)
    return ArquivoExportado(
        conteudo=conteudo,
        media_type=TIPOS_MIDIA[formato],
        nome_arquivo=nome_arquivo(formato, escopo, ano, localidade),
    )
