# Dicionário de Dados

Este dicionário descreve as tabelas curadas resultantes do processo de ETL, integrando dados da Pesquisa de Orçamentos Familiares (POF 2017-2018) e do Censo Demográfico 2022.

## 1. Tabela: fato_consumo_domiciliar

**Descrição:** Tabela principal de microdados consolidados por domicílio. Une o perfil sociodemográfico da pessoa de referência (chefe) com as despesas reais de energia elétrica.

| Nome do Campo | Tipo | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| sigla_uf | STRING | Sigla da Unidade da Federação. | despesa_coletiva_2017.sigla_uf |
| id_domicilio | STRING | Identificador único do domicílio na POF. | Chave primária de junção (Join Key). |
| qtd_moradores | INT2 | Total de residentes no domicílio. | COUNT(DISTINCT id_informante) na base total. |
| arranjo_familiar | STRING | Classificação do tipo de lar. | Unipessoal, Casal/Dupla ou Multipessoal (3+). |
| idade_chefe | INT2 | Idade da pessoa de referência do lar. | Extraído da tabela morador_2017. |
| is_60_mais | BOOL | Flag para identificar chefes idosos. | TRUE se idade_chefe >= 60. |
| consumo_total_kwh | FLOAT8 | Consumo elétrico mensal declarado (kWh). | Variável V9005 (original do IBGE). |
| gasto_total_rs | FLOAT8 | Valor pago mensalmente em R$ (deflacionado). | Variável V8000_deflacionado. |
| consumo_per_capita_kwh | FLOAT8 | Consumo individual médio do domicílio. | consumo_total_kwh / qtd_moradores. |
| peso_final | FLOAT8 | Indica quantas famílias da população brasileira aquele único domicílio da amostra representa. | Serve para "inflar" os dados da pesquisa (que é feita em apenas alguns lares) para o total do Brasil, corrigindo distorções e garantindo que os resultados (como a média de consumo de energia) sejam estatisticamente válidos para todo o país. |

## 2. Tabela: dim_coeficientes_consumo

**Descrição:** Tabela de suporte (lookup) que armazena as médias históricas de consumo por perfil. Utilizada para calibrar as projeções demográficas.

| Nome do Campo | Tipo | Descrição | Regra de Negócio |
| --- | --- | --- | --- |
| sigla_uf | STRING | Unidade da Federação. | Agrupador geográfico. |
| arranjo_familiar | STRING | Tipo de estrutura do domicílio. | Agrupador de estrutura. |
| is_60_mais | BOOL | Segmentação por faixa etária do chefe. | Público-alvo vs. Controle. |
| media_consumo_total_kwh | FLOAT8 | Média de kWh por domicílio do perfil. | AVG(consumo_total_kwh). |
| media_consumo_per_capita_kwh | FLOAT8 | Média de kWh por pessoa do perfil. | AVG(consumo_per_capita_kwh). |
| media_gasto_rs | FLOAT8 | Gasto médio financeiro do perfil. | AVG(gasto_total_rs). |

## 3. Tabela: censo_2022_consumo_estimado

**Descrição:** Tabela de integração final que aplica os coeficientes da POF sobre a população real recenseada em 2022. Serve como o "Ano Base".

| Nome do Campo | Tipo | Descrição | Origem do Dado |
| --- | --- | --- | --- |
| sigla_uf | STRING | Unidade da Federação. | Censo 2022. |
| populacao_total_uf | INT2 | População residente total em 2022. | br_ibge_censo_2022.municipio. |
| populacao_idosa_total_uf | INT2 | Total de idosos (60+) estimado na UF. | Calculado via Índice de Envelhecimento. |
| proporcao_idosos_2022 | FLOAT8 | % da população que é idosa no estado. | Razão Idosa / Total. |
| media_idade_mediana_uf | FLOAT8 | Idade que divide a população ao meio. | Média ponderada municipal. |
| consumo_estimado_idosos_kwh | FLOAT8 | Projeção de demanda para o grupo 60+. | pop_idosa * coef_consumo_60plus. |
| consumo_estimado_nao_idosos_kwh | FLOAT8 | Projeção de demanda para o grupo <60. | pop_não_idosa * coef_consumo_sub60. |
| consumo_residencial_total_2022_kwh | FLOAT8 | Estimativa de demanda total da UF. | Soma dos consumos estimados. |

## 4. Tabelas da Pesquisa de Orçamentos Familiares (POF)

As tabelas com nomenclaturas iniciadas por `pof2017` possuem dicionário de dados localizado em: [basedosdados.org](https://basedosdados.org/dataset/a1b6d2b6-4aa6-47e7-a517-8a21b28b7254?table=7b880731-ffa2-4bde-a290-ae058b3acf51).

## 5. Tabelas do Censo 2022

As tabelas com nomenclaturas iniciadas por `censo2022` possuem dicionário de dados localizado em: [basedosdados.org](https://basedosdados.org/dataset/08a1546e-251f-4546-9fe0-b1e6ab2b203d?table=cf9537b5-6198-455f-a8b0-7c762e94d79c).

## Notas Metodológicas para o TCC:

- **Código de Produto:** A Base dos Dados mapeou o consumo elétrico sob o código 600101 para a POF 2017-2018.
- **Tratamento de Nulos:** Domicílios sem registro de kWh (V9005) foram mantidos como NULL para não distorcer as médias com zeros artificiais, garantindo a integridade estatística.
- **Integração:** A conexão entre POF e Censo 2022 foi realizada via Interpolação de Coeficientes, uma técnica para unir pesquisas amostrais com censos universais.