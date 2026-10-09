# Documentação do Processo de ETL e Integração de Dados

Este documento descreve a engenharia de dados realizada para analisar o impacto do envelhecimento populacional no consumo de energia elétrica residencial no Brasil, integrando microdados amostrais (POF) com dados censitários universais (Censo 2022).

## 1. Visão Geral da Arquitetura

O processo foi executado inteiramente no Google BigQuery, utilizando a técnica de Interpolação de Coeficientes. Esta técnica permite que padrões de consumo identificados em uma pesquisa detalhada (POF 2017-2018) sejam projetados sobre a população total de um período mais recente (Censo 2022).

## 2. Passo a Passo do ETL

### Fase 1: Extração e Consolidação de Microdados (POF)

**Objetivo:** Criar a tabela `fato_consumo_domiciliar` com a granularidade de domicílio.

- **Mapeamento de Fontes:** Foram extraídas as tabelas `morador_2017` e `despesa_coletiva_2017` do projeto público `basedosdados`.
- **Identificação do Produto:** Localizamos o código de item `600101` (Energia Elétrica) no dicionário da POF para isolar apenas gastos energéticos.
- **Filtragem Hierárquica:**
  - Filtramos apenas a Pessoa de Referência (`V0306 IN ('01', '1')`) para garantir que cada domicílio fosse contabilizado apenas uma vez.
  - Realizamos o `JOIN` entre as tabelas usando a chave composta `id_domicilio`.
- **Inclusão de Pesos Amostrais:** Extraímos a variável `peso_final` (da tabela `morador_2017`) e a incorporamos à tabela. O peso amostral é fundamental para corrigir os vieses da amostra e garantir que as médias reflitam o cenário real da população brasileira.
- **Tratamento de Dados:** Aplicamos `TRIM()` nos IDs para evitar erros de espaços em branco e `SAFE_CAST` para garantir que valores não numéricos fossem tratados como nulos em vez de interromper a query.

### Fase 2: Cálculo de Coeficientes de Consumo

**Objetivo:** Criar a tabela `dim_coeficientes_consumo` com médias por perfil.

Nesta etapa, os dados foram agrupados por:

- **Arranjo Familiar:** Classificados em Unipessoal (Mononuclear), Dupla ou Multipessoal.
- **Faixa Etária:** Flag booleana `is_60_mais` baseada na idade do chefe.
- **Localidade:** Agrupamento por `sigla_uf`.

**A lógica do Consumo Estimado em kWh:**
O cálculo central para responder à hipótese do TCC foi o Consumo Médio Per Capita. Como muitos domicílios não reportaram o kWh direto (`V9005`), a ETL prioriza os dados existentes e calcula a média ponderada por perfil social, permitindo que a projeção futura use esses "pesos" estáveis por grupo etário.

### Fase 3: Integração Censitária (Censo 2022)

**Objetivo:** Gerar a tabela final `censo_2022_consumo_estimado`.

- **Dedução da População Idosa:** Como a tabela de municípios do Censo 2022 fornece o `indice_envelhecimento`, aplicamos a fórmula matemática para extrair o valor absoluto de idosos:
  $$População Idosa \approx População \times \left( \frac{Indice}{100 + Indice} \right)$$
- **Aplicação dos Coeficientes:** Multiplicamos a população real recenseada em 2022 pelos coeficientes de consumo (kWh/pessoa) obtidos na Fase 2, segregando por UF e grupo etário (60+ vs Sub-60).

### Fase 4: Projeções Populacionais e Migração para o Supabase

**Objetivo:** Preparar os dados demográficos projetados pelo IBGE (até 2070) e centralizar todas as tabelas geradas na nuvem.

- **Processamento Local (Python):** O script `migraDados.py` recebe as tabelas de projeção de idade do IBGE. Ele realiza a limpeza de colunas não utilizadas, adequação de nomenclaturas e executa um processo de *unpivot* (*melt*) para converter os dados dos anos (antes divididos em colunas) para o formato longo. Este pré-processamento prepara os dados de projeções de idade fornecidas pelo IBGE até 2070 para que a formatação da tabela seja importável para o Supabase.
- **Disponibilização no Supabase:** Após a estruturação dos dados e extração do BigQuery, **todas as tabelas geradas pela ETL foram disponibilizadas no Supabase**. Dessa forma, o backend e a interface da aplicação consomem os dados curados diretamente de um banco de dados PostgreSQL estruturado em nuvem.

## 3. Como Reproduzir no Google Cloud

Para replicar este processo, siga os passos abaixo no seu Console do Google Cloud:

1. **Criar o Dataset de Destino:**
   No BigQuery, crie um dataset dentro de um projeto.
2. **Executar o Script de Microdados (Passo 1):**
   Abra uma nova aba do SQL Editor. Execute a query que gera a `fato_consumo_domiciliar` (utilizando os códigos de produto `600101` e filtros de chefe de domicílio).
3. **Executar o Script de Coeficientes (Passo 2):**
   Gere a tabela de dimensões realizando o `GROUP BY` por `is_60_mais` e `sigla_uf`.
4. **Executar a Integração Final (Passo 3):**
   Execute a query que cruza a `basedosdados.br_ibge_censo_2022.municipio` com a sua tabela de coeficientes criada no passo anterior.

Atenção! Os scripts estão localizados na pasta [scripts](./scripts).

## 4. Resumo e Função das Tabelas Geradas

O processo de ETL resulta em quatro tabelas principais disponibilizadas no banco, cada uma com um papel específico no sistema:

1. **`fato_consumo_domiciliar`:** Tabela base (nível microdado) gerada a partir da POF. Sua função é armazenar o perfil de cada domicílio amostrado (arranjo familiar, presença de idosos, consumos e o `peso_final`). É a matéria-prima para os cálculos estatísticos e para a expansão amostral.
2. **`dim_coeficientes_consumo`:** Tabela de suporte. Sua função é consolidar as médias históricas (ex: média de consumo kWh) agrupadas por perfil e Unidade da Federação. Ela dita os "pesos" que serão aplicados sobre as populações.
3. **`censo_2022_consumo_estimado`:** Tabela que representa o "Ano Base". Ela consolida as populações reais do Censo e estima quanto de energia cada estado consumiu em 2022 (separado por grupo etário). Seus dados servem como tensores de entrada (*Features*) para calibrar as projeções da IA para os próximos anos.
4. **`projecoes_populacao_idade`:** Originada via processamento Python (planilha IBGE). Sua função é alimentar o motor de cálculo com as populações projetadas do Brasil até 2070. Ao cruzar essa projeção com a `dim_coeficientes_consumo`, o sistema consegue simular as tendências do consumo residencial nacional a longo prazo.
