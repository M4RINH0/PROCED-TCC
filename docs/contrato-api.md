# Contrato da API

A documentação interativa é gerada pelo código (RNF09): rode a API e abra
`http://localhost:8000/docs`. Todos os endpoints são `GET`, validam os parâmetros
(422 quando inválidos) e respondem 503 quando o banco não responde.

## `GET /projecoes` (RF01, RF11)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2075 |
| `recorte` | `chefe_60_mais` ou `mononuclear_abaixo_60` |

```json
{ "ano": 2050, "recorte": "chefe_60_mais", "unidade": "kWh/mes/pessoa",
  "cenarios": [ {"id":"mod","valor":null}, {"id":"ibge","valor":94.4},
                {"id":"alt","valor":null} ],
  "dados_ilustrativos": false,
  "fonte": "POF 2017 a 2018 e Projeções da População (IBGE)" }
```

- `ibge`: TBC padronizada (premissas P2 e P6); `null` depois de 2070.
- `mod` e `alt`: `null` até a formulação ser definida.

## `GET /projecoes/serie` (RF01, RF11)

Parâmetro `recorte`. Resposta com `pontos`: um item por ano de 2026 a 2075, cada um
com os três cenários e, para a tela do Panorama:

- em cada cenário, `variacao_kwh` e `variacao_pct` em relação a 2026;
- `participacao_60_mais_pct`: pessoas de 60 anos ou mais na população (até 2070);
- `amplitude_kwh` e `modelo_menos_oficial_kwh`: `null` enquanto só o oficial tem valor.

## `GET /arranjos` (RF03, RF04)

Parâmetro opcional `grupo`: `todos` (padrão), `chefe_60_mais`, `abaixo_60`.

```json
{ "grupo": "todos", "unidade": "kWh/mes/pessoa", "fonte": "...",
  "arranjos": [ { "arranjo": "Casal ou Dupla", "mononuclear": true, "chefe_60_mais": true,
                  "domicilios_amostra": 5705, "consumo_per_capita_kwh": 81.4,
                  "consumo_total_kwh": 162.8, "gasto_rs": 114.03 } ] }
```

## `GET /arranjos/composicao` (RF03, RF04)

Seis categorias (unipessoal, casal ou dupla e multipessoal, com chefe de 60+ ou
abaixo de 60). Para cada uma: TEC da POF, amostra e, por ano de 2026 a 2070,
`participacao_pct` e `casas` (de cada 100 domicílios; a soma do ano é 100). Usa a
premissa P2 por faixa e arranjo.

## `GET /estrutura-etaria/piramides` (RF05)

Todas as pirâmides de 2026 a 2070 numa resposta, para a linha do tempo.

## `GET /estrutura-etaria/piramide` (RF05)

Parâmetro `ano`: 2026 a 2070. Faixas de 10 anos (80+ agrega o resto), em % da
população total do Brasil, mais `participacao_60_mais_pct`.

## `GET /estrutura-etaria/consumo-chefe` (RF05, RF06)

Parâmetro opcional `arranjo`: `mononucleares` (padrão), `unipessoal`,
`casal_ou_dupla`, `multipessoal`, `todos`. Uma linha por faixa do chefe com
`domicilios_amostra` e `consumo_per_capita_kwh` (TEC; `null` sem amostra).

## `GET /simulador` (RF07)

| Parâmetro | Regra |
|---|---|
| `ano` | 2026 a 2075 |
| `faixa` | `ate_29`, `30_39`, `40_49`, `50_59`, `60_69`, `70_79`, `80_mais` |
| `arranjo` | `unipessoal`, `casal_ou_dupla`, `multipessoal` |
| `base` | `ibge`, `mod`, `alt` |
| `taxa` | opcional, 0 a 10; reservada para o cenário do modelo |

Resposta com `valor` (TEC da combinação no cenário oficial), `motivo_sem_valor`
quando não há valor (cenário não modelado, ano depois de 2070 ou sem amostra) e
`por_faixa` para o histograma. A persistência de cenários (RF09) ainda não existe.

## `GET /fontes` (RF10)

Lista de fontes com `nome`, `periodo` e `uso`.

## A definir em conjunto

- Exportação (RF08) e persistência de cenários do simulador (RF09).
- RF02: parâmetro de taxa de envelhecimento, que depende da formulação do cenário do modelo.
