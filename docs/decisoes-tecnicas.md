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
- Fronteira oficial em 2070, não em 2060; o selo do topo diz "Cenário do modelo pendente".
- Controle da taxa de envelhecimento desativado até o cenário do modelo existir.
- Exportar avisa que o RF08 está pendente.
