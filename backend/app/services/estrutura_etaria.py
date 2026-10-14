"""Regras da Estrutura etária (RF02, RF05, RF06): pirâmide da população e consumo por faixa do chefe.

A velocidade do envelhecimento k muda a pirâmide; a intensidade da tendência dos arranjos não
muda nada nesta página (a pirâmide é de pessoas e o consumo por faixa vem da POF 2017 a 2018).
"""

from collections.abc import Iterable

from app.calculo import ajustar_envelhecimento, media_ponderada
from app.dados import Domicilio
from app.dominio import (
    ANO_FINAL,
    ANO_INICIAL,
    BRASIL,
    FAIXAS_CHEFE,
    IDADE_IDOSO,
    K_PADRAO,
    FiltroArranjo,
    baixa_confiabilidade,
    da_faixa,
    da_localidade,
    filtrar,
)
from app.schemas.estrutura_etaria import (
    ConsumoChefeResposta,
    FaixaConsumo,
    FaixaPiramide,
    PiramideResposta,
    PiramidesResposta,
)

# (rótulo, idade mínima, idade máxima); a idade 90 da projeção agrega 90 ou mais
FAIXAS_PIRAMIDE = tuple((f"{i} a {i + 9}", i, i + 9) for i in range(0, 80, 10)) + (("80+", 80, None),)


def consumo_por_faixa(domicilios: Iterable[Domicilio], filtro: FiltroArranjo) -> list[FaixaConsumo]:
    """TEC ponderada por peso_final em cada faixa etária do chefe."""
    selecionados = filtrar(domicilios, filtro)
    resultado = []
    for faixa in FAIXAS_CHEFE:
        grupo = da_faixa(selecionados, faixa)
        valor = media_ponderada([d.consumo_per_capita_kwh for d in grupo], [d.peso for d in grupo]) if grupo else None
        resultado.append(
            FaixaConsumo(
                faixa=faixa.rotulo,
                domicilios_amostra=len(grupo),
                baixa_confiabilidade=baixa_confiabilidade(len(grupo)),
                consumo_per_capita_kwh=None if valor is None else round(valor, 1),
            )
        )
    return resultado


def _soma(populacao: dict[int, int], minima: int, maxima: int | None) -> int:
    return sum(p for idade, p in populacao.items() if idade >= minima and (maxima is None or idade <= maxima))


def montar_piramide(ano: int, por_sexo: dict[str, dict[int, float]]) -> PiramideResposta:
    homens, mulheres = por_sexo["Homem"], por_sexo["Mulher"]
    total = sum(homens.values()) + sum(mulheres.values())
    if total <= 0:
        raise ValueError(f"sem população projetada para {ano}")

    def pct(valor: int) -> float:
        return round(valor / total * 100, 2)

    faixas = [
        FaixaPiramide(faixa=rotulo, homens_pct=pct(_soma(homens, a, b)), mulheres_pct=pct(_soma(mulheres, a, b)))
        for rotulo, a, b in FAIXAS_PIRAMIDE
    ]
    idosos = _soma(homens, IDADE_IDOSO, None) + _soma(mulheres, IDADE_IDOSO, None)
    return PiramideResposta(ano=ano, faixas=faixas, participacao_60_mais_pct=pct(idosos))


def com_envelhecimento(por_ano: dict[int, dict[str, dict[int, int]]], k: float) -> dict[int, dict[str, dict[int, float]]]:
    """Aplica a velocidade do envelhecimento k (P14) a cada idade e sexo, a partir de 2026.

    A regra é linear, então a participação de cada faixa da pirâmide (e a de 60 anos ou mais)
    é a mesma que nos grupos usados pela projeção, enquanto o piso em zero não age.
    """
    if k == K_PADRAO or ANO_INICIAL not in por_ano:
        return por_ano
    grupos = {ano: {(sexo, idade): p for sexo, idades in sexos.items() for idade, p in idades.items()} for ano, sexos in por_ano.items()}
    ajustada = ajustar_envelhecimento(grupos, k, ANO_INICIAL)
    resultado: dict[int, dict[str, dict[int, float]]] = {}
    for ano, valores in ajustada.items():
        sexos = resultado.setdefault(ano, {"Homem": {}, "Mulher": {}})
        for (sexo, idade), p in valores.items():
            sexos.setdefault(sexo, {})[idade] = p
    return resultado


def obter_piramide(ano: int, dados, localidade: str = BRASIL, k: float = K_PADRAO) -> PiramideResposta:
    anos = sorted({ano, ANO_INICIAL})
    por_ano = com_envelhecimento({a: dados.populacao_por_sexo(a, localidade) for a in anos}, k)
    return montar_piramide(ano, por_ano[ano])


def obter_piramides(dados, localidade: str = BRASIL, ano_final: int = ANO_FINAL, k: float = K_PADRAO) -> PiramidesResposta:
    anos = [a for a in dados.anos_piramide(localidade) if a <= ano_final]
    por_ano = com_envelhecimento({a: dados.populacao_por_sexo(a, localidade) for a in anos}, k)
    return PiramidesResposta(
        piramides=[montar_piramide(a, por_ano[a]) for a in anos],
        localidade=localidade,
        k=k,
        simulacao=k != K_PADRAO,
    )


def obter_consumo_chefe(filtro: FiltroArranjo, dados, localidade: str = BRASIL) -> ConsumoChefeResposta:
    domicilios = da_localidade(dados.domicilios(), localidade)
    return ConsumoChefeResposta(arranjo=filtro, faixas=consumo_por_faixa(domicilios, filtro), localidade=localidade)
