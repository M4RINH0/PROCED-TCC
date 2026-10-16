from enum import Enum


class FormatoExportacao(str, Enum):
    csv = "csv"
    xlsx = "xlsx"


class EscopoExportacao(str, Enum):
    ano = "ano"
    serie = "serie"
