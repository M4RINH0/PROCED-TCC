"""TEC por arranjo domiciliar no Brasil (RF03, RF04).

A tabela traz médias por UF; a média nacional pondera cada UF pelo número de
domicílios da amostra, o que equivale à média de todos os domicílios.
"""

from app.modules.arranjos.repository import RepositorioArranjos
from app.modules.arranjos.schemas import ArranjoConsumo, ArranjosResposta, Grupo
from app.modules.projecoes import tec

ORDEM = ("Unipessoal (Mononuclear)", "Casal ou Dupla", "Multipessoal (3+)")
MONONUCLEARES = set(ORDEM[:2])


def _no_grupo(chefe_60_mais: bool, grupo: Grupo) -> bool:
    return grupo is Grupo.todos or (grupo is Grupo.chefe_60_mais) == chefe_60_mais


def agregar(linhas: list[dict], grupo: Grupo) -> list[ArranjoConsumo]:
    soma: dict[tuple[str, bool], dict[str, float]] = {}
    for l in linhas:
        chave = (l["arranjo_familiar"], bool(l["is_60_mais"]))
        if not _no_grupo(chave[1], grupo):
            continue
        n = l["total_domicilios_amostra"]
        acc = soma.setdefault(chave, {"n": 0, "per_capita": 0.0, "total": 0.0, "gasto": 0.0})
        acc["n"] += n
        acc["per_capita"] += n * l["media_consumo_per_capita_kwh"]
        acc["total"] += n * l["media_consumo_total_kwh"]
        acc["gasto"] += n * l["media_gasto_rs"]

    def ordem(chave):
        arranjo, idoso = chave
        return (ORDEM.index(arranjo) if arranjo in ORDEM else len(ORDEM), not idoso)

    resultado = []
    for chave in sorted(soma, key=ordem):
        acc, (arranjo, idoso) = soma[chave], chave
        if acc["n"] <= 0:
            continue
        resultado.append(
            ArranjoConsumo(
                arranjo=arranjo,
                mononuclear=arranjo in MONONUCLEARES,
                chefe_60_mais=idoso,
                domicilios_amostra=int(acc["n"]),
                consumo_per_capita_kwh=round(tec(acc["per_capita"], acc["n"]), 1),
                consumo_total_kwh=round(acc["total"] / acc["n"], 1),
                gasto_rs=round(acc["gasto"] / acc["n"], 2),
            )
        )
    return resultado


def obter_arranjos(grupo: Grupo, repositorio: RepositorioArranjos) -> ArranjosResposta:
    return ArranjosResposta(grupo=grupo, arranjos=agregar(repositorio.coeficientes(), grupo))
