# Decisões técnicas

## Ferramentas de apoio adotadas (entram no Quadro de tecnologias do TCC)

| Ferramenta | Uso |
|---|---|
| Vite | build e servidor de desenvolvimento do React |
| Vitest, React Testing Library, jsdom | testes do front-end (o jsdom é o ambiente de DOM que o Vitest exige) |
| httpx | cliente HTTP da API para ler o Supabase; também usado pelo `TestClient` |
| pytest, `TestClient` do FastAPI | testes do back-end |
| uvicorn | servidor da API |

Não adotado: D3. Os gráficos são componentes SVG próprios, sem biblioteca.

## Rotas do front-end

Roteamento por hash (`#pan`, `#dom`, `#eta`, `#sim`), feito em `frontend/src/rotas.js` e `frontend/src/hooks/useRotaHash.js`,
sem biblioteca de rotas, para não adicionar dependência.

## Leitura do banco

A API lê o Supabase pela REST (PostgREST) com a chave secreta, só no back-end
(`backend/app/supabase.py` e `backend/app/dados.py`). O Supabase devolve no máximo mil linhas por consulta e
não permite agregação, então cada tabela é lida uma vez, paginada, e mantida em
memória. Ao subir, a API faz essa leitura em segundo plano (cerca de 10 segundos).

## Organização das pastas (02/10/2026)

A estrutura por módulos autocontidos (`api/app/modules/...`, `web/src/modules/...`) foi
trocada por camadas com um arquivo por página: `pages/` no front-end e `routes/`,
`services/` e `schemas/` no back-end. O ETL passou para dentro de `backend/`, e as
pastas sem uso (`db/`, etapas vazias do ETL, módulo de exportação, conexão direta
com o Postgres e `psycopg`) foram removidas. Os endereços da API não mudaram.

## Design do front-end

O CSS do `prototipo/proced.html` foi copiado inteiro para `frontend/src/estilos.css`,
e as telas usam as mesmas classes e estrutura. Diferenças em relação ao protótipo,
porque o dado real é outro:

- Domicílios: 6 categorias (3 arranjos do banco, com chefe 60+ ou abaixo) em vez de 7;
  o mini histórico de cada linha mostra a participação no tempo, porque a TEC da POF
  não muda com o ano.
- Estrutura etária: o consumo por faixa do chefe é um gráfico de barras, não de linhas,
  pelo mesmo motivo.
- Simulador: o histograma mostra as faixas do chefe do arranjo escolhido.
- Horizonte de 2026 a 2070, sem a área hachurada depois da projeção oficial; o selo do topo diz "Cenário do modelo pendente".
- Controle da taxa de envelhecimento desativado até o cenário do modelo existir.
- Exportar avisa que o RF08 está pendente.

## Desempenho da API (RNF02)

**Meta proposta:** menos de 1 segundo por resposta depois da primeira carga de cada
localidade, com os parâmetros padrão e com valores de simulação.

**Medição de 14/10/2026** (API local, `uvicorn` sem `--reload`, banco no Supabase; mediana
de 5 chamadas depois da primeira; intensidade 1,2 e k 1,3 na simulação):

| Endpoint | Localidade | Primeira carga | Depois, padrão | Depois, simulação |
|---|---|---|---|---|
| `/projecoes/serie` (todos os domicílios) | Brasil | 4,44 s | 0,28 s | 0,25 s |
| | Nordeste | 7,31 s | 0,22 s | 0,20 s |
| | SP | 1,00 s | 0,18 s | 0,17 s |
| `/arranjos/composicao` | Brasil | 0,29 s | 0,24 s | 0,22 s |
| | Nordeste | 0,23 s | 0,16 s | 0,19 s |
| | SP | 0,12 s | 0,17 s | 0,14 s |
| `/estrutura-etaria/piramides` | Brasil | 0,01 s | 0,00 s | 0,00 s |
| | Nordeste | 1,58 s | 0,00 s | 0,00 s |
| | SP | 1,63 s | 0,00 s | 0,00 s |

A meta já é cumprida depois da primeira carga. Na data da medição, a composição e a
pirâmide ainda não aplicavam os controles de simulação.

**Onde o tempo é gasto**
- Primeira carga: leitura do Supabase em páginas sequenciais de mil linhas. A tabela fato
  leva 6,7 s, a das POFs anteriores 7,8 s, a população de uma região cerca de 7 s e a
  população por sexo de uma localidade cerca de 1,5 s. A pré-carga em segundo plano cobre
  só o Brasil.
- Depois da primeira carga, numa série: cerca de 70% do tempo recalcula a tendência
  nacional dos arranjos a cada requisição, embora ela só dependa dos dados; cerca de 20%
  remonta os parâmetros das células da localidade, que não dependem dos controles; só
  cerca de 5% é a projeção, a única parte que depende de `intensidade` e `k`.
