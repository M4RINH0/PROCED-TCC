"""Regras do Simulador: consulta combinada de ano, arranjo e faixa etária do chefe (RF02, RF07, RF09).

A TEC de cada célula (faixa do chefe, arranjo) fica nos níveis da POF (premissa P6),
então o consumo por pessoa da célula não depende do ano nem do cenário. O ano e o
cenário definem quantos domicílios a célula tem, a participação dela no total e o
consumo total calibrado (P12):
- taxas: taxa de chefia total da faixa constante (P2) e tendência dos arranjos (P13);
- taxas_arranjos_fixos: só o envelhecimento, com os arranjos congelados em 2026;
- contrafactual: o total de domicílios segue a projeção, e a distribuição entre as
  células fica congelada na de 2026 (P10).
Os controles de simulação (RF02) valem aqui como no Panorama.
Cada combinação válida consultada é persistida (RF09) e recuperada nas consultas seguintes.
"""

from app.dominio import (
    BRASIL,
    CASAL_OU_DUPLA,
    INTENSIDADE_PADRAO,
    K_PADRAO,
    MULTIPESSOAL,
    UNIPESSOAL,
    FiltroArranjo,
    baixa_confiabilidade,
    base_da_localidade,
    domicilios_da_localidade,
    em_simulacao,
    memorizado,
    projecao_da_base,
    tendencia_dos_dados,
)
from app.schemas.simulador import ROTULO_FAIXA, ArranjoSim, BaseSim, FaixaSim, SimulacaoResposta
from app.services.estrutura_etaria import consumo_por_faixa

NOME_ARRANJO = {
    ArranjoSim.unipessoal: UNIPESSOAL,
    ArranjoSim.casal_ou_dupla: CASAL_OU_DUPLA,
    ArranjoSim.multipessoal: MULTIPESSOAL,
}


def _chave_cenario(
    ano: int,
    faixa: FaixaSim,
    arranjo: ArranjoSim,
    base: BaseSim,
    localidade: str,
    intensidade: float,
    k: float,
) -> str:
    return f"{localidade}:{ano}:{faixa.value}:{arranjo.value}:{base.value}:{round(intensidade, 4)}:{round(k, 4)}"


def _obter_salvo(dados, chave: str) -> SimulacaoResposta | None:
    obter = getattr(dados, "obter_cenario", None)
    if obter is not None:
        registro = obter(chave)
        return None if registro is None else SimulacaoResposta(**registro)
    memoria = getattr(dados, "_cenarios_memoria", None)
    if memoria is None or chave not in memoria:
        return None
    return SimulacaoResposta(**memoria[chave])


def _salvar(dados, chave: str, resposta: SimulacaoResposta) -> None:
    registro = resposta.model_dump()
    salvar = getattr(dados, "salvar_cenario", None)
    if salvar is not None:
        salvar(chave, registro)
        return
    memoria = getattr(dados, "_cenarios_memoria", None)
    if memoria is None:
        memoria = {}
        setattr(dados, "_cenarios_memoria", memoria)
    memoria[chave] = registro


def simular(
    ano: int,
    faixa: FaixaSim,
    arranjo: ArranjoSim,
    base: BaseSim,
    dados,
    localidade: str = BRASIL,
    intensidade: float = INTENSIDADE_PADRAO,
    k: float = K_PADRAO,
    recalcular: bool = False,
) -> SimulacaoResposta:
    chave = _chave_cenario(ano, faixa, arranjo, base, localidade, intensidade, k)
    if not recalcular:
        salvo = _obter_salvo(dados, chave)
        if salvo is not None:
            return salvo.model_copy(update={"recuperado": True})

    populacao = dados.populacao_por_idade(localidade)
    filtro = FiltroArranjo(arranjo.value)
    por_faixa = memorizado(
        dados, f"consumo_chefe:{localidade}:{filtro.value}", lambda: consumo_por_faixa(domicilios_da_localidade(dados, localidade), filtro)
    )
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
        projecao = projecao_da_base(base_da_localidade(dados, localidade), tendencia_dos_dados(dados), intensidade, k)
        todos = projecao.domicilios(ano, base.value)
        resumo = projecao.resumo(ano, base.value, [celula])
        projetados = round(todos[celula])
        participacao = round(todos[celula] / sum(todos.values()) * 100, 2)
        calibrado = None if resumo.consumo_total_calibrado is None else round(resumo.consumo_total_calibrado)

    resposta = SimulacaoResposta(
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
        recuperado=False,
        localidade=localidade,
        intensidade=intensidade,
        k=k,
        simulacao=em_simulacao(intensidade, k),
    )
    if motivo is None:
        _salvar(dados, chave, resposta)
    return resposta
