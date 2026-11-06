# Publicação no Vercel e integração contínua

O PROCED é publicado como dois projetos no Vercel, ambos ligados ao mesmo
repositório do GitHub pela integração Git:

| Projeto no Vercel | Pasta raiz | O que publica |
|---|---|---|
| `proced-api` | `backend` | API FastAPI como função Python (entrada `app/main.py`) |
| `proced-web` | `frontend` | SPA React gerada pelo Vite (`dist/`) |

Cada push gera um deploy de preview; o push na `main` gera o deploy de produção.
O GitHub Actions (`.github/workflows/ci.yml`) roda em paralelo, a cada push e
pull request:

1. testes do back-end e do ETL (`pytest`);
2. testes do front-end (`vitest`) e build;
3. checagem de travessão e meia-risca em todos os arquivos versionados;
4. na `main`, os testes de integração contra o banco real (`pytest -m integracao`),
   se os secrets do Supabase estiverem configurados.

Para impedir que um PR com teste falhando entre na `main`, ative a proteção da
ramificação no GitHub (Settings, Branches) exigindo os jobs do CI.

## Back-end (`proced-api`)

- **Dependências:** o Vercel instala só `requirements.txt` (FastAPI e httpx).
  Pandas, scikit-learn, pytest e uvicorn ficam em `requirements-dev.txt`, para
  desenvolvimento local, ETL e testes.
- **Python:** versão fixada em `backend/.python-version` (3.12, a mesma do CI).
- **Arquivos fora da função:** `backend/.vercelignore` retira `etl/`, `test/`,
  `.venv/` e `.env` do pacote.
- **Tempo máximo:** `backend/vercel.json` dá 60 segundos à função, porque a
  primeira consulta de uma instância nova lê as tabelas do Supabase.

Variáveis de ambiente (Settings, Environment Variables), nunca no repositório (RNF05):

| Variável | Valor |
|---|---|
| `SUPABASE_URL` | endereço do projeto no Supabase |
| `SUPABASE_SECRET_KEY` | chave secreta (`sb_secret_...`) |
| `CORS_ORIGIN` | endereço de produção do front-end, por exemplo `https://proced-web.vercel.app` (aceita vários, separados por vírgula) |
| `CORS_ORIGIN_REGEX` | opcional, libera os previews do front-end, por exemplo `^https://proced-web-[a-z0-9-]+-seu-time\.vercel\.app$` |

## Front-end (`proced-web`)

- `frontend/vercel.json` fixa o Vite como framework, `npm ci`, `npm run build`
  e a saída em `dist/`. As rotas usam hash, então não há reescrita de endereço.
- Variável de ambiente `VITE_API_URL`: endereço de produção da API, por exemplo
  `https://proced-api.vercel.app`. Vale para produção e preview; os previews do
  front-end conversam com a API de produção (por isso o `CORS_ORIGIN_REGEX`).

## Secrets do GitHub (Settings, Secrets and variables, Actions)

Só para o job de integração; sem eles, o job termina com aviso e sem erro.

| Secret | Valor |
|---|---|
| `SUPABASE_URL` | endereço do projeto no Supabase |
| `SUPABASE_SECRET_KEY` | chave secreta |

## Passo a passo da primeira publicação

1. No Vercel, Add New, Project, importe `M4RINH0/PROCED-TCC` com a pasta raiz
   `backend` e o nome `proced-api`. Cadastre as variáveis acima e publique.
2. Repita com a pasta raiz `frontend` e o nome `proced-web`, com `VITE_API_URL`
   apontando para o endereço da API do passo 1.
3. Volte ao `proced-api`, ajuste `CORS_ORIGIN` (e `CORS_ORIGIN_REGEX`) com o
   endereço do `proced-web` e faça um redeploy.
4. Em cada projeto, Settings, Git, ative "Skip deployments when there are no
   changes to the root directory", para um push só no front-end não publicar a API.
5. Confira `https://proced-api.vercel.app/docs` e a página inicial do front-end.
