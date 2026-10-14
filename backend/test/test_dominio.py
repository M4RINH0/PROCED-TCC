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


def test_celulas_do_recorte_sao_as_faixas_com_os_arranjos_mononucleares():
    from app.dominio import CASAL_OU_DUPLA, CELULAS_DO_RECORTE, UNIPESSOAL, Recorte

    assert CELULAS_DO_RECORTE[Recorte.chefe_60_mais] == (
        ("60 a 69", UNIPESSOAL), ("60 a 69", CASAL_OU_DUPLA),
        ("70 a 79", UNIPESSOAL), ("70 a 79", CASAL_OU_DUPLA),
        ("80+", UNIPESSOAL), ("80+", CASAL_OU_DUPLA),
    )
    assert len(CELULAS_DO_RECORTE[Recorte.mononuclear_abaixo_60]) == 8


@pytest.mark.parametrize("amostra, baixa", [(0, True), (29, True), (30, False), (500, False)])
def test_baixa_confiabilidade_abaixo_de_30(amostra, baixa):
    from app.dominio import baixa_confiabilidade

    assert baixa_confiabilidade(amostra) is baixa


def test_celula_do_domicilio():
    from app.dominio import celula_do_domicilio

    assert celula_do_domicilio(SimpleNamespace(idade_chefe=91, arranjo="Casal ou Dupla")) == ("80+", "Casal ou Dupla")
    assert celula_do_domicilio(SimpleNamespace(idade_chefe=10, arranjo="Casal ou Dupla")) is None


def test_populacao_por_faixa_e_total():
    from app.dominio import populacao_por_faixa, populacao_total

    pop = {2018: {5: 100, 12: 1, 29: 2, 30: 3, 90: 4}}
    # até 29 começa em 12 (P4): 1 + 2; a idade 5 só entra no total
    assert populacao_por_faixa(pop)[2018]["até 29"] == 3
    assert populacao_por_faixa(pop)[2018]["80+"] == 4
    assert populacao_total(pop) == {2018: 110}


def test_montar_projecao_usa_peso_consumo_e_moradores_do_domicilio():
    from app.dados import Domicilio
    from app.dominio import montar_projecao

    # dois domicílios casal 60 a 69: (peso 1, 200 kWh, 2 moradores) e (peso 3, 100 kWh, 2 moradores)
    domicilios = [
        Domicilio("Casal ou Dupla", 62, 100.0, peso=1.0, consumo_total_kwh=200.0, moradores=2),
        Domicilio("Casal ou Dupla", 66, 50.0, peso=3.0, consumo_total_kwh=100.0, moradores=2),
        Domicilio("Casal ou Dupla", 8, 50.0, peso=3.0, consumo_total_kwh=100.0, moradores=2),  # sem faixa: fica de fora
    ]
    pop = {2018: {65: 40}, 2026: {65: 40}}
    celula = montar_projecao(domicilios, pop).celulas[("60 a 69", "Casal ou Dupla")]
    # consumo por domicílio (200 + 300) / 4 = 125; per capita (100 + 150) / 4 = 62,5
    assert celula.amostra == 2 and celula.peso == 4
    assert celula.consumo_domicilio == pytest.approx(125) and celula.tec == pytest.approx(62.5)
    assert celula.moradores == pytest.approx(2)


# ---------- recortes, controles de simulação e tendência (P13) ----------


def test_recortes_novos_usam_os_tres_arranjos():
    from app.dominio import CELULAS_DO_RECORTE, FAIXAS_CHEFE, MULTIPESSOAL, Recorte

    assert list(Recorte)[0] is Recorte.todos_domicilios  # o padrão do Panorama
    assert len(CELULAS_DO_RECORTE[Recorte.todos_domicilios]) == len(FAIXAS_CHEFE) * 3
    assert len(CELULAS_DO_RECORTE[Recorte.chefe_60_mais_todos]) == 9
    assert ("80+", MULTIPESSOAL) in CELULAS_DO_RECORTE[Recorte.chefe_60_mais_todos]
    assert ("80+", MULTIPESSOAL) not in CELULAS_DO_RECORTE[Recorte.chefe_60_mais]


@pytest.mark.parametrize("intensidade, k, simulacao", [(0.6, 1.0, False), (1.0, 1.0, True), (0.5, 1.0, True), (0.6, 1.2, True), (0.0, 0.5, True)])
def test_em_simulacao_quando_algum_controle_sai_do_padrao(intensidade, k, simulacao):
    from app.dominio import em_simulacao

    assert em_simulacao(intensidade, k) is simulacao


def test_grupos_cobrem_todas_as_idades():
    from app.dominio import GRUPO_0_11, populacao_por_grupo

    pop = {2026: {0: 5, 11: 6, 12: 7, 45: 8, 90: 9}}
    grupos = populacao_por_grupo(pop)[2026]
    assert grupos[GRUPO_0_11] == 11 and grupos["até 29"] == 7
    assert sum(grupos.values()) == 35  # a soma de todas as idades


def _hist(ano, arranjo, idade, peso, rede=True):
    from app.dados import DomicilioHistorico

    return DomicilioHistorico(ano, arranjo, idade, peso, rede)


def test_proporcoes_por_edicao_excluem_fora_da_rede_e_contam_2017_como_rede():
    from app.dados import Domicilio
    from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL, proporcoes_por_edicao

    historicos = [
        _hist(2002, UNIPESSOAL, 65, 1.0),
        _hist(2002, MULTIPESSOAL, 66, 3.0),
        _hist(2002, CASAL_OU_DUPLA, 67, 50.0, rede=False),  # fora da rede geral: sai (P13)
        _hist(2008, CASAL_OU_DUPLA, 61, 2.0),
    ]
    atuais = [Domicilio(UNIPESSOAL, 62, 100.0, peso=1.0), Domicilio(CASAL_OU_DUPLA, 63, 50.0, peso=1.0)]
    props = proporcoes_por_edicao(historicos, atuais)
    assert list(props) == [2002.5, 2008.5, 2017.5]
    assert props[2002.5]["60 a 69"] == pytest.approx({UNIPESSOAL: 0.25, MULTIPESSOAL: 0.75})
    assert props[2017.5]["60 a 69"] == pytest.approx({UNIPESSOAL: 0.5, CASAL_OU_DUPLA: 0.5})


def test_tendencia_nacional_com_as_tres_edicoes():
    from app.dados import Domicilio
    from app.dominio import CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL, tendencia_nacional

    def edicao(ano, u, c, m):
        return [_hist(ano, UNIPESSOAL, 65, u), _hist(ano, CASAL_OU_DUPLA, 65, c), _hist(ano, MULTIPESSOAL, 65, m)]

    historicos = edicao(2002, 1, 1, 8) + edicao(2008, 2, 2, 6)
    atuais = [Domicilio(UNIPESSOAL, 65, 1.0, peso=3), Domicilio(CASAL_OU_DUPLA, 65, 1.0, peso=3), Domicilio(MULTIPESSOAL, 65, 1.0, peso=4)]
    tendencia = tendencia_nacional(historicos, atuais)
    assert set(tendencia) == {"60 a 69"}
    assert tendencia["60 a 69"][0] > 0 and tendencia["60 a 69"][0] == pytest.approx(tendencia["60 a 69"][1])
    assert tendencia_nacional([], atuais) == {}  # uma edição só: sem tendência


def test_montar_projecao_com_k_mantem_a_populacao_total():
    from app.dados import Domicilio
    from app.dominio import montar_projecao

    domicilios = [Domicilio("Unipessoal (Mononuclear)", 65, 100.0), Domicilio("Unipessoal (Mononuclear)", 35, 50.0)]
    pop = {2018: {5: 50, 35: 100, 65: 100}, 2026: {5: 50, 35: 100, 65: 100}, 2050: {5: 40, 35: 80, 65: 200}}
    normal = montar_projecao(domicilios, pop)
    lento = montar_projecao(domicilios, pop, k=0.5)
    # 2050: participação de 60 a 69 vai de 0,4 a 0,625; com k = 0,5: 0,4 + 0,5 * 0,225 = 0,5125 -> 164
    assert normal.populacao_por_faixa[2050]["60 a 69"] == 200
    assert lento.populacao_por_faixa[2050]["60 a 69"] == pytest.approx(0.5125 * 320)
    assert lento.populacao_total[2050] == 320
    assert lento.populacao_por_faixa[2018] == normal.populacao_por_faixa[2018]
