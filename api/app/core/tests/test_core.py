import pytest

from app.core import Configuracao, ErroConfiguracao, carregar_configuracao, conectar
from app.core.config import ORIGEM_PADRAO


def test_configuracao_usa_padroes_quando_ambiente_vazio():
    config = carregar_configuracao(ambiente={})
    assert config.cors_origin == ORIGEM_PADRAO
    assert config.supabase_url is None
    assert config.database_url is None


def test_configuracao_le_variaveis_do_ambiente():
    config = carregar_configuracao(
        ambiente={"CORS_ORIGIN": "https://proced.exemplo", "DATABASE_URL": "postgresql://x"}
    )
    assert config.cors_origin == "https://proced.exemplo"
    assert config.database_url == "postgresql://x"


def test_configuracao_le_dotenv_e_ambiente_tem_prioridade(tmp_path):
    arquivo = tmp_path / ".env"
    arquivo.write_text(
        "# comentário\nCORS_ORIGIN=http://do-arquivo\nSUPABASE_URL=https://abc.supabase.co\n\n",
        encoding="utf-8",
    )
    config = carregar_configuracao(ambiente={"CORS_ORIGIN": "http://do-ambiente"}, dotenv=arquivo)
    assert config.cors_origin == "http://do-ambiente"
    assert config.supabase_url == "https://abc.supabase.co"


def test_configuracao_ignora_dotenv_inexistente(tmp_path):
    config = carregar_configuracao(ambiente={}, dotenv=tmp_path / "nao-existe.env")
    assert config.cors_origin == ORIGEM_PADRAO


def test_conectar_sem_database_url_falha():
    with pytest.raises(ErroConfiguracao):
        conectar(Configuracao(cors_origin=ORIGEM_PADRAO, supabase_url=None, database_url=None))
