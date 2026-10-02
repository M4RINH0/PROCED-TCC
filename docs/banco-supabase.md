# Banco no Supabase: estado encontrado em 02/10/2026

Levantamento feito só com leitura (API REST com a chave secreta, no back-end).
Nada foi criado nem alterado.

## Segurança

- RLS ativo: com a chave publicável (anônima), as quatro tabelas devolvem lista vazia.
- Existe a função `rls_auto_enable` exposta em `/rpc`.

## Tabelas

| Tabela | Linhas | Conteúdo |
|---|---|---|
| `fato_consumo_domiciliar` | 52.208 | Um domicílio por linha (POF): UF, moradores, arranjo, idade do chefe, `is_60_mais`, consumo total em kWh, gasto em R$, consumo per capita em kWh |
| `dim_coeficiente_consumo` | 162 | Médias por UF, arranjo e `is_60_mais`: tamanho da amostra, consumo total, consumo per capita e gasto |
| `consumo_estimado` | 27 | Por UF, Censo 2022: população total e idosa, proporção de idosos, idade mediana, índice de envelhecimento, consumo estimado de idosos e não idosos |
| `projecoes_populacao_idade` | 639.639 | Projeção populacional por localidade, sexo (`Homem`, `Mulher`, `Ambos`), idade (0 a 90) e ano (**2000 a 2070**) |

Enumerações: `arranjo_familiar` = `Unipessoal (Mononuclear)`, `Casal ou Dupla`,
`Multipessoal (3+)`; `localidade` = Brasil, as 5 regiões e as 27 UFs.

## Regras conferidas nos dados

Nenhuma das 52.208 linhas de `fato_consumo_domiciliar` viola:

- arranjo pelo número de moradores: 1 é unipessoal, 2 é casal ou dupla, 3 ou mais é multipessoal;
- `is_60_mais` verdadeiro se e somente se `idade_chefe` for 60 ou mais;
- `consumo_per_capita_kwh = consumo_total_kwh / qtd_moradores` (conferido em amostra).

Essas regras estão em `backend/etl/derivacao.py`.

## Decisões tomadas a partir deste levantamento (02/10/2026)

1. **Horizonte:** o estudo vai de 2026 a 2070, o mesmo fim da projeção do IBGE no banco.
2. **Arranjos:** seguir os 3 do banco. Mononuclear = unipessoal ou casal ou dupla;
   casal de idosos = dois moradores com chefe de 60 anos ou mais (premissa P1).
   Há 5.705 domicílios assim na amostra.

## Pendências

- **Unidade da POF:** o banco tem kWh e R$; falta documentar como o kWh foi obtido.
- **Origem da carga:** o código que gerou as tabelas não está no repositório (RNF08).
- **Pesos amostrais:** a tabela não traz o peso da POF (premissa P3).
- **Protótipo:** `prototipo/proced.html` ainda mostra 7 arranjos e a fronteira de 2060;
  é só referência visual.
