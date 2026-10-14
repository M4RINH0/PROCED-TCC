from pydantic import BaseModel, Field


class Fonte(BaseModel):
    id: str
    nome: str
    periodo: str
    uso: str


class Premissa(BaseModel):
    id: str
    texto: str


class FontesResposta(BaseModel):
    fontes: list[Fonte]
    criterio_exclusao: str
    cobertura_pct: float = Field(description="soma dos pesos da base dividida pelo total de domicílios da POF (P9)")
    premissas: list[Premissa]
    premissas_url: str
