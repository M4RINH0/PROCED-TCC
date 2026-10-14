from app.dados import Dados, Domicilio
from app.dominio import UFS


def _linha(id_domicilio, idade, peso=500.0):
    return {
        "id_domicilio": id_domicilio, "sigla_uf": "DF", "arranjo_familiar": "Casal ou Dupla", "idade_chefe": idade,
        "qtd_moradores": 2, "consumo_total_kwh": 185, "consumo_per_capita_kwh": 92.5, "peso_final": peso,
    }


class ClienteFalso:
    def __init__(self, domicilios=None):
        self.chamadas = []
        self._domicilios = domicilios or [_linha(1, 70)]

    def selecionar(self, tabela, colunas, filtros=None):
        self.chamadas.append((tabela, colunas, filtros))
        if tabela == "fato_consumo_domiciliar":
            return self._domicilios
        return [
            {"localidade": "DF", "sexo": "Ambos", "ano": 2018, "idade": 60, "populacao": 10},
            {"localidade": "GO", "sexo": "Ambos", "ano": 2018, "idade": 61, "populacao": 20},
            {"localidade": "DF", "sexo": "Ambos", "ano": 2030, "idade": 60, "populacao": 30},
            {"localidade": "Brasil", "sexo": "Ambos", "ano": 2018, "idade": 60, "populacao": 999},
            {"localidade": "Centro-Oeste", "sexo": "Ambos", "ano": 2018, "idade": 60, "populacao": 999},
        ]


def test_converte_linhas_de_domicilio_com_peso_e_consumo_total():
    repo = Dados(ClienteFalso())
    assert repo.domicilios() == [Domicilio("Casal ou Dupla", 70, 92.5, "DF", 500.0, 185.0, 2, 1)]
    _, colunas, _ = repo._cliente.chamadas[0]
    assert "peso_final" in colunas and "id_domicilio" in colunas


def test_domicilio_repetido_fica_com_o_chefe_mais_velho():
    # P8: o id 1 aparece com chefes de 52 e 77 anos; fica o de 77
    repo = Dados(ClienteFalso([_linha(1, 52), _linha(1, 77), _linha(2, 40)]))
    assert [(d.id_domicilio, d.idade_chefe) for d in repo.domicilios()] == [(1, 77), (2, 40)]


def test_populacao_do_brasil_soma_as_27_ufs_sem_as_linhas_de_total():
    # DF e GO entram; as linhas "Brasil" e "Centro-Oeste" (999) não
    cliente = ClienteFalso()
    repo = Dados(cliente)
    assert repo.populacao_por_idade() == {2018: {60: 10, 61: 20}, 2030: {60: 30}}
    tabela, _, filtros = cliente.chamadas[0]
    assert tabela == "projecoes_populacao_idade"
    assert filtros["localidade"] == f"in.({','.join(UFS)})" and filtros["sexo"] == "eq.Ambos"


def test_le_cada_tabela_uma_vez_so():
    cliente = ClienteFalso()
    repo = Dados(cliente)
    repo.domicilios(), repo.domicilios(), repo.populacao_por_idade(), repo.populacao_por_idade()
    assert len(cliente.chamadas) == 2


def test_le_as_pofs_anteriores_sem_filtrar_a_rede_geral():
    from app.dados import DomicilioHistorico

    class Cliente:
        def selecionar(self, tabela, colunas, filtros=None):
            assert tabela == "fato_consumo_pof_historica" and "energia_rede_geral" in colunas
            return [
                {"ano_pof": 2002, "arranjo_familiar": "Casal ou Dupla", "idade_chefe": 70, "peso_final": 10.5, "energia_rede_geral": False},
                {"ano_pof": 2008, "arranjo_familiar": "Multipessoal (3+)", "idade_chefe": 40, "peso_final": 3.0, "energia_rede_geral": True},
            ]

    historicos = Dados(Cliente()).domicilios_historicos()
    assert historicos == [
        DomicilioHistorico(2002, "Casal ou Dupla", 70, 10.5, False),
        DomicilioHistorico(2008, "Multipessoal (3+)", 40, 3.0, True),
    ]


def test_derivado_calcula_uma_vez_por_chave():
    repo = Dados(ClienteFalso())
    contagem = []
    calcular = lambda: contagem.append(1) or len(contagem)  # noqa: E731
    assert repo.derivado("x", calcular) == 1
    assert repo.derivado("x", calcular) == 1
    assert repo.derivado("y", calcular) == 2
    assert len(contagem) == 2


def test_uma_chave_lenta_nao_bloqueia_outra():
    import threading
    import time

    repo = Dados(ClienteFalso())
    liberar = threading.Event()

    def lento():
        liberar.wait(2)
        return "lento"

    t = threading.Thread(target=lambda: repo.derivado("lenta", lento))
    t.start()
    time.sleep(0.05)
    inicio = time.time()
    assert repo.derivado("rapida", lambda: "ok") == "ok"
    assert time.time() - inicio < 0.5  # não esperou a chave lenta
    liberar.set()
    t.join()
    assert repo.derivado("lenta", lambda: "outro") == "lento"


def test_memorizado_sem_cache_calcula_na_hora():
    from app.dominio import memorizado

    class SemCache:
        pass

    assert memorizado(SemCache(), "x", lambda: 42) == 42
    repo = Dados(ClienteFalso())
    assert memorizado(repo, "x", lambda: 1) == 1 and memorizado(repo, "x", lambda: 2) == 1
