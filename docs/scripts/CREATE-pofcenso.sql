CREATE OR REPLACE TABLE `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.consumo_estimado` AS

WITH censo_uf_agrupado AS (
  -- 1. Agrega a população municipal do Censo 2022 por UF e pondera idade_mediana e indice_envelhecimento pela população de cada município
  SELECT
    sigla_uf,
    SUM(populacao) AS populacao_total_uf,
    SAFE_DIVIDE(SUM(idade_mediana * populacao), SUM(populacao)) AS media_idade_mediana_uf,
    SAFE_DIVIDE(SUM(indice_envelhecimento * populacao), SUM(populacao)) AS media_indice_envelhecimento_uf
  FROM `basedosdados.br_ibge_censo_2022.municipio`
  WHERE populacao > 0
  GROUP BY 1
),

proporcao_idosos_uf_2022 AS (
  -- 2. Obtém a proporção real de idosos (60+ anos) por UF em 2022 a partir da distribuição etária oficial do IBGE
  -- (Substitui a fórmula inválida indice / (100 + indice), que omitia a população de 15 a 59 anos)
  SELECT
    localidade AS sigla_uf,
    SAFE_DIVIDE(
      SUM(CASE WHEN idade >= 60 THEN populacao ELSE 0 END),
      SUM(populacao)
    ) AS proporcao_idosos_2022
  FROM `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.projecoes_populacao_idade`
  WHERE ano = 2022
    AND sexo = 'Ambos'
    AND LENGTH(localidade) = 2
  GROUP BY 1
),

fato_unico AS (
  SELECT *
  FROM `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.fato_consumo_domiciliar`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_domicilio ORDER BY idade_chefe DESC) = 1
),

coeficientes_consumo AS (
  -- 3. Calcula o consumo per capita médio ponderado pelo peso_final para os grupos 60+ e <60 em cada UF
  -- (Substitui o MAX() anterior, que selecionava acidentalmente apenas o arranjo Unipessoal)
  SELECT
    sigla_uf,
    SAFE_DIVIDE(
      SUM(CASE WHEN is_60_mais = TRUE THEN consumo_per_capita_kwh * peso_final END),
      SUM(CASE WHEN is_60_mais = TRUE THEN peso_final END)
    ) AS consumo_per_capita_60_mais,
    SAFE_DIVIDE(
      SUM(CASE WHEN is_60_mais = FALSE THEN consumo_per_capita_kwh * peso_final END),
      SUM(CASE WHEN is_60_mais = FALSE THEN peso_final END)
    ) AS consumo_per_capita_sub_60
  FROM fato_unico
  GROUP BY 1
)

-- 4. Consumo total de energia estimado para o ano-base de 2022 por Estado (UF)
SELECT
    c.sigla_uf,
    c.populacao_total_uf,
    CAST(ROUND(c.populacao_total_uf * p.proporcao_idosos_2022) AS INT64) AS populacao_idosa_total_uf,
    p.proporcao_idosos_2022,
    c.media_idade_mediana_uf,
    c.media_indice_envelhecimento_uf,

    -- Consumo estimado do grupo de idosos (60+)
    (ROUND(c.populacao_total_uf * p.proporcao_idosos_2022) * COALESCE(coef.consumo_per_capita_60_mais, 0))
      AS consumo_estimado_idosos_kwh,

    -- Consumo estimado do grupo não idoso (<60)
    ((c.populacao_total_uf - ROUND(c.populacao_total_uf * p.proporcao_idosos_2022)) * COALESCE(coef.consumo_per_capita_sub_60, 0))
      AS consumo_estimado_nao_idosos_kwh,

    -- Consumo residencial total estimado para 2022
    (
      (ROUND(c.populacao_total_uf * p.proporcao_idosos_2022) * COALESCE(coef.consumo_per_capita_60_mais, 0)) +
      ((c.populacao_total_uf - ROUND(c.populacao_total_uf * p.proporcao_idosos_2022)) * COALESCE(coef.consumo_per_capita_sub_60, 0))
    ) AS consumo_residencial_total_2022_kwh

FROM censo_uf_agrupado c
INNER JOIN proporcao_idosos_uf_2022 p ON c.sigla_uf = p.sigla_uf
LEFT JOIN coeficientes_consumo coef ON c.sigla_uf = coef.sigla_uf
WHERE c.populacao_total_uf > 0;
