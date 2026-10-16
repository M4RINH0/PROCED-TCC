CREATE OR REPLACE TABLE `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.dim_coeficiente_consumo` AS
SELECT
    sigla_uf,
    arranjo_familiar,
    is_60_mais,
    COUNT(*) as total_domicilios_amostra,
    AVG(consumo_total_kwh) as media_consumo_total_kwh, -- Média de consumo excluindo nulos p/ garantir precisão
    AVG(consumo_per_capita_kwh) as media_consumo_per_capita_kwh,
    AVG(gasto_total_rs) as media_gasto_rs
FROM `{NOME DO SEU PROJETO}.{NOME DO SEU DATASET}.fato_consumo_domiciliar`
GROUP BY 1, 2, 3;