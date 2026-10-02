"""Configuração lida só de variáveis de ambiente (RNF05)."""

import os
from dataclasses import dataclass
from pathlib import Path

ORIGEM_PADRAO = "http://localhost:5173"
DOTENV = Path(__file__).resolve().parents[2] / ".env"


@dataclass(frozen=True)
class Configuracao:
    cors_origin: str
    supabase_url: str | None
    database_url: str | None
    supabase_secret_key: str | None = None


def _ler_dotenv(caminho: Path) -> dict[str, str]:
    """Lê pares CHAVE=valor de um arquivo .env, ignorando comentários e linhas vazias."""
    valores: dict[str, str] = {}
    if not caminho.is_file():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valores[chave.strip()] = valor.strip()
    return valores


def carregar_configuracao(
    ambiente: dict[str, str] | None = None, dotenv: Path | None = None
) -> Configuracao:
    """Monta a configuração. Variáveis do ambiente têm prioridade sobre o .env."""
    arquivo = _ler_dotenv(dotenv) if dotenv else {}
    env = {**arquivo, **(ambiente if ambiente is not None else os.environ)}
    return Configuracao(
        cors_origin=env.get("CORS_ORIGIN") or ORIGEM_PADRAO,
        supabase_url=env.get("SUPABASE_URL") or None,
        database_url=env.get("DATABASE_URL") or None,
        supabase_secret_key=env.get("SUPABASE_SECRET_KEY") or None,
    )
