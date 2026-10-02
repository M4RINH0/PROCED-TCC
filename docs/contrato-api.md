# Contrato da API

A documentação interativa é gerada pelo código (RNF09): rode a API e abra
`http://localhost:8000/docs`.

## Implementado

### `GET /projecoes` (RF01, RF11)

| Parâmetro | Tipo | Regra |
|---|---|---|
| `ano` | inteiro | 2026 a 2075 |
| `recorte` | enumeração | `chefe_60_mais` ou `mononuclear_abaixo_60` |

Resposta:

```json
{ "ano": 2075, "recorte": "chefe_60_mais", "unidade": "kWh/mes/pessoa",
  "cenarios": [ {"id":"mod","valor":230.3}, {"id":"ibge","valor":null},
                {"id":"alt","valor":262.3} ],
  "dados_ilustrativos": true }
```

- `ibge` é `null` depois de 2060.
- Parâmetro ausente ou fora do domínio: 422.
- Os valores vêm do repositório ilustrativo (as mesmas funções sintéticas do
  protótipo) até a projeção real ser calculada; por isso `dados_ilustrativos: true`.

## A definir em conjunto

Arranjos, pirâmide, consulta do simulador, fontes e exportação.

Lacunas do endpoint atual:

- RF02 (ajustar a taxa de envelhecimento) não tem parâmetro no contrato.
- O gráfico do Panorama precisa da série de 2026 a 2075; com o contrato atual seriam
  50 requisições. Sugestão a discutir: `GET /projecoes/serie?recorte=&taxa=`.
