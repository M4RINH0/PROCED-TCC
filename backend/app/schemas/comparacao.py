"""Modelos de entrada e saída da página Comparar (RF12)."""

from enum import Enum

from pydantic import BaseModel, Field

from app.dominio import GrupoId
from app.schemas.panorama import CenarioId, Simulacao

FONTE = "POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)"


class IndicadorComparacao(str, Enum):
    domicilios = "domicilios"
    consumo_total = "consumo_total"
    participacao = "participacao"
    consumo_por_pessoa = "consumo_por_pessoa"  # só para agregados


class FormaComparacao(str, Enum):
    absoluto = "absoluto"
    indice = "indice"  # 2026 = 100


class ArranjoGrupo(str, Enum):
    """Arranjo da célula (para a cor da linha); agregado não tem um arranjo só."""

    unipessoal = "unipessoal"
    casal_ou_dupla = "casal_ou_dupla"
    multipessoal = "multipessoal"


class PontoGrupo(BaseModel):
    ano: int
    valor: float | None = Field(description="na forma pedida: valor absoluto ou índice com 2026 = 100")
    valor_absoluto: float | None = Field(description="no indicador pedido, já arredondado como no Panorama")
    indice: float | None = Field(description="valor do ano sobre o de 2026, vezes 100")


class SerieGrupo(BaseModel):
    id: GrupoId
    rotulo: str
    agregado: bool
    chefe_60_mais: bool
    arranjo: ArranjoGrupo | None = Field(description="arranjo da célula; null nos agregados")
    domicilios_amostra: int = Field(description="domicílios da POF no grupo e na localidade")
    baixa_confiabilidade: bool = Field(description="alguma célula do grupo tem menos de 30 domicílios na amostra")
    motivo_sem_valor: str | None = None
    pontos: list[PontoGrupo]


class LinhaComparacao(BaseModel):
    id: GrupoId
    rotulo: str
    valor_2026: float | None
    valor_2050: float | None
    valor_2070: float | None
    variacao_absoluta: float | None = Field(description="2070 menos 2026, no indicador pedido")
    variacao_pct: float | None = Field(description="variação de 2026 a 2070, em %")
    ordem: int | None = Field(description="1 para o grupo que mais cresce em %; null sem valor")


class ComparacaoResposta(Simulacao):
    indicador: IndicadorComparacao
    forma: FormaComparacao
    cenario: CenarioId
    unidade: str = Field(description="unidade do valor absoluto")
    localidade: str
    grupos: list[SerieGrupo]
    tabela: list[LinhaComparacao]
    dados_ilustrativos: bool = False
    fonte: str = FONTE
