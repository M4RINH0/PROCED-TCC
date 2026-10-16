# Scripts do Processo de ETL

Este diretório contém os scripts necessários para processar e estruturar os dados do TCC. A execução deve seguir uma ordem lógica para garantir que as dependências entre as tabelas sejam respeitadas, finalizando com a preparação dos dados que serão enviados ao Supabase.

## Ordem de Execução e Descrição dos Scripts

### 1. `CREATE-pof.sql`
- **O que faz:** Gera a tabela base `fato_consumo_domiciliar`. Extrai os microdados da Pesquisa de Orçamentos Familiares (POF 2017-2018), filtrando gastos específicos com energia elétrica (código 600101) e calculando o consumo per capita para cada domicílio.
- **Ambiente:** Google BigQuery.

### 2. `CREATE-coeficientes.sql`
- **O que faz:** Depende da tabela anterior. Cria a tabela dimensão `dim_coeficiente_consumo`, calculando as médias de consumo e gasto agrupadas por perfil (arranjo familiar e se a pessoa de referência possui 60 anos ou mais).
- **Ambiente:** Google BigQuery.

### 3. `CREATE-pofcenso.sql`
- **O que faz:** Depende da tabela de coeficientes. Cruza as médias de consumo calculadas a partir da POF com os dados demográficos absolutos do Censo 2022. O resultado é a tabela final `consumo_estimado`, que estima o consumo total de energia segmentado por população idosa e não idosa por Unidade da Federação.
- **Ambiente:** Google BigQuery.

### 4. `CREATE-pof-historica.sql`
- **O que faz:** Cria no Supabase (PostgreSQL) a tabela `fato_consumo_pof_historica` para receber os microdados harmonizados das POFs 2002-2003 e 2008-2009, utilizados na estimação da tendência dos arranjos domiciliares (Premissa P13).
- **Ambiente:** Supabase (PostgreSQL).

### 5. `migraDados.py` (Localizado na raiz do projeto)
- **O que faz:** Prepara os dados das projeções de idade fornecidas pelo IBGE até 2070, disponível em [www.ibge.gov.br](https://www.ibge.gov.br/estatisticas/sociais/populacao/9109-projecao-da-populacao.html). O script realiza a limpeza, renomeação de colunas e transformação da estrutura dos dados (unpivot/melt) para um formato longo, gerando o arquivo `projecoes_normalizadas_pronto.csv` para que a formatação da tabela (`projecoes_populacao_idade`) seja perfeitamente importável para o banco de dados PostgreSQL no Supabase.
- **Ambiente:** Python (Local).
