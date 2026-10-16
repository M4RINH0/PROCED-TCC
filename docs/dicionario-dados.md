# Dicionário de Dados

Este dicionário mapeia integralmente as **9 tabelas** presentes no banco de dados PostgreSQL (Supabase), abrangendo as tabelas analíticas curadas pelo processo de ETL, as projeções demográficas do IBGE, os microdados históricos da POF (2002-2003 e 2008-2009) e as tabelas brutas de referência da POF 2017-2018 e do Censo Demográfico 2022.

## Visão Geral das Tabelas no Supabase

| # | Nome da Tabela no Supabase | Linhas | Escopo / Papel na Arquitetura |
| --- | --- | --- | --- |
| 1 | `fato_consumo_domiciliar` | 52.207 | Tabela fato principal (POF 2017-2018) consumida pela API e pelo pipeline de projeções. |
| 2 | `dim_coeficiente_consumo` | 162 | Tabela auxiliar de médias simples por UF, arranjo e faixa (`is_60_mais`). |
| 3 | `consumo_estimado` | 27 | Tabela agregada estadual do Censo 2022 cruzada com coeficientes da POF. |
| 4 | `projecoes_populacao_idade` | 639.639 | Projeções populacionais do IBGE (Edição 2024) por localidade, sexo, idade (0–90+) e ano (2000–2070). |
| 5 | `fato_consumo_pof_historica` | 88.726 | Microdados harmonizados das POFs 2002-2003 e 2008-2009 para tendência dos arranjos (P13). |
| 6 | `pof2017_domicilio` | 57.920 | Microdados brutos de domicílios da POF 2017-2018 (características físicas e infraestrutura). |
| 7 | `pof2017_morador` | 178.431 | Microdados brutos de moradores da POF 2017-2018 (perfil sociodemográfico e rendimentos). |
| 8 | `censo2022_municipio` | 5.570 | Indicadores demográficos municipais consolidados do Censo 2022 (5.570 municípios). |
| 9 | `censo2022_indice_envelhecimento` | 55.700 | Série municipal (2010 e 2022) de índice de envelhecimento, idade mediana e razão de sexo por cor/raça. |

---

## 1. Tabela: `fato_consumo_domiciliar`

**Descrição:** Tabela principal de microdados consolidados por domicílio (POF 2017-2018,5). Une o perfil sociodemográfico da pessoa de referência (chefe) com o consumo físico e a despesa mensal de energia elétrica (código `600101`). Contém 52.207 linhas (52.102 domicílios únicos após desduplicação pela pessoa de referência mais velha na Premissa P8).

| Nome do Campo | Tipo (Supabase) | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| `sigla_uf` | `public.localidade` (ENUM) | Sigla da Unidade da Federação (27 UFs). | `despesa_coletiva_2017.sigla_uf` |
| `id_domicilio` | `FLOAT8` (`double precision`) | Identificador único do domicílio na POF. | Chave de junção (`JOIN` entre despesa e morador). |
| `qtd_moradores` | `INT4` (`integer`) | Total de residentes no domicílio. | `COUNT(DISTINCT id_informante)` na base de moradores. |
| `arranjo_familiar` | `public.arranjo_familiar` (ENUM) | Classificação da estrutura domiciliar. | `'Unipessoal (Mononuclear)'` (1), `'Casal ou Dupla'` (2) ou `'Multipessoal (3+)'` (3+). |
| `idade_chefe` | `INT4` (`integer`) | Idade da pessoa de referência do lar em anos completos. | Extraído de `morador_2017` onde `V0306` indica pessoa de referência. |
| `is_60_mais` | `BOOL` (`boolean`) | Flag para identificar chefes idosos (60 anos ou mais). | `TRUE` se `idade_chefe >= 60`, caso contrário `FALSE`. |
| `consumo_total_kwh` | `FLOAT8` (`double precision`) | Consumo elétrico mensal declarado do domicílio (kWh/mês). | Soma de `V9005` para o item `V9001 = '600101'`. |
| `gasto_total_rs` | `FLOAT8` (`double precision`) | Valor pago mensalmente em R$ (deflacionado). | Soma de `V8000_deflacionado` para o item `V9001 = '600101'`. |
| `consumo_per_capita_kwh` | `FLOAT8` (`double precision`) | Consumo individual médio mensal dentro do domicílio (kWh/mês/pessoa). | `consumo_total_kwh / qtd_moradores`. |
| `peso_final` | `FLOAT8` (`double precision`) | Fator de expansão amostral da POF 2017-2018. | Indica quantos domicílios da população brasileira aquele registro representa, corrigindo o desenho amostral (Premissa P3). |

---

## 2. Tabela: `dim_coeficiente_consumo`

**Descrição:** Tabela auxiliar (lookup) com 162 linhas (27 UFs $\times$ 3 arranjos $\times$ 2 grupos etários) que armazena médias simples de consumo e gasto por perfil, gerada pelo script [`CREATE-coeficientes.sql`](./scripts/CREATE-coeficientes.sql). **Nota:** não é consumida pela API nem pelo motor de projeção principal, que calculam as taxas diretamente sobre `fato_consumo_domiciliar` ponderadas por `peso_final`.

| Nome do Campo | Tipo (Supabase) | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| `id` | `INT4` (`integer`, PK) | Identificador sequencial da linha na dimensão. | Chave primária gerada no banco (`1` a `162`). |
| `sigla_uf` | `public.localidade` (ENUM) | Sigla da Unidade da Federação. | Agrupador geográfico (`GROUP BY`). |
| `arranjo_familiar` | `public.arranjo_familiar` (ENUM) | Tipo de estrutura do domicílio. | Agrupador de estrutura (`Unipessoal (Mononuclear)`, `Casal ou Dupla`, `Multipessoal (3+)`). |
| `is_60_mais` | `BOOL` (`boolean`) | Segmentação por faixa etária do chefe (60+ vs. abaixo de 60). | Agrupador demográfico (`TRUE` / `FALSE`). |
| `total_domicilios_amostra` | `INT8` (`bigint`) | Quantidade de registros na amostra da POF para o perfil na UF. | `COUNT(*)` sobre `fato_consumo_domiciliar`. |
| `media_consumo_total_kwh` | `FLOAT8` (`double precision`) | Média aritmética simples de kWh/mês por domicílio do perfil. | `AVG(consumo_total_kwh)`. |
| `media_consumo_per_capita_kwh` | `FLOAT8` (`double precision`) | Média aritmética simples de kWh/mês por pessoa do perfil. | `AVG(consumo_per_capita_kwh)`. |
| `media_gasto_rs` | `FLOAT8` (`double precision`) | Gasto médio mensal simples em R$ do perfil. | `AVG(gasto_total_rs)`. |

---

## 3. Tabela: `consumo_estimado`

**Descrição:** Tabela de integração exploratória (27 linhas, uma por UF) gerada pelo script [`CREATE-pofcenso.sql`](./scripts/CREATE-pofcenso.sql), que cruza indicadores municipais do Censo Demográfico 2022 com coeficientes da tabela `dim_coeficiente_consumo`.

| Nome do Campo | Tipo (Supabase) | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| `id` | `INT4` (`integer`, PK) | Identificador sequencial do registro estadual. | Chave primária no Supabase (`1` a `27`). |
| `sigla_uf` | `public.localidade` (ENUM) | Sigla da Unidade da Federação. | `basedosdados.br_ibge_censo_2022.municipio`. |
| `populacao_total_uf` | `INT8` (`bigint`) | População residente total na UF em 2022. | `SUM(populacao)` dos municípios da UF no Censo 2022. |
| `populacao_idosa_total_uf` | `INT8` (`bigint`) | Estimativa de idosos na UF calculada no SQL exploratório. | Soma municipal de `populacao * (indice_envelhecimento / (100 + indice_envelhecimento))`. |
| `proporcao_idosos_2022` | `FLOAT8` (`double precision`) | Proporção estimada na tabela entre `populacao_idosa_total_uf` e `populacao_total_uf`. | `SAFE_DIVIDE(populacao_idosa_total_uf, populacao_total_uf)`. |
| `media_idade_mediana_uf` | `FLOAT8` (`double precision`) | Média aritmética simples da idade mediana dos municípios da UF. | `AVG(idade_mediana)` por UF. |
| `media_indice_envelhecimento_uf` | `FLOAT8` (`double precision`) | Média aritmética simples do índice de envelhecimento municipal da UF. | `AVG(indice_envelhecimento)` por UF. |
| `consumo_estimado_idosos_kwh` | `FLOAT8` (`double precision`) | Estimativa de consumo mensal do grupo 60+ na UF (kWh/mês). | `populacao_idosa_total_uf * MAX(media_consumo_per_capita_kwh)` onde `is_60_mais = TRUE`. |
| `consumo_estimado_nao_idosos_kwh` | `FLOAT8` (`double precision`) | Estimativa de consumo mensal do grupo <60 na UF (kWh/mês). | `(populacao_total_uf - populacao_idosa_total_uf) * MAX(media_consumo_per_capita_kwh)` onde `is_60_mais = FALSE`. |
| `consumo_residencial_total_2022_kwh` | `FLOAT8` (`double precision`) | Soma dos consumos mensais estimados para a UF (kWh/mês). | `consumo_estimado_idosos_kwh + consumo_estimado_nao_idosos_kwh`. |

---

## 4. Tabela: `projecoes_populacao_idade`

**Descrição:** Tabela de projeções demográficas oficiais do IBGE (Revisão 2024), processada pelo script `migraDados.py` em formato longo (*tidy/long*). Contém 639.639 linhas ($33 \text{ localidades} \times 3 \text{ sexos} \times 91 \text{ idades} \times 71 \text{ anos}$). Alimenta a pirâmide etária e a projeção de domicílios e moradores de 2026 a 2070.

| Nome do Campo | Tipo (Supabase) | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| `id` | `INT8` (`bigint`, PK) | Identificador único sequencial da linha. | Chave primária no Supabase. |
| `localidade` | `public.localidade` (ENUM) | Recorte geográfico da projeção. | `'Brasil'`, 5 macrorregiões (`'Norte'`, `'Nordeste'`, `'Centro-Oeste'`, `'Sudeste'`, `'Sul'`) e 27 siglas de UFs. |
| `sexo` | `public.sexo` (ENUM) | Recorte por sexo biológico na projeção do IBGE. | `'Homem'`, `'Mulher'` ou `'Ambos'`. |
| `idade` | `INT4` (`integer`) | Idade simples em anos completos (`0` a `90`). | Valores de `0` a `89` representam idades exatas; `90` agrega o grupo aberto de **90 anos ou mais (90+)**. |
| `ano` | `INT4` (`integer`) | Ano de referência da série demográfica (`2000` a `2070`). | Série contínua anual de 71 anos; a aplicação expõe o horizonte prospectivo de `2026` a `2070`. |
| `populacao` | `INT4` (`integer`) | População residente projetada pelo IBGE para a combinação `(localidade, sexo, idade, ano)`. | Planilha oficial de Projeções da População do IBGE (transformada via *melt* no `migraDados.py`). |

---

## 5. Tabela: `fato_consumo_pof_historica`

**Descrição:** Tabela contendo os microdados harmonizados das edições históricas da POF **2002-2003** (39.458 domicílios) e **2008-2009** (49.268 domicílios), totalizando 88.726 linhas. Criada por [`CREATE-pof-historica.sql`](./scripts/CREATE-pof-historica.sql) e carregada por `python -m etl.historica`. Utilizada exclusivamente para estimar a inclinação histórica da transição dos arranjos domiciliares dentro de cada faixa etária do chefe (Premissa P13).

| Nome do Campo | Tipo (Supabase) | Descrição | Regra de Negócio / Origem |
| --- | --- | --- | --- |
| `ano_pof` | `INT2` (`smallint`, PK) | Ano inicial de referência da edição da POF (`2002` ou `2008`). | Parte da chave primária composta `(ano_pof, id_domicilio)`. |
| `sigla_uf` | `CHAR(2)` (`character(2)`) | Sigla da Unidade da Federação. | Microdados oficiais do IBGE (código UF convertido para sigla). |
| `id_domicilio` | `TEXT` (PK) | Identificador único do domicílio dentro da respectiva edição da POF. | Parte da chave primária composta `(ano_pof, id_domicilio)`. |
| `qtd_moradores` | `INT2` (`smallint`) | Total de moradores do domicílio ($\ge 1$). | Contagem de moradores na respectiva edição da POF. |
| `arranjo_familiar` | `TEXT` | Classificação do arranjo pelo número de moradores. | `'Unipessoal (Mononuclear)'` (1), `'Casal ou Dupla'` (2) ou `'Multipessoal (3+)'` (3+). |
| `idade_chefe` | `INT2` (`smallint`) | Idade da pessoa de referência (maior idade entre chefes de UC do domicílio). | Equivalente à regra da Premissa P8. |
| `is_60_mais` | `BOOL` (`boolean`) | Flag indicando se `idade_chefe >= 60`. | `TRUE` se `idade_chefe >= 60`, senão `FALSE`. |
| `consumo_total_kwh` | `FLOAT8` (`double precision`) | Consumo mensal de energia elétrica do domicílio em kWh. | Quadro 07 item `00202` (POF 2002) e `V9001 = 600201` (POF 2008). |
| `consumo_per_capita_kwh` | `FLOAT8` (`double precision`) | Consumo mensal de energia por pessoa no domicílio (kWh/mês/pessoa). | `consumo_total_kwh / qtd_moradores`. |
| `peso_final` | `FLOAT8` (`double precision`) | Fator de expansão amostral do domicílio. | Variável `fator` (POF 2002) e `PESO_FINAL` (POF 2008). |
| `kwh_imputado` | `BOOL` (`boolean`) | Indica se a quantidade de kWh sofreu imputação pelo IBGE na edição. | Flag de controle de imputação dos microdados originais. |
| `energia_rede_geral` | `BOOL` (`boolean`) | Indica se o domicílio é atendido por energia elétrica de rede geral. | Filtro aplicado no cálculo da tendência (Premissa P13). |

---

## 6. Tabela: `pof2017_domicilio`

**Descrição:** Tabela bruta de microdados de domicílios da POF 2017-2018 (57.920 linhas), extraída do diretório público `basedosdados.br_ibge_pof.domicilio_2017`. Armazena variáveis estruturais de habitação, saneamento, energia e fatores de expansão. Dicionário completo de códigos disponível em [basedosdados.org](https://basedosdados.org/dataset/a1b6d2b6-4aa6-47e7-a517-8a21b28b7254?table=7b880731-ffa2-4bde-a290-ae058b3acf51).

| Nome do Campo | Tipo (Supabase) | Descrição | Origem / Observação |
| --- | --- | --- | --- |
| `sigla_uf` | `TEXT` | Sigla da Unidade da Federação. | Identificação geográfica da amostra. |
| `situacao` | `INT8` (`bigint`) | Situação do domicílio (`1` = Urbano, `2` = Rural). | Classificação censitária do setor. |
| `id_estrato` | `INT8` (`bigint`) | Identificador do estrato geográfico/estatístico do plano amostral. | Desenho amostral da POF 2017-2018. |
| `id_unidade_primaria_amostragem` | `INT8` (`bigint`) | Identificador da Unidade Primária de Amostragem (UPA). | Desenho amostral da POF 2017-2018. |
| `id_domicilio` | `INT8` (`bigint`) | Identificador único do domicílio. | Chave de ligação com `pof2017_morador` e `fato_consumo_domiciliar`. |
| `V0201` | `INT8` (`bigint`) | Tipo do domicílio (casa, apartamento, cômodo/cortiço etc.). | Questionário POF 1 (Características do Domicílio). |
| `V0202` a `V0204` | `INT8` (`bigint`) | Material predominante nas paredes externas (`V0202`), telhado (`V0203`) e piso (`V0204`). | Questionário POF 1. |
| `V0205` a `V0206` | `INT8` (`bigint`) | Total de cômodos do domicílio (`V0205`) e quantidade de cômodos servindo de dormitório (`V0206`). | Questionário POF 1 (potenciais variáveis explicativas de consumo). |
| `V0207` a `V0213` | `INT8` (`bigint`) | Abastecimento de água, canalização, frequência, banheiros e esgotamento sanitário. | Questionário POF 1. |
| `V02141` e `V02142` | `INT8` (`bigint`) | Origem da energia elétrica: rede geral (`V02141`: `1`=Sim, `2`=Não) e outra fonte (`V02142`). | Questionário POF 1. |
| `V0215` a `V02164` | `INT8` (`bigint`) | Frequência da disponibilidade de energia elétrica da rede geral e combustíveis usados no fogão. | Questionário POF 1. |
| `V0217` a `V0221` | `INT8` (`bigint`) | Condição de ocupação do domicílio (próprio, alugado, cedido), pavimentação e serviços postais. | Questionário POF 1. |
| `V6199` | `INT8` (`bigint`) | Segurança alimentar / situação síntese do domicílio na POF. | Variável derivada do IBGE. |
| `peso` | `FLOAT8` (`double precision`) | Peso amostral básico (sem pós-estratificação). | Plano amostral POF 2017-2018. |
| `peso_final` | `FLOAT8` (`double precision`) | Peso amostral calibrado (com pós-estratificação). | Fator de expansão oficial para estimativas populacionais. |

---

## 7. Tabela: `pof2017_morador`

**Descrição:** Tabela bruta de microdados de indivíduos residentes da POF 2017-2018 (178.431 linhas), extraída de `basedosdados.br_ibge_pof.morador_2017`. Contém perfil demográfico, parentesco com a pessoa de referência (`V0306`), escolaridade e variáveis de renda. Dicionário completo de códigos disponível em [basedosdados.org](https://basedosdados.org/dataset/a1b6d2b6-4aa6-47e7-a517-8a21b28b7254?table=7b880731-ffa2-4bde-a290-ae058b3acf51).

| Nome do Campo | Tipo (Supabase) | Descrição | Origem / Observação |
| --- | --- | --- | --- |
| `sigla_uf` | `TEXT` | Sigla da Unidade da Federação. | Identificação geográfica. |
| `situacao` | `INT8` (`bigint`) | Situação do domicílio (`1` = Urbano, `2` = Rural). | Classificação do setor. |
| `id_estrato` | `INT8` (`bigint`) | Identificador do estrato amostral. | Desenho amostral da POF. |
| `id_unidade_primaria_amostragem` | `INT8` (`bigint`) | Identificador da UPA. | Desenho amostral da POF. |
| `id_domicilio` | `INT8` (`bigint`) | Identificador do domicílio. | Chave de junção com `pof2017_domicilio` e `fato_consumo_domiciliar`. |
| `id_unidade_consumo` | `INT8` (`bigint`) | Número da Unidade de Consumo (UC) dentro do domicílio. | Um domicílio pode conter mais de uma UC (tratado pela Premissa P8). |
| `id_informante` | `INT8` (`bigint`) | Identificador do morador dentro do domicílio/UC. | Usado em `COUNT(DISTINCT id_informante)` para calcular `qtd_moradores`. |
| `dia_nascimento`, `mes_nascimento`, `ano_nascimento` | `INT8` (`bigint`) | Data de nascimento declarada pelo morador. | Questionário POF 1 (Bloco de Moradores). |
| `idade` | `INT8` (`bigint`) | Idade calculada em anos completos na data da entrevista. | Origem de `idade_chefe` quando `V0306 = 1`. |
| `sexo` | `INT8` (`bigint`) | Sexo do morador (`1` = Homem, `2` = Mulher). | Questionário POF 1. |
| `raca_cor` | `INT8` (`bigint`) | Cor ou raça declarada (`1`=Branca, `2`=Preta, `3`=Amarela, `4`=Parda, `5`=Indígena, `9`=Sem declaração). | Questionário POF 1. |
| `anos_estudo` | `INT8` (`bigint`) | Total de anos de estudo concluídos. | Variável derivada do IBGE. |
| `nivel_instrucao` | `INT8` (`bigint`) | Nível de instrução mais elevado alcançado (`1` a `7`). | Variável derivada do IBGE. |
| `composicao_familiar` | `INT8` (`bigint`) | Código de classificação tipológica da composição familiar da UC. | Variável derivada da POF. |
| `V0306` | `INT8` (`bigint`) | Condição na Unidade de Consumo (relação de parentesco com a pessoa de referência). | `1` = Pessoa de referência (chefe), `2`/`3` = Cônjuge/companheiro(a), `4`+ = Filhos, outros parentes, agregados etc. |
| `V0401` a `V0430` | `INT8` (`bigint`) / `TEXT` | Variáveis suplementares de condição de presença, alfabetização, frequência escolar, rede de ensino, curso e plano de saúde. | Questionário POF 1 (`V0413` é `TEXT`, demais são `INT8`). |
| `renda_total` | `FLOAT8` (`double precision`) | Renda total mensal da Unidade de Consumo (R$). | Variável derivada do IBGE. |
| `deducao_per_capita` | `FLOAT8` (`double precision`) | Deduções mensais familiares per capita (impostos diretos, previdência etc. em R$). | Variável derivada do IBGE. |
| `renda_nao_monetaria_per_capita` | `FLOAT8` (`double precision`) | Parcela não monetária da renda per capita da UC (R$). | Variável derivada do IBGE. |
| `renda_monetaria_per_capita` | `FLOAT8` (`double precision`) | Parcela monetária da renda per capita da UC (R$). | Variável derivada do IBGE. |
| `renda_disponivel_per_capita` | `FLOAT8` (`double precision`) | Renda disponível familiar per capita mensal (R$). | Variável derivada do IBGE. |
| `peso` | `FLOAT8` (`double precision`) | Peso amostral básico sem pós-estratificação. | Plano amostral POF 2017-2018. |
| `peso_final` | `FLOAT8` (`double precision`) | Peso amostral calibrado (com pós-estratificação). | Origem da coluna `peso_final` em `fato_consumo_domiciliar`. |

---

## 8. Tabela: `censo2022_municipio`

**Descrição:** Tabela com indicadores demográficos consolidados dos **5.570 municípios brasileiros** no Censo Demográfico 2022, extraída de `basedosdados.br_ibge_censo_2022.municipio`. Dicionário de referência disponível em [basedosdados.org](https://basedosdados.org/dataset/08a1546e-251f-4546-9fe0-b1e6ab2b203d?table=cf9537b5-6198-455f-a8b0-7c762e94d79c).

| Nome do Campo | Tipo (Supabase) | Descrição | Origem / Regra de Negócio |
| --- | --- | --- | --- |
| `id_municipio` | `INT8` (`bigint`) | Código IBGE de 7 dígitos do município. | Identificador oficial municipal do IBGE. |
| `sigla_uf` | `TEXT` | Sigla da Unidade da Federação à qual o município pertence. | Agrupador estadual. |
| `domicilios` | `INT8` (`bigint`) | Total de domicílios recenseados no município em 2022 (soma Brasil: 90.688.021 domicílios totais). | Censo Demográfico 2022 (Universo). |
| `populacao` | `INT8` (`bigint`) | População residente total recenseada no município em 2022 (soma Brasil: 203.080.756 habitantes). | Censo Demográfico 2022 (Universo). |
| `area` | `INT8` (`bigint`) | Área territorial do município em $\text{km}^2$. | Malha territorial do IBGE. |
| `taxa_alfabetizacao` | `FLOAT8` (`double precision`) | Taxa de alfabetização da população de 15 anos ou mais. | Censo Demográfico 2022. |
| `idade_mediana` | `FLOAT8` (`double precision`) | Idade que divide a população residente do município em duas partes iguais. | Censo Demográfico 2022. |
| `razao_sexo` | `FLOAT8` (`double precision`) | Número de homens para cada grupo de 100 mulheres no município. | Censo Demográfico 2022. |
| `indice_envelhecimento` | `FLOAT8` (`double precision`) | Número de pessoas de 60 anos ou mais para cada 100 pessoas de 0 a 14 anos no município. | $\text{IE} = \frac{\text{Pop}_{60+}}{\text{Pop}_{0-14}} \times 100$. |
| `populacao_indigena` | `INT8` (`bigint`) | População residente indígena total no município. | Censo Demográfico 2022. |
| `populacao_indigena_terra_indigena` | `INT8` (`bigint`) | População indígena residente em Terras Indígenas no município. | Censo Demográfico 2022. |
| `populacao_quilombola` | `INT8` (`bigint`) | População residente quilombola total no município. | Censo Demográfico 2022. |
| `populacao_quilombola_territorio_quilombola` | `INT8` (`bigint`) | População quilombola residente em Territórios Quilombolas delimitados. | Censo Demográfico 2022. |

---

## 9. Tabela: `censo2022_indice_envelhecimento`

**Descrição:** Tabela histórica comparativa municipal (55.700 linhas = 5.570 municípios $\times$ 2 edições censitárias $\times$ 5 recortes de cor/raça) contendo os indicadores de envelhecimento demográfico dos Censos de **2010** e **2022**. Dicionário de referência disponível em [basedosdados.org](https://basedosdados.org/dataset/08a1546e-251f-4546-9fe0-b1e6ab2b203d?table=cf9537b5-6198-455f-a8b0-7c762e94d79c).

| Nome do Campo | Tipo (Supabase) | Descrição | Origem / Observação |
| --- | --- | --- | --- |
| `ano` | `INT8` (`bigint`) | Ano do Censo Demográfico (`2010` ou `2022`). | Série comparativa intercensitária. |
| `id_municipio` | `INT8` (`bigint`) | Código IBGE de 7 dígitos do município. | Chave de ligação com `censo2022_municipio.id_municipio`. |
| `cor_raca` | `TEXT` | Recorte de cor ou raça (`Branca`, `Preta`, `Amarela`, `Parda`, `Indígena`). | Classificação racial do IBGE. |
| `indice_envelhecimento` | `TEXT` | Razão entre a população de 60+ anos e a população de 0 a 14 anos ($\times 100$) para o recorte racial no município. | Armazenado como texto na importação bruta; requer conversão numérica (`SAFE_CAST`) para agregações. |
| `idade_mediana` | `TEXT` | Idade mediana da população do recorte racial no município. | Armazenado como texto na importação bruta. |
| `razao_sexo` | `TEXT` | Número de homens por 100 mulheres para o recorte racial no município. | Armazenado como texto na importação bruta. |

---

## Notas Metodológicas para o TCC

- **Código de Produto:** A Base dos Dados mapeou o consumo elétrico sob o código `600101` para a POF 2017-2018 (e `00202` no quadro 07 da POF 2002-2003; `600201` na POF 2008-2009).
- **Tratamento de Nulos e Critério de Exclusão:** Na extração da `fato_consumo_domiciliar`, domicílios sem registro válido de kWh (`V9005`) não foram imputados com zeros artificiais e foram filtrados segundo o critério de exclusão da metodologia (cobertura de 92,4% dos domicílios ponderados do país — Premissa P9).
- **Desduplicação de Unidades de Consumo (Premissa P8):** Na `fato_consumo_domiciliar`, os 99 domicílios com mais de uma Unidade de Consumo (204 linhas) são desduplicados no pipeline mantendo-se a pessoa de referência de maior idade, resultando em **52.102 domicílios únicos**.
- **Integração e Projeção:** O motor analítico principal (`backend/app/calculo.py` e `backend/etl/modelagem.py`) combina as taxas ponderadas de consumo e de chefia da `fato_consumo_domiciliar` (POF 2017-2018), a tendência histórica de arranjos da `fato_consumo_pof_historica` (POFs 2002, 2008 e 2017) e a população oficial da `projecoes_populacao_idade` (IBGE 2024).