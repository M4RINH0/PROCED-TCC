"""Conexão com o PostgreSQL do Supabase.

Ainda não é usada por nenhum módulo: o esquema do banco depende do modelo
entidade-relacionamento, que está pendente.
"""

from app.core.config import Configuracao
from app.core.erros import ErroConfiguracao


def conectar(config: Configuracao):
    """Abre uma conexão psycopg. Exige DATABASE_URL configurada."""
    if not config.database_url:
        raise ErroConfiguracao("DATABASE_URL não configurada")
    import psycopg

    return psycopg.connect(config.database_url)
