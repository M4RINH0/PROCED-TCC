"""Regras do Simulador: consulta combinada de ano, arranjo e faixa etária do chefe (RF07).

A TEC de cada célula (faixa do chefe, arranjo) fica nos níveis da POF (premissa P6),
então o consumo por pessoa da célula não depende do ano nem do cenário. O ano e o
cenário definem quantos domicílios a célula tem, a participação dela no total e o
consumo total calibrado (P12):
- taxas: taxa de chefia de 2018 constante (P2);
- contrafactual: o total de domicílios segue a projeção, e a distribuição entre as
  células fica congelada na de 2026 (P10).
A persistência de cenários (RF09) ainda não foi implementada.
"""

from app.dominio import BRASIL, CASAL_OU_DUPLA, MULTIPESSOAL, UNIPESSOAL, FiltroArranjo, baixa_confiabilidade, da_localidade, montar_projecao
from app.schemas.simulador import ROTULO_FAIXA, ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.services.estrutura_etaria import consumo_por_faixa

NOME_ARRANJO = {
    ArranjoSim.unipessoal: UNIPESSOAL,
    ArranjoSim.casal_ou_dupla: CASAL_OU_DUPLA,
    ArranjoSim.multipessoal: MULTIPESSOAL,
}


def simular(ano: int, faixa: FaixaSim, arranjo: ArranjoSim, base: BaseSim, dados, localidade: str = BRASIL) -> SimulacaoResposta:
    domicilios = da_localidade(dados.domicilios(), localidade)
    populacao = dados.populacao_por_idade(localidade)
    por_faixa = consumo_por_faixa(domicilios, FiltroArranjo(arranjo.value))
    rotulo = ROTULO_FAIXA[faixa]
    escolhida = next(f for f in por_faixa if f.faixa == rotulo)
    celula = (rotulo, NOME_ARRANJO[arranjo])

    projetados = participacao = calibrado = None
    motivo = None
    if escolhida.consumo_per_capita_kwh is None:
        motivo = "Sem domicílios na amostra para esta combinação."
    elif ano not in populacao:
        motivo = "Sem projeção da população para este ano."
    else:
        projecao = montar_projecao(domicilios, populacao)
        todos = projecao.domicilios(ano, base.value)
        resumo = projecao.resumo(ano, base.value, [celula])
        projetados = round(todos[celula])
        participacao = round(todos[celula] / sum(todos.values()) * 100, 2)
        calibrado = None if resumo.consumo_total_calibrado is None else round(resumo.consumo_total_calibrado)

    return SimulacaoResposta(
        ano=ano,
        faixa=rotulo,
        arranjo=arranjo,
        base=base,
        valor=escolhida.consumo_per_capita_kwh,
        motivo_sem_valor=motivo,
        domicilios_amostra=escolhida.domicilios_amostra,
        baixa_confiabilidade=baixa_confiabilidade(escolhida.domicilios_amostra),
        domicilios_projetados=projetados,
        participacao_pct=participacao,
        consumo_total_calibrado_kwh_mes=calibrado,
        por_faixa=por_faixa,
        localidade=localidade,
    )
