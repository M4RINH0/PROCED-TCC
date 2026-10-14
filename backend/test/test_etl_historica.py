import json

import httpx
import pandas as pd
import pytest

from etl import historica


def _linha(ano, id_, moradores=1, idade=70, kwh=120.0, peso=500.0):
    arranjo = {1: "Unipessoal (Mononuclear)", 2: "Casal ou Dupla"}.get(moradores, "Multipessoal (3+)")
    return {
        "ano_pof": ano, "sigla_uf": "DF", "id_domicilio": id_, "qtd_moradores": moradores, "arranjo_familiar": arranjo,
        "idade_chefe": idade, "is_60_mais": idade >= 60, "consumo_total_kwh": kwh,
        "consumo_per_capita_kwh": kwh / moradores, "peso_final": peso, "kwh_imputado": False, "energia_rede_geral": True,
    }


def _csvs(tmp_path, linhas2002, linhas2008):
    pd.DataFrame(linhas2002).to_csv(tmp_path / "a.csv", index=False)
    pd.DataFrame(linhas2008).to_csv(tmp_path / "b.csv", index=False)
    return {2002: "a.csv", 2008: "b.csv"}


def test_le_as_duas_edicoes_e_registra_a_origem(tmp_path):
    arquivos = _csvs(tmp_path, [_linha(2002, "2002-1"), _linha(2002, "2002-2", 3, 40, 300.0)], [_linha(2008, "2008-1", 2, 65, 200.0)])
    dados, registro = historica.ler(tmp_path, arquivos, {2002: 2, 2008: 1})
    assert len(dados) == 3 and list(dados.columns) == list(historica.COLUNAS)
    assert registro["linhas"] == {2002: 2, 2008: 1} and "IBGE" in registro["fonte"]
    assert dados["id_domicilio"].dtype == object  # o id é texto, como "2002-11-001-9-01"


def test_contagem_diferente_da_esperada_falha(tmp_path):
    arquivos = _csvs(tmp_path, [_linha(2002, "2002-1")], [_linha(2008, "2008-1")])
    with pytest.raises(ValueError, match="1 registros, esperados 39458"):
        historica.ler(tmp_path, arquivos)


def test_arquivo_ausente_falha(tmp_path):
    with pytest.raises(FileNotFoundError):
        historica.ler(tmp_path, {2002: "nao_existe.csv"}, {})


@pytest.mark.parametrize(
    "estrago, mensagem",
    [
        ({"ano_pof": 2008}, "outra edição"),
        ({"peso_final": 0.0}, "peso_final"),
        ({"arranjo_familiar": "Casal ou Dupla"}, "arranjo"),
        ({"is_60_mais": False}, "is_60_mais"),
        ({"consumo_per_capita_kwh": 1.0}, "per capita"),
        ({"sigla_uf": None}, "ausentes"),
    ],
)
def test_validacao_recusa_registro_inconsistente(estrago, mensagem):
    df = pd.DataFrame([{**_linha(2002, "2002-1"), **estrago}])
    with pytest.raises(ValueError, match=mensagem):
        historica.validar(df, 2002)


def test_validacao_recusa_id_repetido_e_coluna_ausente():
    with pytest.raises(ValueError, match="repetido"):
        historica.validar(pd.DataFrame([_linha(2002, "x"), _linha(2002, "x")]), 2002)
    with pytest.raises(ValueError, match="colunas ausentes"):
        historica.validar(pd.DataFrame([_linha(2002, "x")]).drop(columns="kwh_imputado"), 2002)


def test_carga_leva_os_fora_da_rede_geral():
    # o filtro da rede geral é aplicado no cálculo (P13), não na carga
    df = pd.DataFrame([{**_linha(2002, "a"), "energia_rede_geral": False}, _linha(2002, "b")])
    linhas = historica.linhas_para_carga(df)
    assert [l["energia_rede_geral"] for l in linhas] == [False, True]
    assert json.dumps(linhas)  # tipos nativos, serializáveis
    assert isinstance(linhas[0]["ano_pof"], int) and isinstance(linhas[0]["peso_final"], float)


def test_gravar_faz_upsert_em_lotes_com_a_chave():
    pedidos = []

    def manipulador(req):
        pedidos.append(req)
        return httpx.Response(201)

    http = httpx.Client(transport=httpx.MockTransport(manipulador))
    linhas = [{"ano_pof": 2002, "id_domicilio": str(i)} for i in range(5)]
    assert historica.gravar("https://x.supabase.co/", "chave", linhas, http=http, lote=2) == 5
    assert len(pedidos) == 3  # 2 + 2 + 1
    assert pedidos[0].url.path == "/rest/v1/fato_consumo_pof_historica"
    assert pedidos[0].url.params["on_conflict"] == "ano_pof,id_domicilio"
    assert "merge-duplicates" in pedidos[0].headers["Prefer"] and pedidos[0].headers["apikey"] == "chave"
    assert len(json.loads(pedidos[2].content)) == 1


def test_gravar_falha_com_erro_do_banco():
    http = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(404)))
    with pytest.raises(RuntimeError, match="404"):
        historica.gravar("https://x.supabase.co", "chave", [{"a": 1}], http=http)


class ClienteFalso:
    def __init__(self, contagens):
        self.contagens, self.filtros = contagens, []

    def contar(self, tabela, filtros=None):
        self.filtros.append(filtros)
        return self.contagens[int(filtros["ano_pof"].removeprefix("eq."))]


def test_conferir_o_count_no_banco():
    cliente = ClienteFalso({2002: 39458, 2008: 49268})
    assert historica.conferir(cliente) == {2002: 39458, 2008: 49268}
    assert cliente.filtros[0] == {"ano_pof": "eq.2002"}
    with pytest.raises(ValueError, match="49000 registros no banco"):
        historica.conferir(ClienteFalso({2002: 39458, 2008: 49000}))
