from app.modules.projecoes.repository import RepositorioProjecoes
from app.modules.projecoes.schemas import (
    ANO_FINAL,
    ANO_FINAL_IBGE,
    ANO_INICIAL,
    Cenario,
    CenarioId,
    ProjecaoResposta,
    Recorte,
)


def obter_projecao(ano: int, recorte: Recorte, repositorio: RepositorioProjecoes) -> ProjecaoResposta:
    """Valores dos três cenários num ano (RF01, RF11).

    A série oficial do IBGE é sempre null depois de 2060, seja qual for a fonte.
    """
    if not ANO_INICIAL <= ano <= ANO_FINAL:
        raise ValueError(f"o ano precisa estar entre {ANO_INICIAL} e {ANO_FINAL}")

    cenarios = []
    for cenario in CenarioId:
        if cenario is CenarioId.ibge and ano > ANO_FINAL_IBGE:
            valor = None
        else:
            valor = repositorio.valor(cenario, ano, recorte)
        cenarios.append(Cenario(id=cenario, valor=None if valor is None else round(valor, 1)))

    return ProjecaoResposta(
        ano=ano,
        recorte=recorte,
        cenarios=cenarios,
        dados_ilustrativos=repositorio.dados_ilustrativos,
    )
