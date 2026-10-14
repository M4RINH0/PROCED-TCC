# Banco no Supabase: estado encontrado em 02/10/2026

Levantamento feito só com leitura (API REST com a chave secreta, no back-end).
Nada foi criado nem alterado.

## Segurança

- RLS ativo: com a chave publicável (anônima), as quatro tabelas devolvem lista vazia.
- Existe a função `rls_auto_enable` exposta em `/rpc`.

## Tabelas

| Tabela | Linhas | Conteúdo |
|---|---|---|
| `fato_consumo_domiciliar` | 52.207 | Um domicílio por linha (POF): UF, moradores, arranjo, idade do chefe, `is_60_mais`, consumo total em kWh, gasto em R$, consumo per capita em kWh |
| `dim_coeficiente_consumo` | 162 | Médias por UF, arranjo e `is_60_mais`: tamanho da amostra, consumo total, consumo per capita e gasto |
| `consumo_estimado` | 27 | Por UF, Censo 2022: população total e idosa, proporção de idosos, idade mediana, índice de envelhecimento, consumo estimado de idosos e não idosos |
| `projecoes_populacao_idade` | 639.639 | Projeção populacional por localidade, sexo (`Homem`, `Mulher`, `Ambos`), idade (0 a 90) e ano (**2000 a 2070**) |

Enumerações: `arranjo_familiar` = `Unipessoal (Mononuclear)`, `Casal ou Dupla`,
`Multipessoal (3+)`; `localidade` = Brasil, as 5 regiões e as 27 UFs.

## Regras conferidas nos dados

Nenhuma das 52.207 linhas de `fato_consumo_domiciliar` viola:

- arranjo pelo número de moradores: 1 é unipessoal, 2 é casal ou dupla, 3 ou mais é multipessoal;
- `is_60_mais` verdadeiro se e somente se `idade_chefe` for 60 ou mais;
- `consumo_per_capita_kwh = consumo_total_kwh / qtd_moradores` (conferido em amostra).

Essas regras estão em `backend/etl/derivacao.py`.

## Decisões tomadas a partir deste levantamento (02/10/2026)

1. **Horizonte:** o estudo vai de 2026 a 2070, o mesmo fim da projeção do IBGE no banco.
2. **Arranjos:** seguir os 3 do banco. Mononuclear = unipessoal ou casal ou dupla;
   casal de idosos = dois moradores com chefe de 60 anos ou mais (premissa P1).
   Há 5.705 domicílios assim na amostra.

## Pendências Resolvidas

### 1. Unidade da POF: Obtenção do kWh
A variável de consumo em kWh foi obtida diretamente dos microdados da POF 2017-2018, especificamente da tabela de Despesa Coletiva.
- **Fonte Original:** Tabela `basedosdados.br_ibge_pof.despesa_coletiva_2017`.
- **Variável de Consumo:** Coluna `V9005`. Esta variável armazena a "Quantidade final consumida em kWh", mas sua coleta pelo IBGE ocorre apenas para o item de Energia Elétrica.
- **Filtro de Item:** O dado de kWh só é válido e populado quando o código do item (`V9001`) corresponde a `600101` (conforme identificado no dicionário de produtos da POF).
- **Metodologia de Extração:** A ETL realiza um `SAFE_CAST(V9005 AS FLOAT64)` para tratar os dados. Nos casos onde o domicílio reportou o gasto financeiro (`V8000_deflacionado`), mas o campo `V9005` estava nulo, a coluna de kWh foi mantida em branco para garantir a integridade dos dados reais, evitando imputações arbitrárias na camada de microdados.

### 2. Origem da Carga (RNF08)
Para atender ao requisito RNF08, o código SQL utilizado para gerar a tabela fato (`fato_consumo_domiciliar`) foi versionado no repositório através do script `CREATE-pof.sql` (localizado na pasta `scripts/`).

### 3. Pesos Amostrais (Premissa P3)
Para cumprir a Premissa P3, a tabela `fato_consumo_domiciliar` foi atualizada para incluir o peso do plano amostral da POF.
- **Variável Utilizada:** `peso_final` da tabela `morador_2017`.
- **Importância:** Este peso é fundamental para que as médias de consumo calculadas (kWh por tipo de arranjo) não sejam apenas aritméticas, mas representativas da população brasileira.
- **Aplicação:** Ao realizar a projeção para 2075, as análises de "Consumo Médio" devem utilizar o peso para corrigir o viés da amostra, garantindo que o impacto do envelhecimento seja expandido corretamente para o universo total de domicílios do Brasil.

## Pendências Restantes

- **Protótipo:** `prototipo/proced.html` ainda mostra 7 arranjos e a fronteira de 2060;
  é só referência visual.
