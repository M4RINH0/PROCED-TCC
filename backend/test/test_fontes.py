import pytest
from fastapi.testclient import TestClient

from app.dados import Domicilio, obter_dados
from app.main import criar_app
from app.services.fontes import cobertura


class RepositorioFalso:
    # soma dos pesos 34.450.000: metade dos 68,9 milhões de domicílios da POF
    def domicilios(self):
        return [Domicilio("Casal ou Dupla", 70, 90.0, peso=34_450_000.0)]


def test_cobertura_e_a_soma_dos_pesos_sobre_o_total_da_pof():
    # 63.684.287 / 68.900.000 = 92,43%
    assert cobertura(63_684_287) == 92.4
    assert cobertura(5, total=10) == 50.0
    with pytest.raises(ValueError):
        cobertura(1, total=0)


def test_fontes_criterio_cobertura_e_premissas():
    app = criar_app()
    app.dependency_overrides[obter_dados] = RepositorioFalso
    r = TestClient(app).get("/fontes")
    assert r.status_code == 200
    corpo = r.json()
    fontes = {f["id"]: f for f in corpo["fontes"]}
    assert fontes["pof"]["periodo"] == "2017 a 2018"
    assert fontes["projecao"]["periodo"].startswith("2000 a 2070")
    assert all(f["nome"] and f["uso"] for f in fontes.values())
    assert "kWh" in corpo["criterio_exclusao"]
    assert corpo["cobertura_pct"] == 50.0
    assert [p["id"] for p in corpo["premissas"]] == ["P2", "P8", "P9", "P10", "P11", "P12", "P13", "P14"]
    assert corpo["premissas_url"].endswith("docs/premissas.md")
    assert "oficial" not in r.text


def test_fontes_incluem_as_pofs_da_tendencia_dos_arranjos():
    from app.services.fontes import FONTES

    historica = next(f for f in FONTES if f.id == "pof_historica")
    assert historica.periodo == "2002 a 2003 e 2008 a 2009"
    assert "P13" in historica.uso


def test_p2_antiga_saiu_e_p13_e_p14_entraram():
    from app.services.fontes import PREMISSAS

    textos = {p.id: p.texto for p in PREMISSAS}
    # a P2 antiga dizia que a taxa era constante por faixa e arranjo, o que congelava os arranjos
    assert "congela os arranjos" not in textos["P2"] and "P13" in textos["P2"]
    assert "0,6" in textos["P13"] and "2002 a 2003" in textos["P13"]
    assert "k = 1" in textos["P14"]


def test_premissas_da_gaveta_existem_em_docs_e_nao_estao_revogadas():
    import re
    from pathlib import Path

    from app.services.fontes import PREMISSAS

    doc = (Path(__file__).resolve().parents[2] / "docs" / "premissas.md").read_text(encoding="utf-8")
    linhas = {m.group(1): m.group(0) for m in re.finditer(r"^\| (P\d+) \|.*$", doc, flags=re.M)}
    for premissa in PREMISSAS:
        assert premissa.id in linhas, premissa.id
        assert "Revogada" not in linhas[premissa.id], premissa.id
    # toda premissa em vigor que muda os resultados exibidos está na gaveta (P1 e P4 a P7 são de recorte e faixa)
    em_vigor = {i for i, l in linhas.items() if "Revogada" not in l}
    assert em_vigor - {p.id for p in PREMISSAS} == {"P1", "P4", "P5", "P6", "P7"}
