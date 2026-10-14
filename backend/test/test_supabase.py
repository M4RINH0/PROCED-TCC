import httpx
import pytest

from app.config import Configuracao, ErroConfiguracao, ErroFonteDados
from app.supabase import ClienteSupabase, criar_cliente, total_do_intervalo


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


def _com_contagem(linhas, maximo_do_servidor):
    """Servidor que informa o total e devolve no máximo `maximo_do_servidor` linhas por página."""

    def manipulador(req):
        ini, fim = map(int, req.headers["Range"].split("-"))
        fim = min(fim, ini + maximo_do_servidor - 1)
        pagina = linhas[ini : fim + 1]
        cabecalhos = {"content-range": f"{ini}-{ini + len(pagina) - 1}/{len(linhas)}"}
        return httpx.Response(206, json=pagina, headers=cabecalhos)

    return manipulador


def test_le_todas_as_linhas_mesmo_com_paginas_menores_que_o_pedido():
    # o cliente pede 4 por página e o servidor só devolve 3: sem a contagem, pararia na primeira página
    linhas = [{"v": i} for i in range(10)]
    http = httpx.Client(transport=httpx.MockTransport(_com_contagem(linhas, 3)))
    cliente = ClienteSupabase("https://x.supabase.co", "k", http=http, tamanho_pagina=4)
    assert cliente.selecionar("t", "v") == linhas


def test_primeira_pagina_pede_a_contagem_exata():
    pedidos = []

    def manipulador(req):
        pedidos.append(req)
        return _com_contagem([{"v": 1}], 10)(req)

    _cliente(manipulador).selecionar("t", "v")
    assert pedidos[0].headers["Prefer"] == "count=exact"


def test_leitura_incompleta_vira_erro_de_fonte():
    def manipulador(req):
        ini = int(req.headers["Range"].split("-")[0])
        pagina = [{"v": 1}, {"v": 2}] if ini == 0 else []
        return httpx.Response(206, json=pagina, headers={"content-range": "0-1/5"})

    with pytest.raises(ErroFonteDados, match="2 de 5"):
        _cliente(manipulador).selecionar("t", "v")


def test_contar_le_o_total_do_cabecalho():
    pedidos = []

    def manipulador(req):
        pedidos.append(req)
        return httpx.Response(206, json=[{"v": 1}], headers={"content-range": "0-0/52207"})

    assert _cliente(manipulador).contar("t", {"sexo": "eq.Ambos"}) == 52207
    assert pedidos[0].headers["Range"] == "0-0" and pedidos[0].url.params["sexo"] == "eq.Ambos"


def test_contar_sem_cabecalho_vira_erro_de_fonte():
    with pytest.raises(ErroFonteDados):
        _cliente(lambda req: httpx.Response(200, json=[])).contar("t")


@pytest.mark.parametrize(
    "cabecalho, total", [("0-999/52207", 52207), ("*/0", 0), ("0-9/*", None), (None, None), ("", None)]
)
def test_total_do_intervalo(cabecalho, total):
    assert total_do_intervalo(cabecalho) == total
