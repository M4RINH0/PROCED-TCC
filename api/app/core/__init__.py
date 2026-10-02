"""Código comum aos módulos: configuração, acesso aos dados e erros."""

from app.core.config import DOTENV, Configuracao, carregar_configuracao
from app.core.db import conectar
from app.core.erros import ErroConfiguracao, ErroFonteDados
from app.core.supabase import ClienteSupabase, criar_cliente, obter_cliente

__all__ = [
    "DOTENV",
    "Configuracao",
    "carregar_configuracao",
    "conectar",
    "ErroConfiguracao",
    "ErroFonteDados",
    "ClienteSupabase",
    "criar_cliente",
    "obter_cliente",
]
