-- ==============================================================================
-- PROCED-TCC: Consultas Analíticas e Machine Learning no BigQuery (BigQuery AI & ML)
-- ==============================================================================
-- Este arquivo reúne os scripts de análise avançada recomendados para o TCC,
-- utilizando recursos nativos do BigQuery ML e Vertex AI conforme a skill bigquery-ai-ml.
-- Substitua `{PROJETO}` e `{DATASET}` pelos identificadores do seu ambiente no GCP.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXPLORAÇÃO ESTATÍSTICA MANDATÓRIA (ML.DESCRIBE_DATA)
-- ------------------------------------------------------------------------------
-- Avalia distribuição estatística, quartis, desvio-padrão e nulos dos microdados da POF.
SELECT *
FROM ML.DESCRIBE_DATA(
  TABLE `{PROJETO}.{DATASET}.fato_consumo_domiciliar`
);

-- Amostra exploratória inicial
SELECT 
  id_domicilio,
  sigla_uf,
  arranjo_familiar,
  idade_chefe,
  is_60_mais,
  consumo_total_kwh,
  gasto_total_rs,
  consumo_per_capita_kwh,
  peso_final,
  SAFE_DIVIDE(gasto_total_rs, consumo_total_kwh) AS tarifa_implicita_rs_kwh
FROM `{PROJETO}.{DATASET}.fato_consumo_domiciliar`
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 2. DETECÇÃO DE ANOMALIAS E OUTLIERS NOS MICRODADOS (AI.DETECT_ANOMALIES)
-- ------------------------------------------------------------------------------
-- Identifica domicílios com consumos absurdos ou erros de digitação na POF (como 1.640 kWh/mês per capita)
-- e inconsistências na tarifa implícita (gasto / kWh).
SELECT *
FROM AI.DETECT_ANOMALIES(
  (
    SELECT
      CAST(id_domicilio AS STRING) AS id_domicilio,
      sigla_uf,
      arranjo_familiar,
      idade_chefe,
      qtd_moradores,
      consumo_total_kwh,
      consumo_per_capita_kwh,
      SAFE_DIVIDE(gasto_total_rs, consumo_total_kwh) AS tarifa_implicita
    FROM `{PROJETO}.{DATASET}.fato_consumo_domiciliar`
  ),
  contamination => 0.01 -- Sinaliza o 1% com comportamento mais discrepante
)
ORDER BY is_anomaly DESC, anomaly_score DESC
LIMIT 50;

-- ------------------------------------------------------------------------------
-- 3. ANÁLISE DE FATORES DETERMINANTES DO CONSUMO (AI.KEY_DRIVERS)
-- ------------------------------------------------------------------------------
-- Identifica as variáveis que mais influenciam o consumo per capita elétrico,
-- enriquecendo a tabela fato com variáveis físicas e financeiras de pof2017_domicilio e pof2017_morador.
SELECT *
FROM AI.KEY_DRIVERS(
  (
    SELECT
      f.consumo_per_capita_kwh,
      f.arranjo_familiar,
      f.is_60_mais,
      f.sigla_uf,
      f.qtd_moradores,
      -- Variáveis físicas do domicílio
      COALESCE(d.V0201, 1) AS tipo_domicilio,
      COALESCE(d.V0205, 5) AS qtd_comodos,
      COALESCE(d.situacao, 1) AS situacao_censitaria, -- 1=Urbano, 2=Rural
      -- Renda per capita disponível do domicílio
      COALESCE(m.renda_disponivel_per_capita, 0) AS renda_disponivel_per_capita
    FROM `{PROJETO}.{DATASET}.fato_consumo_domiciliar` f
    LEFT JOIN `{PROJETO}.{DATASET}.pof2017_domicilio` d
      ON f.id_domicilio = d.id_domicilio
    LEFT JOIN (
      SELECT id_domicilio, AVG(renda_disponivel_per_capita) AS renda_disponivel_per_capita
      FROM `{PROJETO}.{DATASET}.pof2017_morador`
      GROUP BY 1
    ) m ON f.id_domicilio = m.id_domicilio
  ),
  target_column => 'consumo_per_capita_kwh'
);

-- ------------------------------------------------------------------------------
-- 4. TREINAMENTO DE MODELO BOOSTED TREE NATIVO NO BIGQUERY ML (ML_GB EVOLUÍDO)
-- ------------------------------------------------------------------------------
-- Substitui os modelos com baixo R² (0,16) por um modelo Boosted Trees nativo no BQML,
-- incorporando variáveis de infraestrutura e renda para explicar o consumo.
CREATE OR REPLACE MODEL `{PROJETO}.{DATASET}.modelo_consumo_residencial_gb`
OPTIONS(
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['consumo_per_capita_kwh'],
  enable_global_explain = TRUE
) AS
SELECT
  f.consumo_per_capita_kwh,
  f.sigla_uf,
  f.arranjo_familiar,
  f.idade_chefe,
  f.is_60_mais,
  f.qtd_moradores,
  f.peso_final,
  d.situacao,
  d.V0205 AS total_comodos,
  m.renda_disponivel_per_capita
FROM `{PROJETO}.{DATASET}.fato_consumo_domiciliar` f
LEFT JOIN `{PROJETO}.{DATASET}.pof2017_domicilio` d ON f.id_domicilio = d.id_domicilio
LEFT JOIN (
  SELECT id_domicilio, AVG(renda_disponivel_per_capita) AS renda_disponivel_per_capita
  FROM `{PROJETO}.{DATASET}.pof2017_morador`
  GROUP BY 1
) m ON f.id_domicilio = m.id_domicilio;

-- Avaliação das métricas do modelo (R², MAE, RMSE)
SELECT *
FROM ML.EVALUATE(MODEL `{PROJETO}.{DATASET}.modelo_consumo_residencial_gb`);

-- Importância global de cada variável no modelo
SELECT *
FROM ML.GLOBAL_EXPLAIN(MODEL `{PROJETO}.{DATASET}.modelo_consumo_residencial_gb`);

-- ------------------------------------------------------------------------------
-- 5. PREVISÃO TEMPORAL DE CONSUMO / TRANSIÇÃO DEMOGRÁFICA (AI.FORECAST - TimesFM)
-- ------------------------------------------------------------------------------
-- Exemplo de uso de TimesFM para projetar a população de idosos com intervalos de confiança.
-- Observa a divisão cronológica estrita em histórico (<= 2022) e avaliação (> 2022).
WITH serie_populacao AS (
  SELECT
    localidade AS uf,
    PARSE_DATE('%Y', CAST(ano AS STRING)) AS data_referencia,
    SUM(populacao) AS pop_idosa
  FROM `{PROJETO}.{DATASET}.projecoes_populacao_idade`
  WHERE sexo = 'Ambos'
    AND idade >= 60
    AND LENGTH(localidade) = 2
  GROUP BY 1, 2
)
SELECT *
FROM AI.FORECAST(
  (
    SELECT *
    FROM serie_populacao
    WHERE data_referencia <= DATE '2022-01-01'
  ),
  time_col => 'data_referencia',
  target_col => 'pop_idosa',
  series_col => 'uf',
  horizon => 10,
  confidence_level => 0.95
);
