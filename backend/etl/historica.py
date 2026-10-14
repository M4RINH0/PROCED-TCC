"""Carga das POFs 2002 a 2003 e 2008 a 2009 na tabela fato_consumo_pof_historica (RNF08).

Os CSVs ficam em etl/entrada/ (fora do git) e foram gerados a partir dos microdados
oficiais do IBGE (ftp.ibge.gov.br/Orcamentos_Familiares); a origem está no docs/etl.md.
A carga leva todos os registros: o filtro dos domicílios fora da rede geral é aplicado
no cálculo (premissa P13), não aqui.

Rodar na pasta backend/: python -m etl.historica
É idempotente: grava por upsert na chave (ano_pof, id_domicilio) e confere o count no banco.
"""

from collections.abc import Iterable
from pathlib import Path

import httpx
import pandas as pd

from etl.derivacao import arranjo_familiar, eh_60_mais

TABELA = "fato_consumo_pof_historica"
PASTA_ENTRADA = Path(__file__).parent / "entrada"
ARQUIVOS = {2002: "fato_consumo_domiciliar_pof2002.csv", 2008: "fato_consumo_domiciliar_pof2008.csv"}
CONTAGENS = {2002: 39_458, 2008: 49_268}  # domicílios com conta de luz em cada edição
COLUNAS = (
    "ano_pof", "sigla_uf", "id_domicilio", "qtd_moradores", "arranjo_familiar", "idade_chefe", "is_60_mais",
    "consumo_total_kwh", "consumo_per_capita_kwh", "peso_final", "kwh_imputado", "energia_rede_geral",
)
LOTE = 1000


def validar(df: pd.DataFrame, ano: int, esperado: int | None = None) -> None:
    """Confere colunas, contagem, edição, nulos, chave única e as regras de derivação."""
    faltando = set(COLUNAS) - set(df.columns)
    if faltando:
        raise ValueError(f"POF {ano}: colunas ausentes {sorted(faltando)}")
    if esperado is not None and len(df) != esperado:
        raise ValueError(f"POF {ano}: {len(df)} registros, esperados {esperado}")
    if (df["ano_pof"] != ano).any():
        raise ValueError(f"POF {ano}: há registros de outra edição")
    nulos = [c for c in COLUNAS if df[c].isna().any()]
    if nulos:
        raise ValueError(f"POF {ano}: valores ausentes em {nulos}")
    if df["id_domicilio"].duplicated().any():
        raise ValueError(f"POF {ano}: id_domicilio repetido")
    if (df["peso_final"] <= 0).any():
        raise ValueError(f"POF {ano}: peso_final não positivo")
    if (df["arranjo_familiar"] != df["qtd_moradores"].map(arranjo_familiar)).any():
        raise ValueError(f"POF {ano}: arranjo não confere com o número de moradores")
    if (df["is_60_mais"] != df["idade_chefe"].map(eh_60_mais)).any():
        raise ValueError(f"POF {ano}: is_60_mais não confere com a idade do chefe")
    per_capita = df["consumo_total_kwh"] / df["qtd_moradores"]
    if ((per_capita - df["consumo_per_capita_kwh"]).abs() > 0.01).any():
        raise ValueError(f"POF {ano}: consumo per capita não confere com consumo total / moradores")


def ler(pasta: Path = PASTA_ENTRADA, arquivos: dict[int, str] = ARQUIVOS, contagens: dict[int, int] = CONTAGENS) -> tuple[pd.DataFrame, dict]:
    partes = []
    for ano, nome in arquivos.items():
        caminho = pasta / nome
        if not caminho.exists():
            raise FileNotFoundError(f"falta {caminho}")
        df = pd.read_csv(caminho, dtype={"id_domicilio": str, "sigla_uf": str, "arranjo_familiar": str})
        validar(df, ano, contagens.get(ano))
        partes.append(df[list(COLUNAS)])
    dados = pd.concat(partes, ignore_index=True)
    registro = {
        "etapa": "carga das POFs anteriores",
        "fonte": "microdados oficiais do IBGE (ftp.ibge.gov.br/Orcamentos_Familiares), POF 2002 a 2003 e 2008 a 2009",
        "transformacao": "conferência de colunas, contagens, chave e regras de derivação; carga de todos os registros",
        "linhas": {int(a): int((dados["ano_pof"] == a).sum()) for a in arquivos},
    }
    return dados, registro


def linhas_para_carga(dados: pd.DataFrame) -> list[dict]:
    """Converte para tipos nativos do JSON (sem numpy)."""
    inteiros = ("ano_pof", "qtd_moradores", "idade_chefe")
    logicos = ("is_60_mais", "kwh_imputado", "energia_rede_geral")
    reais = ("consumo_total_kwh", "consumo_per_capita_kwh", "peso_final")
    linhas = []
    for r in dados.itertuples(index=False):
        d = r._asdict()
        linhas.append(
            {
                **{c: str(d[c]) for c in ("sigla_uf", "id_domicilio", "arranjo_familiar")},
                **{c: int(d[c]) for c in inteiros},
                **{c: bool(d[c]) for c in logicos},
                **{c: float(d[c]) for c in reais},
            }
        )
    return linhas


def gravar(url: str, chave: str, linhas: Iterable[dict], http: httpx.Client | None = None, lote: int = LOTE) -> int:
    """Upsert em lotes pela API REST do Supabase, com a chave secreta (só no back-end, RNF05)."""
    http = http or httpx.Client(timeout=120)
    endereco = url.rstrip("/") + f"/rest/v1/{TABELA}"
    cabecalhos = {"apikey": chave, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}
    lista = list(linhas)
    for inicio in range(0, len(lista), lote):
        resposta = http.post(endereco, params={"on_conflict": "ano_pof,id_domicilio"}, json=lista[inicio : inicio + lote], headers=cabecalhos)
        if resposta.status_code >= 400:
            raise RuntimeError(f"{TABELA} respondeu com o código {resposta.status_code} no lote que começa em {inicio}")
    return len(lista)


def conferir(cliente, contagens: dict[int, int] = CONTAGENS) -> dict[int, int]:
    """Count no banco por edição; falha se não bater com o esperado."""
    no_banco = {ano: cliente.contar(TABELA, {"ano_pof": f"eq.{ano}"}) for ano in contagens}
    for ano, n in no_banco.items():
        if n != contagens[ano]:
            raise ValueError(f"POF {ano}: {n} registros no banco, esperados {contagens[ano]}")
    return no_banco


def main() -> None:
    from app.config import DOTENV, carregar_configuracao
    from app.supabase import criar_cliente

    config = carregar_configuracao(dotenv=DOTENV)
    dados, _ = ler()
    gravados = gravar(config.supabase_url, config.supabase_secret_key, linhas_para_carga(dados))
    no_banco = conferir(criar_cliente(config))
    print(f"{gravados} registros enviados; no banco: {no_banco}")


if __name__ == "__main__":
    main()
