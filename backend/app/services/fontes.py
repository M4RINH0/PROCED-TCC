"""Fontes, período de referência, critério de exclusão e premissas principais (RF10)."""

from app.dominio import TOTAL_DOMICILIOS_POF, memorizado
from app.schemas.fontes import Fonte, FontesResposta, Premissa

FONTES = [
    Fonte(
        id="pof",
        nome="Pesquisa de Orçamentos Familiares (IBGE)",
        periodo="2017 a 2018",
        uso="Consumo de energia em kWh por domicílio, arranjo e idade do chefe, com o peso amostral",
    ),
    Fonte(
        id="pof_historica",
        nome="Pesquisas de Orçamentos Familiares anteriores (IBGE)",
        periodo="2002 a 2003 e 2008 a 2009",
        uso="Tendência dos arranjos: divisão dos domicílios entre unipessoal, casal ou dupla e multipessoal "
        "em cada faixa do chefe, com o peso amostral (P13)",
    ),
    Fonte(
        id="projecao",
        nome="Projeções da População (IBGE)",
        periodo="2000 a 2070 (usadas de 2018 a 2070)",
        uso="Pirâmide etária, taxas de chefia de 2018 e domicílios projetados de 2026 a 2070",
    ),
]

CRITERIO_EXCLUSAO = (
    "Ficaram de fora, na extração, os domicílios sem declaração válida de consumo de energia "
    "(sem kWh), conforme o critério de exclusão da Metodologia do TCC."
)

# Resumo das premissas de docs/premissas.md que afetam os resultados exibidos (P1 e P4 a P7 são de
# recorte e de faixa, e a P3 foi revogada); o texto completo fica no link da gaveta.
PREMISSAS = [
    Premissa(
        id="P2",
        texto="Taxa de chefia total de 2018 constante por faixa de idade do chefe, combinada com a "
        "tendência histórica de transição dos arranjos domiciliares estimada a partir das POFs (P13).",
    ),
    Premissa(id="P8", texto="Domicílio repetido na POF fica só com a linha do chefe de maior idade (provisória)."),
    Premissa(
        id="P9",
        texto="O consumo se refere aos domicílios com kWh declarado, que cobrem parte do total de domicílios da POF.",
    ),
    Premissa(
        id="P10",
        texto="Sem mudanças desde 2026: o total de domicílios segue a projeção, e a composição por faixa do chefe e "
        "arranjo fica a de 2026 (provisória).",
    ),
    Premissa(
        id="P11",
        texto="Moradores médios de cada célula constantes; os moradores projetados não são limitados pela população do IBGE.",
    ),
    Premissa(
        id="P12",
        texto="Consumo total calibrado: consumo por pessoa vezes a população do IBGE no ano. O fator é único "
        "para todas as células e corrige o nível, mas não a composição.",
    ),
    Premissa(
        id="P13",
        texto="Tendência dos arranjos: em cada faixa do chefe, a divisão entre unipessoal, casal ou dupla e "
        "multipessoal segue a reta das POFs 2002 a 2003, 2008 a 2009 e 2017 a 2018, com intensidade padrão 0,6 "
        "(calibrada pela validação fora do tempo). Com intensidade 0, os arranjos ficam congelados a partir de 2026.",
    ),
    Premissa(
        id="P14",
        texto="Velocidade do envelhecimento k: a participação de cada grupo de idade se afasta da de 2026 k vezes "
        "o que a projeção da população do IBGE prevê. k = 1 reproduz a projeção.",
    ),
]

PREMISSAS_URL = "https://github.com/M4RINH0/PROCED-TCC/blob/main/docs/premissas.md"


def cobertura(soma_pesos: float, total: float = TOTAL_DOMICILIOS_POF) -> float:
    if total <= 0:
        raise ValueError("o total de domicílios precisa ser maior que zero")
    return round(soma_pesos / total * 100, 1)


def obter_fontes(dados) -> FontesResposta:
    return FontesResposta(
        fontes=FONTES,
        criterio_exclusao=CRITERIO_EXCLUSAO,
        cobertura_pct=cobertura(memorizado(dados, "soma_dos_pesos", lambda: sum(d.peso for d in dados.domicilios()))),
        premissas=PREMISSAS,
        premissas_url=PREMISSAS_URL,
    )
