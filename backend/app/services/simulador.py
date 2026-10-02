"""Regras do Simulador: consulta combinada de ano, arranjo e faixa etária do chefe (RF07).

No cenário oficial, a TEC de cada tipo de domicílio fica nos níveis da POF
(premissa P6): o ano escolhido só decide se há projeção oficial (até 2070).
A persistência de cenários (RF09) ainda não foi implementada.
"""

from app.dominio import ANO_FINAL_IBGE, FiltroArranjo
from app.schemas.simulador import ROTULO_FAIXA, ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.services.estrutura_etaria import consumo_por_faixa


def simular(
    ano: int, faixa: FaixaSim, arranjo: ArranjoSim, base: BaseSim, taxa: float | None, dados
) -> SimulacaoResposta:
    por_faixa = consumo_por_faixa(dados.domicilios(), FiltroArranjo(arranjo.value))
    rotulo = ROTULO_FAIXA[faixa]
    escolhida = next(f for f in por_faixa if f.faixa == rotulo)

    valor, motivo = escolhida.consumo_per_capita_kwh, None
    if base is not BaseSim.ibge:
        valor, motivo = None, "Cenário ainda não modelado."
    elif ano > ANO_FINAL_IBGE:
        valor, motivo = None, f"A projeção oficial do IBGE termina em {ANO_FINAL_IBGE}."
    elif valor is None:
        motivo = "Sem domicílios na amostra para esta combinação."

    return SimulacaoResposta(
        ano=ano,
        faixa=rotulo,
        arranjo=arranjo,
        base=base,
        taxa=taxa,
        valor=valor,
        motivo_sem_valor=motivo,
        domicilios_amostra=escolhida.domicilios_amostra,
        por_faixa=por_faixa,
    )
