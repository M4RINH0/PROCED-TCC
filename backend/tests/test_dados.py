from app.dados import Dados, Domicilio


class ClienteFalso:
    def __init__(self):
        self.chamadas = []

    def selecionar(self, tabela, colunas, filtros=None):
        self.chamadas.append((tabela, colunas, filtros))
        if tabela == "fato_consumo_domiciliar":
            return [{"arranjo_familiar": "Casal ou Dupla", "idade_chefe": 70, "consumo_per_capita_kwh": 92.5}]
        return [
            {"ano": 2018, "idade": 60, "populacao": 10},
            {"ano": 2018, "idade": 61, "populacao": 20},
            {"ano": 2030, "idade": 60, "populacao": 30},
        ]


def test_converte_linhas_de_domicilio():
    repo = Dados(ClienteFalso())
    assert repo.domicilios() == [Domicilio("Casal ou Dupla", 70, 92.5)]


def test_agrupa_populacao_por_ano_e_idade_do_brasil_ambos_os_sexos():
    cliente = ClienteFalso()
    repo = Dados(cliente)
    assert repo.populacao_por_idade() == {2018: {60: 10, 61: 20}, 2030: {60: 30}}
    tabela, _, filtros = cliente.chamadas[0]
    assert tabela == "projecoes_populacao_idade"
    assert filtros["localidade"] == "eq.Brasil" and filtros["sexo"] == "eq.Ambos"


def test_le_cada_tabela_uma_vez_so():
    cliente = ClienteFalso()
    repo = Dados(cliente)
    repo.domicilios(), repo.domicilios(), repo.populacao_por_idade(), repo.populacao_por_idade()
    assert len(cliente.chamadas) == 2
