# Decisões técnicas

## Ferramentas de apoio adotadas (entram no Quadro de tecnologias do TCC)

| Ferramenta | Uso |
|---|---|
| Vite | build e servidor de desenvolvimento do React |
| Vitest, React Testing Library, jsdom | testes do front-end (o jsdom é o ambiente de DOM que o Vitest exige) |
| pytest, `TestClient` do FastAPI, httpx | testes do back-end (o `TestClient` depende do httpx) |
| uvicorn | servidor da API |
| psycopg | driver do PostgreSQL (conexão pronta em `api/app/core/db.py`, ainda sem uso) |

Ainda não adotado: D3 (entra com o gráfico do Panorama).

## Rotas do front-end

Roteamento por hash (`#pan`, `#dom`, `#eta`, `#sim`), feito em `web/src/app`,
sem biblioteca de rotas, para não adicionar dependência.

## Repositório ilustrativo da API

Enquanto não há projeção calculada, o módulo `projecoes` usa
`RepositorioIlustrativo`, que reproduz as funções do protótipo e marca
`dados_ilustrativos: true`. Trocar por um repositório que leia o banco não muda o
contrato.
