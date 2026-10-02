"""Código comum aos módulos: configuração, conexão com o banco e erros."""

from app.core.config import Configuracao, carregar_configuracao
from app.core.db import conectar
from app.core.erros import ErroConfiguracao

__all__ = ["Configuracao", "carregar_configuracao", "conectar", "ErroConfiguracao"]
