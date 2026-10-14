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
- **Critério de exclusão aplicado na extração:** ficaram de fora os domicílios sem declaração válida de consumo de energia (sem kWh na `V9005`), conforme o critério de exclusão da Metodologia do TCC. Segundo a equipe, saíram cerca de 6 mil registros. Por isso a tabela carregada no Supabase não tem nenhum domicílio com kWh nulo ou zero (o menor valor é 13 kWh), e a soma de `peso_final` (63,68 milhões de domicílios, depois da premissa P8) cobre 92,4% dos 68,9 milhões de domicílios estimados pela POF 2017 a 2018 (premissa P9).
- **Domicílios com mais de uma unidade de consumo:** cada unidade de consumo da POF tem a sua pessoa de referência, então o filtro de chefe não garante uma linha por domicílio. Há 99 `id_domicilio` repetidos em 204 linhas, com o mesmo consumo, o mesmo peso e os mesmos moradores. A projeção mantém só a linha do chefe de maior idade (premissa P8).

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
2. **`dim_coeficientes_consumo`:** Tabela de suporte. Sua função é consolidar as médias históricas (ex: média de consumo kWh) agrupadas por perfil e Unidade da Federação. Ela dita os "pesos" que serão aplicados sobre as populações. **Não é usada pela API nem pelas projeções:** foi calculada com média simples, sem o peso amostral; as médias por arranjo saem da `fato_consumo_domiciliar` com `peso_final`.
3. **`censo_2022_consumo_estimado`:** Tabela que representa o "Ano Base". Ela consolida as populações reais do Censo e estima quanto de energia cada estado consumiu em 2022 (separado por grupo etário). Seus dados servem como tensores de entrada (*Features*) para calibrar as projeções da IA para os próximos anos.
4. **`projecoes_populacao_idade`:** Originada via processamento Python (planilha IBGE). Sua função é alimentar o motor de cálculo com as populações projetadas do Brasil até 2070. Ao cruzar essa projeção com a `dim_coeficientes_consumo`, o sistema consegue simular as tendências do consumo residencial nacional a longo prazo.

## 5. Projeções de 2026 a 2070 (`backend/etl`)

Gerado por `.venv/Scripts/python -m etl.pipeline` (na pasta `backend/`), a partir das tabelas do Supabase. O código está em `backend/etl/modelagem.py`; as fórmulas, em `backend/app/calculo.py`.

**Leitura e conferência**
- A REST do Supabase devolve no máximo mil linhas por requisição. O cliente pagina e confere o total pelo cabeçalho `Content-Range` (contagem exata): se faltar linha, a leitura falha em vez de seguir pela metade. A auditoria registra as linhas lidas de cada tabela contra o count do banco.
- A população vem das 27 UFs pela lista explícita de siglas, com sexo "Ambos". As linhas de total (regiões e Brasil) nunca entram no cálculo. A linha "Brasil" é lida só para conferência: a soma das 27 UFs confere com ela em todos os anos e idades (de 2018 a 2070, diferença máxima zero; conferido em 14/10/2026).

**Etapas**
1. Preparação: premissa P8 (domicílio repetido fica com o chefe de maior idade), faixa etária do chefe e célula (faixa e arranjo).
2. Auditoria (`saida/auditoria.json`): peso ausente, repetidos, chefes com menos de 18 anos, domicílios acima de 1.000 kWh (mantidos), cobertura da POF e tabela por célula, com aviso nas células com menos de 30 domicílios.
3. Ponte comum (premissa P2): taxa de chefia por faixa e arranjo com os pesos de 2018; domicílios projetados por ano.
4. Método das taxas (`taxas`), contrafactual (`contrafactual`: o total de domicílios segue a projeção e a distribuição entre as células fica na de 2026, premissa P10) e a validação da ponte contra o Censo 2022. A projeção é a mesma da API (`app.calculo.Projecao`).
5. Calibração (premissa P12): `consumo_total_calibrado_kwh_mes` = consumo por pessoa vezes a população do IBGE no ano. O consumo total bruto (`consumo_total_kwh_mes`) fica só como diagnóstico.
6. Método de machine learning (`ml_rf` e `ml_gb`): validação cruzada, métricas (`metricas_modelos.json`) e importância das variáveis (`importancia_variaveis.csv`). A projeção por reponderação está pausada (`projetar_ml=False`).
7. Análise de sensibilidade da cobertura (premissa P9): saída separada, nunca misturada ao resultado principal.

## 6. POFs anteriores: 2002 a 2003 e 2008 a 2009 (`fato_consumo_pof_historica`)

Usadas só para estimar a tendência dos arranjos domiciliares por faixa etária do chefe (premissa P13). A `fato_consumo_domiciliar` (POF 2017 a 2018) não muda.

**Origem.** Gerados a partir dos microdados oficiais do IBGE (`ftp.ibge.gov.br/Orcamentos_Familiares`), com as mesmas regras da POF 2017 a 2018:
- consumo mensal em kWh, somado por domicílio;
- quantidade final do IBGE, com a coluna `kwh_imputado` marcando as imputações;
- chefe = pessoa de referência da unidade de consumo com maior idade (equivale à premissa P8);
- arranjo pelo número de moradores (1, 2, 3 ou mais);
- só domicílios com conta de luz; não há gasto em reais.

| Edição | Item de energia elétrica | Peso | Domicílios |
|---|---|---|---|
| 2002 a 2003 | quadro 07, item 00202 | `fator` | 39.458 |
| 2008 a 2009 | V9001 = 600201 | `PESO_FINAL` | 49.268 |
| 2017 a 2018 | V9001 = 600101 | `peso_final` | 52.207 (52.102 depois da P8) |

**Carga.** Os CSVs (`fato_consumo_domiciliar_pof2002.csv` e `fato_consumo_domiciliar_pof2008.csv`) ficam em `backend/etl/entrada/`, fora do git. A tabela é criada por `docs/scripts/CREATE-pof-historica.sql`, no editor SQL do Supabase, e carregada por `.venv/Scripts/python -m etl.historica` (na pasta `backend/`), que:
1. confere colunas, contagens, chave única e as regras de derivação (arranjo, 60 anos ou mais, consumo per capita);
2. grava todos os registros por upsert na chave (`ano_pof`, `id_domicilio`), em lotes de mil;
3. confere o count no banco por edição.

A carga leva todos os registros, inclusive os 240 (2002) e 88 (2008) domicílios fora da rede geral (`energia_rede_geral` falso). O filtro é aplicado no cálculo (P13).
