CREATE OR REPLACE TABLE `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.consumo_estimado` AS

WITH censo_municipios AS (
  -- 1. Extraímos os dados demográficos do Censo 2022 por município/UF
  SELECT
    sigla_uf,
    id_municipio,
    -- População total recenseada em 2022
    populacao as populacao_2022,
    -- Idade mediana da população daquele município
    idade_mediana,
    -- Razão entre idosos (60+) e jovens (0-14 anos)
    indice_envelhecimento,
    -- Estimativa de idosos no município baseada no índice de envelhecimento
    SAFE_CAST(populacao * (indice_envelhecimento / (100 + indice_envelhecimento)) AS INT64) as populacao_idosa_estimada
  FROM `basedosdados.br_ibge_censo_2022.municipio`
),

censo_uf_agrupado AS (
  -- 2. Métricas demográficas por Estado (UF) para casar com a granularidade da POF
  SELECT
    sigla_uf,
    SUM(populacao_2022) as populacao_total_uf,
    SUM(populacao_idosa_estimada) as populacao_idosa_total_uf,
    AVG(idade_mediana) as media_idade_mediana_uf,
    AVG(indice_envelhecimento) as media_indice_envelhecimento_uf
  FROM censo_municipios
  GROUP BY 1
),

coeficientes_consumo AS (
  -- 3. Pesos de consumo calculados a partir da POF
  SELECT
    sigla_uf,
    -- Consumo médio per capita para o grupo alvo (60+ anos)
    MAX(CASE WHEN is_60_mais = TRUE THEN media_consumo_per_capita_kwh END) as consumo_per_capita_60_mais,
    -- Consumo médio per capita para o grupo de controle (Sub-60)
    MAX(CASE WHEN is_60_mais = FALSE THEN media_consumo_per_capita_kwh END) as consumo_per_capita_sub_60
  FROM `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.dim_coeficiente_consumo`
  GROUP BY 1
)

-- 4. Consumo total de energia estimado para o ano de 2022 por Estado
SELECT
    c.sigla_uf,
    c.populacao_total_uf,
    c.populacao_idosa_total_uf,
    -- Proporção de idosos na UF em 2022
    SAFE_DIVIDE(c.populacao_idosa_total_uf, c.populacao_total_uf) as proporcao_idosos_2022,
    c.media_idade_mediana_uf,
    c.media_indice_envelhecimento_uf,

    -- Consumo estimado do grupo de idosos (População idosa de 2022 * Coeficiente de consumo per capita da POF)
    (c.populacao_idosa_total_uf * COALESCE(coef.consumo_per_capita_60_mais, 0)) as consumo_estimado_idosos_kwh,

    -- Consumo estimado do grupo não idoso
    ((c.populacao_total_uf - c.populacao_idosa_total_uf) * COALESCE(coef.consumo_per_capita_sub_60, 0)) as consumo_estimado_nao_idosos_kwh,

    -- Consumo residencial total estimado para 2022
    (
        (c.populacao_idosa_total_uf * COALESCE(coef.consumo_per_capita_60_mais, 0)) +
        ((c.populacao_total_uf - c.populacao_idosa_total_uf) * COALESCE(coef.consumo_per_capita_sub_60, 0))
        ) as consumo_residencial_total_2022_kwh

FROM censo_uf_agrupado c
         LEFT JOIN coeficientes_consumo coef ON c.sigla_uf = coef.sigla_uf
WHERE c.populacao_total_uf > 0;
