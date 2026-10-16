CREATE OR REPLACE TABLE `basestcc2.TCC2.fato_consumo_domiciliar`
AS
WITH
  pof_moradores_total AS (
    -- 1. Calcula o tamanho real de cada família na base completa de moradores (Sem filtros prévios)
    SELECT
      TRIM(id_domicilio) AS id_domicilio,
      COUNT(DISTINCT id_informante) AS qtd_moradores
    FROM `basedosdados.br_ibge_pof.morador_2017`
    GROUP BY 1
  ),
  pof_chefes_perfil AS (
    -- 2. Identifica a pessoa de referência (chefe) garantindo exatamente 1 linha por domicílio:
    -- Prioriza a Unidade de Consumo principal (MOD(id_unidade_consumo, 100) = 1) e, em caso de empate,
    -- o chefe de maior idade (Premissa P8), eliminando as 105 linhas duplicadas na origem.
    SELECT
      TRIM(id_domicilio) AS id_domicilio,
      SAFE_CAST(idade AS INT64) AS idade_chefe,
      peso_final
    FROM `basedosdados.br_ibge_pof.morador_2017`
    WHERE V0306 IN ('01', '1', 'Pessoa de referência')
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY TRIM(id_domicilio)
      ORDER BY SAFE_CAST(idade AS INT64) DESC, SAFE_CAST(id_unidade_consumo AS INT64) ASC
    ) = 1
  ),
  pof_energia_domicilio AS (
    -- 3. Agrega o consumo de energia elétrica (código 600101)
    SELECT
      TRIM(id_domicilio) AS id_domicilio,
      ANY_VALUE(sigla_uf) AS sigla_uf,
      SUM(SAFE_CAST(V9005 AS FLOAT64)) AS consumo_total_kwh,
      SUM(V8000_deflacionado) AS gasto_total_rs
    FROM `basedosdados.br_ibge_pof.despesa_coletiva_2017`
    WHERE V9001 = '600101'
    GROUP BY 1
  )

-- 4. Junção final por id_domicilio (apenas domicílios com consumo em kWh declarado, conforme critério de exclusão)
SELECT
    e.sigla_uf,
    e.id_domicilio,
    m.qtd_moradores,
    CASE
        WHEN m.qtd_moradores = 1 THEN 'Unipessoal (Mononuclear)'
        WHEN m.qtd_moradores = 2 THEN 'Casal ou Dupla'
        ELSE 'Multipessoal (3+)'
    END AS arranjo_familiar,
    c.idade_chefe,
    IF(c.idade_chefe >= 60, TRUE, FALSE) AS is_60_mais,
    c.peso_final,
    e.consumo_total_kwh,
    e.gasto_total_rs,
    SAFE_DIVIDE(e.consumo_total_kwh, m.qtd_moradores) AS consumo_per_capita_kwh
FROM pof_energia_domicilio e
INNER JOIN pof_moradores_total m
    ON e.id_domicilio = m.id_domicilio
INNER JOIN pof_chefes_perfil c
    ON e.id_domicilio = c.id_domicilio
WHERE e.consumo_total_kwh > 0;
