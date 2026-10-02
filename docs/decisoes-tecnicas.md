# Decisões técnicas

## Ferramentas de apoio adotadas (entram no Quadro de tecnologias do TCC)

| Ferramenta | Uso |
|---|---|
| Vite | build e servidor de desenvolvimento do React |
| Vitest, React Testing Library, jsdom | testes do front-end (o jsdom é o ambiente de DOM que o Vitest exige) |
| httpx | cliente HTTP da API para ler o Supabase; também usado pelo `TestClient` |
| pytest, `TestClient` do FastAPI | testes do back-end |
| uvicorn | servidor da API |
| psycopg | driver do PostgreSQL (conexão pronta em `api/app/core/db.py`, ainda sem uso: falta a `DATABASE_URL`) |

Não adotado: D3. Os gráficos são componentes SVG próprios, sem biblioteca.

## Rotas do front-end

Roteamento por hash (`#pan`, `#dom`, `#eta`, `#sim`), feito em `web/src/app`,
sem biblioteca de rotas, para não adicionar dependência.

## Leitura do banco

A API lê o Supabase pela REST (PostgREST) com a chave secreta, só no back-end
(`api/app/core/supabase.py`). O Supabase devolve no máximo mil linhas por consulta e
não permite agregação, então cada tabela é lida uma vez, paginada, e mantida em
memória. Ao subir, a API faz essa leitura em segundo plano (cerca de 10 segundos).

## Dependência entre módulos da API

`arranjos` e `estrutura_etaria` usam a interface pública de `projecoes` (função `tec`,
TEC por faixa e repositório). `projecoes` não depende de nenhum outro módulo.

## Design do front-end

O CSS do `prototipo/proced.html` foi copiado inteiro para `web/src/app/estilos.css`,
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
