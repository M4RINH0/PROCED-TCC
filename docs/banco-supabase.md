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

Essas regras estão em `etl/modules/derivacao/regras.py`.

## Divergências com as regras do projeto e o protótipo

1. **Horizonte da projeção oficial.** As regras do projeto dizem que a projeção do IBGE termina
   em 2060, mas a tabela vai até 2070 (a revisão de 2024 das Projeções da População
   do IBGE chega a 2070). A API ainda corta em 2060.
2. **Arranjos.** O banco tem 3 categorias; o protótipo mostra 7 (unipessoal 60+,
   casal de idosos, casal sem filhos, monoparental etc.).
3. **"Mononuclear".** No banco só o unipessoal leva esse rótulo; nas regras do projeto o
   recorte mononuclear inclui o casal de idosos.
4. **Unidade da POF** (decisão em aberto 2). O banco já tem consumo em kWh e gasto
   em R$ lado a lado. Falta documentar como o kWh foi obtido.
5. **Origem da carga.** O código que gerou essas tabelas não está neste repositório
   (RNF08 exige ETL reproduzível a partir dos dados brutos).
