from types import SimpleNamespace

import pytest

from app.dominio import UFS, faixa_do_chefe, sem_repeticao, somar_populacao, ufs_explicitas


def _linha(localidade, sexo, populacao, ano=2018, idade=60):
    return {"localidade": localidade, "sexo": sexo, "ano": ano, "idade": idade, "populacao": populacao}


# Tabela como a do banco: duas UFs, a região, o Brasil, e os três sexos.
# Só DF e GO com "Ambos" entram: 10 + 20 = 30.
LINHAS = [
    _linha("DF", "Ambos", 10),
    _linha("DF", "Homem", 4),
    _linha("DF", "Mulher", 6),
    _linha("GO", "Ambos", 20),
    _linha("GO", "Homem", 9),
    _linha("GO", "Mulher", 11),
    _linha("Centro-Oeste", "Ambos", 30),
    _linha("Brasil", "Ambos", 30),
    _linha("Brasil", "Homem", 13),
]


def test_filtro_de_populacao_exclui_ambos_regioes_e_brasil_quando_soma_um_sexo():
    assert somar_populacao(LINHAS, ["DF", "GO"], sexo="Homem") == {2018: {60: 13}}


def test_filtro_de_populacao_exclui_as_linhas_de_total_e_os_outros_sexos():
    assert somar_populacao(LINHAS, ["DF", "GO"]) == {2018: {60: 30}}


def test_filtro_de_populacao_de_uma_uf():
    assert somar_populacao(LINHAS, ["GO"]) == {2018: {60: 20}}


def test_filtro_de_populacao_agrupa_por_ano_e_idade():
    linhas = [_linha("SP", "Ambos", 5, 2030, 61), _linha("RJ", "Ambos", 7, 2030, 61), _linha("SP", "Ambos", 1, 2030, 90)]
    assert somar_populacao(linhas, ["SP", "RJ"]) == {2030: {61: 12, 90: 1}}


def test_filtro_de_populacao_rejeita_sigla_que_nao_e_uf():
    with pytest.raises(ValueError, match="Brasil"):
        somar_populacao(LINHAS, ["Brasil"])


def test_ufs_explicitas():
    assert len(UFS) == 27 and "Brasil" not in UFS and "Sul" not in UFS
    assert ufs_explicitas("Brasil") == UFS
    assert ufs_explicitas("Sul") == ("PR", "RS", "SC")
    assert ufs_explicitas("AP") == ("AP",)


@pytest.mark.parametrize("idade, rotulo", [(12, "até 29"), (29, "até 29"), (30, "30 a 39"), (79, "70 a 79"), (90, "80+")])
def test_faixa_do_chefe(idade, rotulo):
    assert faixa_do_chefe(idade).rotulo == rotulo


def test_faixa_do_chefe_abaixo_da_idade_minima():
    assert faixa_do_chefe(11) is None


def _dom(id_domicilio, idade):
    return SimpleNamespace(id_domicilio=id_domicilio, idade_chefe=idade)


def test_repeticao_fica_com_o_chefe_de_maior_idade():
    # id 7 com chefes de 52, 77 e 40 anos: fica o de 77; a ordem de entrada se mantém
    entrada = [_dom(1, 30), _dom(7, 52), _dom(7, 77), _dom(2, 45), _dom(7, 40)]
    assert [(d.id_domicilio, d.idade_chefe) for d in sem_repeticao(entrada)] == [(1, 30), (7, 77), (2, 45)]


def test_repeticao_com_mesma_idade_fica_com_a_primeira_linha():
    primeira, segunda = _dom(3, 60), _dom(3, 60)
    assert sem_repeticao([primeira, segunda]) == [primeira]


def test_linhas_sem_id_passam_todas():
    a, b = SimpleNamespace(idade_chefe=1), SimpleNamespace(id_domicilio=None, idade_chefe=2)
    assert sem_repeticao([a, b]) == [a, b]
