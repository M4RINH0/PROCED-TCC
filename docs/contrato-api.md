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

## `GET /projecoes` (RF01, RF11)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2070 |
| `recorte` | `chefe_60_mais` ou `mononuclear_abaixo_60` |

Exemplo real (Brasil, consulta de 14/10/2026):

```json
{ "ano": 2050, "recorte": "chefe_60_mais", "unidade": "kWh/mes/pessoa",
  "cenarios": [
    {"id": "taxas", "valor": 98.0, "consumo_por_pessoa_kwh": 93.0,
     "consumo_total_calibrado_kwh_mes": 3527888853},
    {"id": "ml_rf", "valor": null, "consumo_por_pessoa_kwh": null, "consumo_total_calibrado_kwh_mes": null},
    {"id": "ml_gb", "valor": null, "consumo_por_pessoa_kwh": null, "consumo_total_calibrado_kwh_mes": null},
    {"id": "contrafactual", "valor": 97.9, "consumo_por_pessoa_kwh": 93.0,
     "consumo_total_calibrado_kwh_mes": 2327910204} ],
  "efeito_envelhecimento_kwh": 0.1,
  "efeito_envelhecimento_total_kwh_mes": 1199978649,
  "dados_ilustrativos": false,
  "fonte": "POF 2017 a 2018 e Projeções da População (IBGE)",
  "localidade": "Brasil", "domicilios_amostra": 9120,
  "celulas": [ {"faixa": "60 a 69", "arranjo": "Unipessoal (Mononuclear)",
                "domicilios_amostra": 1605, "baixa_confiabilidade": false} ],
  "baixa_confiabilidade": false }
```

- `taxas`: método das taxas, padronização direta com a TEC ponderada da POF e as taxas de chefia de 2018 (premissas P2 e P6).
- `contrafactual`: o mesmo cálculo com a distribuição dos domicílios entre as células congelada na de 2026; o total de domicílios segue a projeção (P10).
- `ml_rf` e `ml_gb`: machine learning, pausado; sempre `null`.
- `valor`: TBC padronizada, a média por domicílio do consumo per capita (kWh/mês por pessoa).
- `consumo_por_pessoa_kwh`: consumo total do recorte dividido pelos moradores projetados (P11).
- `consumo_total_calibrado_kwh_mes`: consumo total do recorte calibrado pela população do IBGE (P12). O consumo total bruto não sai na API.
- `efeito_envelhecimento_kwh` e `efeito_envelhecimento_total_kwh_mes`: `taxas` menos `contrafactual`.
- Um cenário fica `null` se alguma faixa do recorte não tiver domicílio na amostra da localidade.
- O IBGE projeta só a população; nenhum cenário é uma projeção oficial de consumo.

## `GET /projecoes/serie` (RF01, RF11)

Parâmetro `recorte`. Resposta com `pontos`: um item por ano de 2026 a 2070, cada um
com os quatro cenários e, para a tela do Panorama:

- em cada cenário, `variacao_kwh` e `variacao_pct` do `valor` em relação a 2026;
- `participacao_60_mais_pct`: pessoas de 60 anos ou mais na população;
- `efeito_envelhecimento_kwh` e `efeito_envelhecimento_total_kwh_mes`.

A resposta também traz `domicilios_amostra`, `celulas` e `baixa_confiabilidade`.

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
premissa P2 por faixa e arranjo, com a mesma projeção do Panorama.

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

## `GET /simulador` (RF07)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2070 |
| `faixa` | `ate_29`, `30_39`, `40_49`, `50_59`, `60_69`, `70_79`, `80_mais` |
| `arranjo` | `unipessoal`, `casal_ou_dupla`, `multipessoal` |
| `base` | `taxas` ou `contrafactual` |

O parâmetro `taxa` saiu até o RF02 ser definido.

Resposta:
- `valor`: TEC ponderada da célula (kWh/mês por pessoa), igual nos dois cenários (P6);
- `domicilios_projetados`, `participacao_pct` e `consumo_total_calibrado_kwh_mes`: a célula no ano e no cenário escolhidos;
- `domicilios_amostra` e `baixa_confiabilidade`;
- `motivo_sem_valor`, quando falta amostra ou projeção da população;
- `por_faixa`, para o histograma.

A persistência de cenários (RF09) ainda não existe.

## `GET /fontes` (RF10)

`fontes` (com `nome`, `periodo` e `uso`), `criterio_exclusao` (domicílios sem kWh),
`cobertura_pct` (soma dos pesos da base sobre os 68,9 milhões de domicílios da POF,
P9), `premissas` (P2, P8, P9, P11 e P12, com `id` e `texto`) e `premissas_url`.

## A definir em conjunto

- Exportação (RF08) e persistência de cenários do simulador (RF09).
- RF02: parâmetro ajustável do cenário, ainda sem formulação.
- Cenários de machine learning (`ml_rf` e `ml_gb`): pausados.
