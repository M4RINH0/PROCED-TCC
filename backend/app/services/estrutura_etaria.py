"""Regras da Estrutura etária (RF05, RF06): pirâmide da população e consumo por faixa do chefe."""

from collections.abc import Iterable

from app.calculo import tec
from app.dados import Domicilio
from app.dominio import ANO_FINAL, FAIXAS_CHEFE, IDADE_IDOSO, FiltroArranjo, da_faixa, filtrar
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
    """TEC por faixa etária do chefe."""
    selecionados = filtrar(domicilios, filtro)
    resultado = []
    for faixa in FAIXAS_CHEFE:
        grupo = da_faixa(selecionados, faixa)
        valor = tec(sum(d.consumo_per_capita_kwh for d in grupo), len(grupo)) if grupo else None
        resultado.append(
            FaixaConsumo(
                faixa=faixa.rotulo,
                domicilios_amostra=len(grupo),
                consumo_per_capita_kwh=None if valor is None else round(valor, 1),
            )
        )
    return resultado


def _soma(populacao: dict[int, int], minima: int, maxima: int | None) -> int:
    return sum(p for idade, p in populacao.items() if idade >= minima and (maxima is None or idade <= maxima))


def montar_piramide(ano: int, por_sexo: dict[str, dict[int, int]]) -> PiramideResposta:
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


def obter_piramide(ano: int, dados) -> PiramideResposta:
    return montar_piramide(ano, dados.populacao_por_sexo(ano))


def obter_piramides(dados, ano_final: int = ANO_FINAL) -> PiramidesResposta:
    anos = [a for a in dados.anos_piramide() if a <= ano_final]
    return PiramidesResposta(piramides=[montar_piramide(a, dados.populacao_por_sexo(a)) for a in anos])


def obter_consumo_chefe(filtro: FiltroArranjo, dados) -> ConsumoChefeResposta:
    return ConsumoChefeResposta(arranjo=filtro, faixas=consumo_por_faixa(dados.domicilios(), filtro))
