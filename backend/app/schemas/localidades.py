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
