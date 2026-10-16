CREATE OR REPLACE TABLE `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.dim_coeficiente_consumo` AS
WITH fato_unico AS (
    -- Garante 1 linha por domicílio (chefe de maior idade, Premissa P8) caso a tabela fato ainda contenha duplicatas de UC
    SELECT *
    FROM `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.fato_consumo_domiciliar`
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_domicilio ORDER BY idade_chefe DESC) = 1
)
SELECT
    sigla_uf,
    arranjo_familiar,
    is_60_mais,
    COUNT(*) AS total_domicilios_amostra,
    -- Médias ponderadas pelo fator de expansão amostral (peso_final) da POF 2017-2018 (Premissa P3)
    SAFE_DIVIDE(SUM(consumo_total_kwh * peso_final), SUM(peso_final)) AS media_consumo_total_kwh,
    SAFE_DIVIDE(SUM(consumo_per_capita_kwh * peso_final), SUM(peso_final)) AS media_consumo_per_capita_kwh,
    SAFE_DIVIDE(SUM(gasto_total_rs * peso_final), SUM(peso_final)) AS media_gasto_rs
FROM fato_unico
GROUP BY 1, 2, 3;