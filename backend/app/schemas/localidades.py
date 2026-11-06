from pydantic import BaseModel


class Estado(BaseModel):
    sigla: str
    nome: str


class Regiao(BaseModel):
    nome: str
    estados: list[Estado]


class LocalidadesResposta(BaseModel):
    padrao: str
    regioes: list[Regiao]


class LinhaSinteseRegional(BaseModel):
    localidade: str
    amostra_pof: int
    populacao_60_mais_pct_2026: float
    populacao_60_mais_pct_2070: float
    tbc_2026: float
    tbc_2070: float
    variacao_tbc_pct: float
    part_mono_60_mais_pct_2026: float
    part_mono_60_mais_pct_2070: float


class SinteseRegionalResposta(BaseModel):
    linhas: list[LinhaSinteseRegional]
    fonte: str = "POF 2017 a 2018 e Projeções da População Revisão 2024 (IBGE)"
