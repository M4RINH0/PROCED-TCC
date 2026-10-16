# Contrato da API

A documentação interativa é gerada pelo código (RNF09): rode a API e abra
`http://localhost:8000/docs`. Todos os endpoints são `GET`, validam os parâmetros
(422 quando inválidos) e respondem 503 quando o banco não responde.

## Filtro de localidade (todos os endpoints de dados)

Todos os endpoints de dados abaixo, menos `/fontes` e `/localidades`, aceitam o parâmetro
opcional `localidade`: `Brasil` (padrão), uma região (`Norte`, `Nordeste`,
`Centro-Oeste`, `Sudeste`, `Sul`) ou a sigla de uma UF (`DF`, `SP`...). O cálculo usa
só os domicílios da POF da localidade e a projeção populacional do IBGE da mesma
localidade. Toda resposta devolve o campo `localidade`.

## `GET /localidades`

Regiões e os estados de cada uma, para montar os filtros:
`{ "padrao": "Brasil", "regioes": [ { "nome": "Norte", "estados": [ {"sigla": "AC", "nome": "Acre"} ] } ] }`.

## Amostra e baixa confiabilidade (todas as respostas por localidade)

Toda resposta que usa os domicílios da POF informa o tamanho da amostra e marca
`baixa_confiabilidade: true` quando a célula (faixa do chefe e arranjo) tem menos de
30 domicílios. Em `/projecoes` e `/projecoes/serie`, a lista `celulas` traz cada
célula do recorte, e o campo `baixa_confiabilidade` da resposta fica verdadeiro se
alguma delas tiver menos de 30.

## Controles de simulação (RF02): `/projecoes`, `/projecoes/serie`, `/arranjos/composicao`, `/estrutura-etaria/piramide(s)` e `/simulador`

| Parâmetro | Regra | Padrão |
|---|---|---|
| `intensidade` | 0 a 1,5: multiplica a variação dos logs das razões entre os arranjos depois de 2026 (P13); 0 congela os arranjos a partir de 2026 | 0,6 (calibrada pela validação fora do tempo) |
| `k` | 0,5 a 1,5: velocidade do envelhecimento (P14) | 1 (projeção do IBGE) |

De 2017,5 a 2026 vale sempre a intensidade padrão, então todos os valores de 2026 são iguais em qualquer simulação. A pirâmide aceita só `k`: a intensidade não muda a população. O consumo por faixa do chefe (`/estrutura-etaria/consumo-chefe`) e o consumo por arranjo (`/arranjos`) não dependem de nenhum dos dois. Fora do intervalo, a API responde 422. Toda resposta devolve `intensidade`, `k` e
`simulacao`, que fica `true` quando algum controle está fora do padrão: a interface
rotula o resultado como simulação. Os padrões reproduzem o cenário principal.

## `GET /projecoes` (RF01, RF02, RF11)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2070 |
| `recorte` | `todos_domicilios`, `chefe_60_mais_todos`, `chefe_60_mais` ou `mononuclear_abaixo_60` |
| `intensidade`, `k` | controles de simulação (opcionais) |

Recortes:
- `todos_domicilios`: todos os arranjos e faixas; o único em que o efeito da idade aparece.
- `chefe_60_mais_todos`: chefe de 60 anos ou mais, todos os arranjos; mostra principalmente o efeito dos arranjos.
- `chefe_60_mais` e `mononuclear_abaixo_60`: só mononucleares; escondem os dois efeitos, porque já são definidos pela idade e pelo arranjo.

Exemplo real (Brasil, todos os domicílios, consulta de 14/10/2026):

```json
{ "ano": 2050, "recorte": "todos_domicilios", "unidade": "kWh/mes/pessoa",
  "cenarios": [
    {"id": "taxas", "valor": 81.3, "consumo_por_pessoa_kwh": 70.1, "consumo_total_calibrado_kwh_mes": 15300389004},
    {"id": "taxas_arranjos_fixos", "valor": 75.8, "consumo_por_pessoa_kwh": 64.0, "consumo_total_calibrado_kwh_mes": 13965888940},
    {"id": "contrafactual", "valor": 72.4, "consumo_por_pessoa_kwh": 61.3, "consumo_total_calibrado_kwh_mes": 13386430798} ],
  "efeito_envelhecimento_kwh": 8.9, "efeito_idade_kwh": 3.4, "efeito_arranjos_kwh": 5.5,
  "efeito_envelhecimento_total_kwh_mes": 1913958206,
  "efeito_idade_total_kwh_mes": 579458142, "efeito_arranjos_total_kwh_mes": 1334500064,
  "intensidade": 1.0, "k": 1.0, "simulacao": false,
  "dados_ilustrativos": false,
  "fonte": "POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)",
  "localidade": "Brasil", "domicilios_amostra": 52102,
  "celulas": [ {"faixa": "até 29", "arranjo": "Unipessoal (Mononuclear)",
                "domicilios_amostra": 503, "baixa_confiabilidade": false} ],
  "baixa_confiabilidade": false }
```

- `taxas`: método das taxas com a taxa de chefia total da faixa constante (P2) e a tendência dos arranjos (P13).
- `taxas_arranjos_fixos`: só o envelhecimento, com as proporções de arranjo congeladas nas de 2026.
- `contrafactual`: a distribuição dos domicílios entre as células congelada na de `taxas` em 2026; o total de domicílios segue a projeção (P10).
- Os cenários de machine learning (`ml_rf` e `ml_gb`) saíram da API em 16/10/2026: o machine learning ficou fora do escopo das projeções (baixo poder explicativo, ausência de série temporal e equivalência com o método das taxas sob reponderação). O experimento continua em `backend/etl/modelagem.py`, fora do pipeline padrão.
- Os três cenários do método das taxas coincidem em 2026.
- `valor`: TBC padronizada, a média por domicílio do consumo per capita (kWh/mês por pessoa).
- `consumo_por_pessoa_kwh`: consumo total do recorte dividido pelos moradores projetados (P11).
- `consumo_total_calibrado_kwh_mes`: consumo total do recorte calibrado pela população do IBGE (P12). O consumo total bruto não sai na API.
- `participacao_consumo_pct`: participação do recorte no consumo residencial de todos os domicílios da localidade, em %. Como o fator de calibração é único, é a mesma com o consumo bruto ou o calibrado. Em `todos_domicilios` é sempre 100.
- Decomposição, na TBC (`_kwh`), no consumo total (`_total_kwh_mes`) e na participação (`_participacao_pp`):
  - `efeito_idade`: `taxas_arranjos_fixos` menos `contrafactual`;
  - `efeito_arranjos`: `taxas` menos `taxas_arranjos_fixos`;
  - `efeito_envelhecimento`: a soma dos dois, `taxas` menos `contrafactual`.
- A decomposição também sai na participação, em pontos percentuais (`_participacao_pp`).
- Um cenário fica `null` se alguma faixa do recorte não tiver domicílio na amostra da localidade.
- O IBGE projeta só a população; nenhum cenário é uma projeção oficial de consumo.

## `GET /projecoes/serie` (RF01, RF02, RF11)

Parâmetros `recorte`, `intensidade` e `k`. Resposta com `pontos`: um item por ano de
2026 a 2070, cada um com os cinco cenários e, para a tela do Panorama:

- em cada cenário, `variacao_kwh` e `variacao_pct` do `valor` em relação a 2026;
- `participacao_60_mais_pct`: pessoas de 60 anos ou mais na população, já com o controle `k`;
- os seis campos da decomposição.

A resposta também traz `domicilios_amostra`, `celulas`, `baixa_confiabilidade`,
`intensidade`, `k` e `simulacao`.

## `GET /arranjos` (RF03, RF04)

Parâmetro opcional `grupo`: `todos` (padrão), `chefe_60_mais`, `abaixo_60`. Médias
ponderadas pelo peso amostral sobre a tabela fato (sem as linhas repetidas, P8).

```json
{ "grupo": "chefe_60_mais", "unidade": "kWh/mes/pessoa", "fonte": "...",
  "arranjos": [ { "arranjo": "Casal ou Dupla", "mononuclear": true, "chefe_60_mais": true,
                  "domicilios_amostra": 5705, "baixa_confiabilidade": false,
                  "consumo_per_capita_kwh": 85.2, "consumo_total_kwh": 170.3, "gasto_rs": 121.31 } ] }
```

## `GET /arranjos/composicao` (RF03, RF04)

Seis categorias (unipessoal, casal ou dupla e multipessoal, com chefe de 60+ ou
abaixo de 60). Para cada uma: TEC ponderada da POF, amostra, `baixa_confiabilidade`
(alguma célula da categoria com menos de 30 domicílios) e, por ano de 2026 a 2070,
`participacao_pct` e `casas` (de cada 100 domicílios; a soma do ano é 100). Usa a
mesma projeção do cenário `taxas` do Panorama, com os padrões dos controles (P2 e P13).

## `GET /estrutura-etaria/piramides` (RF05)

Todas as pirâmides de 2026 a 2070 numa resposta, para a linha do tempo.

## `GET /estrutura-etaria/piramide` (RF05)

Parâmetro `ano`: 2026 a 2070. Faixas de 10 anos (80+ agrega o resto), em % da
população total do Brasil, mais `participacao_60_mais_pct`.

## `GET /estrutura-etaria/consumo-chefe` (RF05, RF06)

Parâmetro opcional `arranjo`: `mononucleares` (padrão), `unipessoal`,
`casal_ou_dupla`, `multipessoal`, `todos`. Uma linha por faixa do chefe com
`domicilios_amostra`, `baixa_confiabilidade` e `consumo_per_capita_kwh` (TEC ponderada;
`null` sem amostra).

## `GET /simulador` (RF02, RF07, RF09)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2070 |
| `faixa` | `ate_29`, `30_39`, `40_49`, `50_59`, `60_69`, `70_79`, `80_mais` |
| `arranjo` | `unipessoal`, `casal_ou_dupla`, `multipessoal` |
| `base` | `taxas`, `taxas_arranjos_fixos` ou `contrafactual` |
| `intensidade`, `k` | controles de simulação (opcionais) |
| `recalcular` | booleano opcional (padrão `false`); força novo cálculo e atualiza o cenário salvo |

O antigo parâmetro `taxa` saiu; o RF02 é atendido por `intensidade` e `k`.

Resposta:
- `valor`: TEC ponderada da célula (kWh/mês por pessoa), igual nos três cenários (P6);
- `domicilios_projetados`, `participacao_pct` e `consumo_total_calibrado_kwh_mes`: a célula no ano e no cenário escolhidos;
- `domicilios_amostra` e `baixa_confiabilidade`;
- `motivo_sem_valor`, quando falta amostra ou projeção da população;
- `por_faixa`, para o histograma;
- `recuperado`: `false` quando o cenário foi calculado na consulta e salvo; `true` quando foi recuperado de cenário já calculado (RF09).

Os cenários ficam na tabela `cenario_salvo`, identificados pelos parâmetros da consulta e pela versão do modelo (`VERSAO_MODELO`). Cenário de versão antiga não volta como `recuperado`: é recalculado e gravado com a versão nova. Se o banco falhar ao ler ou gravar, a consulta é calculada e respondida mesmo assim.

## `GET /fontes` (RF10)

`fontes` (com `nome`, `periodo` e `uso`), `criterio_exclusao` (domicílios sem kWh),
`cobertura_pct` (soma dos pesos da base sobre os 68,9 milhões de domicílios da POF,
P9), `premissas` (P2, P8, P9, P11 e P12, com `id` e `texto`) e `premissas_url`.

## `GET /exportar` (RF08)

| Parâmetro | Regra |
|---|---|
| `formato` | `csv` (padrão) ou `xlsx` |
| `escopo` | `ano` (padrão) ou `serie` (2026 a 2070) |
| `ano` | 2026 a 2070 (padrão 2070; usado quando `escopo=ano`) |
| `recorte` | opcional; sem ele, exporta os quatro recortes |
| `localidade`, `intensidade`, `k` | filtro de localidade e controles de simulação (opcionais) |

Devolve o arquivo para download (`Content-Disposition: attachment`) com uma linha por cenário, contendo os indicadores, a decomposição dos efeitos, os controles de simulação, a amostra, a coluna `fonte`, a versão do modelo (`versao_modelo`) e a data e hora da geração (`gerado_em`, ISO 8601 com fuso), nos dois formatos. O CSV sai em UTF-8 com BOM, para o Excel em português reconhecer os acentos; para planilha, o XLSX é o recomendado. Os valores lógicos (`simulacao` e `baixa_confiabilidade`) saem como `true` e `false`, em minúsculas, nos dois formatos; no XLSX ficam como texto, para o Excel em português não trocá-los por VERDADEIRO e FALSO.

## A definir em conjunto

