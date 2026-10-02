"""Módulo arranjos, RF03 e RF04: exibir e filtrar a TEC por arranjo domiciliar.

Interface pública.
"""

from app.modules.arranjos.router import obter_repositorio, router

__all__ = ["router", "obter_repositorio"]
