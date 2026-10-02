import httpx
import pytest

from app.config import Configuracao, ErroConfiguracao, ErroFonteDados
from app.supabase import ClienteSupabase, criar_cliente


def _cliente(manipulador, pagina=2):
    http = httpx.Client(transport=httpx.MockTransport(manipulador))
    return ClienteSupabase("https://x.supabase.co/", "chave-teste", http=http, tamanho_pagina=pagina)


def test_pagina_ate_acabar_as_linhas_e_envia_chave_e_filtros():
    pedidos = []
    linhas = [{"v": i} for i in range(5)]

    def manipulador(req):
        pedidos.append(req)
        ini, fim = map(int, req.headers["Range"].split("-"))
        return httpx.Response(200, json=linhas[ini : fim + 1])

    resultado = _cliente(manipulador).selecionar("tabela", "v", {"localidade": "eq.Brasil"})
    assert resultado == linhas
    assert [p.headers["Range"] for p in pedidos] == ["0-1", "2-3", "4-5"]
    assert pedidos[0].headers["apikey"] == "chave-teste"
    assert pedidos[0].url.path == "/rest/v1/tabela"
    assert pedidos[0].url.params["select"] == "v"
    assert pedidos[0].url.params["localidade"] == "eq.Brasil"


def test_pagina_exata_faz_uma_consulta_a_mais_e_para():
    def manipulador(req):
        ini = int(req.headers["Range"].split("-")[0])
        return httpx.Response(200, json=[{"v": 1}, {"v": 2}] if ini == 0 else [])

    assert len(_cliente(manipulador).selecionar("t", "v")) == 2


def test_codigo_de_erro_vira_erro_de_fonte():
    with pytest.raises(ErroFonteDados, match="401"):
        _cliente(lambda req: httpx.Response(401, json={})).selecionar("t", "v")


def test_falha_de_rede_vira_erro_de_fonte():
    def manipulador(req):
        raise httpx.ConnectError("sem rede")

    with pytest.raises(ErroFonteDados):
        _cliente(manipulador).selecionar("t", "v")


def test_criar_cliente_exige_url_e_chave():
    with pytest.raises(ErroConfiguracao):
        criar_cliente(Configuracao(cors_origin="x", supabase_url="https://x"))
    cliente = criar_cliente(
        Configuracao(cors_origin="x", supabase_url="https://x", supabase_secret_key="k")
    )
    assert isinstance(cliente, ClienteSupabase)
