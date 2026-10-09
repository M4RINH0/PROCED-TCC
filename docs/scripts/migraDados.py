import pandas as pd
from sqlalchemy import create_engine

print("Lendo o arquivo Excel...")
excel_path = "projecoes_2024_idade.xlsx"
df = pd.read_excel(excel_path, sheet_name="1) POP_IDADE SIMPLES")

df = df.drop(columns=["LOCAL"])  # Descarta a coluna 'LOCAL' original

df = df.rename(
    columns={
        "CÓD.": "cod_local",
        "SIGLA": "localidade",
        "SEXO": "sexo",
        "IDADE": "idade",
    }
)


# Tratamento e Mapeamento de Valores (Sexo e Localidade) para ficar de acordo com o padrão utilizado nas demais tabelas
# e no Supabase (enum type)
mapeamento_sexo = {"Mulheres": "Mulher", "Homens": "Homem"}

mapeamento_localidade = {
    "BR": "Brasil",
    "NO": "Norte",
    "ND": "Nordeste",
    "SD": "Sudeste",
    "CO": "Centro-Oeste",
    "SU": "Sul",
}

# .replace mantém inalterados os demais valores (ex: 'Ambos' e siglas das UFs como SP, RJ, etc.)
df["sexo"] = df["sexo"].replace(mapeamento_sexo)
df["localidade"] = df["localidade"].replace(mapeamento_localidade)

# 5. Normalização dos Anos (Unpivot / Melt)
id_vars = ["cod_local", "localidade", "sexo", "idade"]
colunas_anos = [col for col in df.columns if col not in id_vars]

print("Normalizando dados para formato longo (linhas por ano)...")
df_normalizado = df.melt(
    id_vars=id_vars,
    value_vars=colunas_anos,
    var_name="ano",
    value_name="populacao",
)

# Ajuste de tipos
df_normalizado["ano"] = df_normalizado["ano"].astype(int)
df_normalizado["populacao"] = df_normalizado["populacao"].astype(int)

# Reordenação final das colunas
colunas_finais = ["cod_local", "localidade", "sexo", "idade", "ano", "populacao"]
df_normalizado = df_normalizado[colunas_finais]

df_normalizado.to_csv("projecoes_normalizadas_pronto.csv", index=False, encoding="utf-8")
print("Arquivo projecoes_normalizadas_pronto.csv gerado com sucesso!")