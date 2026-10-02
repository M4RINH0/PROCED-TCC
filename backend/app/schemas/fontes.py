from pydantic import BaseModel


class Fonte(BaseModel):
    id: str
    nome: str
    periodo: str
    uso: str
