"""Estrutura etária (RF05, RF06): pirâmide da população e consumo por faixa do chefe."""

from app.modules.estrutura_etaria.repository import RepositorioPiramide
from app.modules.estrutura_etaria.schemas import ConsumoChefeResposta, FaixaPiramide, PiramideResposta
from app.modules.projecoes import FiltroArranjo, RepositorioProjecoes, obter_consumo_por_faixa

# (rótulo, idade mínima, idade máxima); a idade 90 da projeção agrega 90 ou mais
FAIXAS_PIRAMIDE = tuple((f"{i} a {i + 9}", i, i + 9) for i in range(0, 80, 10)) + (("80+", 80, None),)
IDADE_IDOSO = 60


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


def obter_piramide(ano: int, repositorio: RepositorioPiramide) -> PiramideResposta:
    return montar_piramide(ano, repositorio.populacao_por_sexo(ano))


def obter_consumo_chefe(filtro: FiltroArranjo, repositorio: RepositorioProjecoes) -> ConsumoChefeResposta:
    return ConsumoChefeResposta(arranjo=filtro, faixas=obter_consumo_por_faixa(filtro, repositorio))
