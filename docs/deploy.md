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

## Partida a frio da API e como ela é contornada

No Vercel a API é uma função serverless: o Vercel liga uma instância quando chega uma
requisição e a desliga depois de um tempo ociosa (o Vercel não publica esse tempo). O
cache da API mora na memória da instância, então cada instância nova relê as tabelas do
Supabase antes de responder.

**Medição de 11/11/2026** (`proced-tcc.vercel.app`, instância desligada):

| Chamada | Primeira, com a instância desligada | Depois |
|---|---|---|
| `/fontes` (só ligar a função) | 9,2 s | 0,3 s |
| `/projecoes/serie` (Panorama) | 37,6 s | 0,3 s |
| `/estrutura-etaria/piramides` | 57,6 s | 0,2 s |

Três medidas, que se somam:

1. **Dados de abertura no front-end.** No build, o Vite grava em `dist/dados-iniciais.json`
   as respostas da API para a visão padrão de cada tela (Brasil, controles no padrão; 21
   consultas, 263 kB, 32 kB comprimido). A lista fica em
   `frontend/src/services/dadosIniciais.js`. São respostas da própria API, sem cálculo no
   front-end. Se a API não responder no build, o build segue sem o arquivo e o site
   consulta a API como antes.
2. **Aquecimento na abertura.** Em produção, o front-end chama por trás a série e a
   pirâmide do Brasil assim que a página abre, para a API carregar as tabelas enquanto o
   usuário vê a tela inicial.
3. **Cache na memória do navegador.** Cada consulta vai à API uma vez por visita
   (`frontend/src/services/cache.js`). A falha simulada do menu Demonstração continua
   valendo, e o Simulador com `recalcular` nunca usa o cache.

Como os dados de abertura são gravados no build do front-end, **uma mudança na API que
altere essas respostas exige republicar o `proced-web` depois do `proced-api`** (no Vercel,
Deployments, Redeploy).

### Cron para manter a API ligada

Um serviço gratuito de cron chama a API a cada 5 minutos, para a instância não ficar
ociosa. Configuração no [cron-job.org](https://cron-job.org) (conta gratuita), com duas
tarefas:

| Campo | Tarefa 1 | Tarefa 2 |
|---|---|---|
| Title | PROCED série | PROCED pirâmide |
| URL | `https://proced-tcc.vercel.app/projecoes/serie?recorte=todos_domicilios&localidade=Brasil&intensidade=0.6&k=1` | `https://proced-tcc.vercel.app/estrutura-etaria/piramides?localidade=Brasil&k=1` |
| Execution schedule | Every 5 minutes | Every 5 minutes |
| Request method | GET | GET |

As duas chamadas obrigam a API a carregar todas as tabelas; chamar só `/fontes` liga a
função, mas não carrega os dados. A primeira execução, com a instância desligada, pode
aparecer como falha por tempo limite no cron-job.org; as seguintes devem levar menos de
1 segundo. O cron reduz as partidas a frio, mas não as elimina: o Vercel pode reciclar a
instância, abrir uma segunda quando há acessos simultâneos e começa do zero a cada
publicação. Os itens 1 a 3 cobrem esses casos.

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
