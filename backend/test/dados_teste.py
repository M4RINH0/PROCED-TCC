"""Dados pequenos para os testes, com resultados calculados à mão.

Recorte chefe 60+ (só mononucleares entram):
    60 a 69: dois domicílios, 100 e 120 kWh  -> TEC 110, n = 2
    70 a 79: um domicílio, 150 kWh            -> TEC 150, n = 1
    80+:     um domicílio, 200 kWh (idade 90) -> TEC 200, n = 1
População de 2018: 65 anos 1000, 75 anos 500, 90 anos 250
    chefia: 2/1000 = 0,002; 1/500 = 0,002; 1/250 = 0,004
A população de 2026 repete a de 2018: a composição do contrafactual é a da amostra.
Sem moradores informados, cada domicílio conta um morador.
"""

from app.dados import Domicilio
from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL

DOMICILIOS = [
    Domicilio(UNIPESSOAL, 62, 100.0),
    Domicilio(CASAL_OU_DUPLA, 68, 120.0),
    Domicilio(UNIPESSOAL, 75, 150.0),
    Domicilio(CASAL_OU_DUPLA, 90, 200.0),
    Domicilio(MULTIPESSOAL, 70, 999.0),  # fora do recorte mononuclear
    Domicilio(UNIPESSOAL, 25, 80.0),
    Domicilio(CASAL_OU_DUPLA, 45, 60.0),
    Domicilio(MULTIPESSOAL, 35, 40.0),
]

POPULACAO = {
    2018: {25: 2000, 35: 2000, 45: 2000, 55: 1000, 65: 1000, 75: 500, 90: 250},
    2026: {25: 2000, 35: 2000, 45: 2000, 55: 1000, 65: 1000, 75: 500, 90: 250},
    2030: {25: 2000, 35: 2000, 45: 2000, 55: 1000, 65: 1000, 75: 1000, 90: 500},
    2070: {25: 1000, 35: 1000, 45: 1000, 55: 1000, 65: 1000, 75: 500, 90: 250},
}


class RepositorioFalso:
    def __init__(self, domicilios=DOMICILIOS, populacao=POPULACAO):
        self._d, self._p = domicilios, populacao

    def domicilios(self):
        return self._d

    def populacao_por_idade(self, localidade="Brasil"):
        return self._p
