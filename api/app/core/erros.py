class ErroConfiguracao(RuntimeError):
    """Variável de ambiente obrigatória ausente ou inválida."""


class ErroFonteDados(RuntimeError):
    """A fonte de dados (Supabase) não respondeu ou respondeu com erro."""
