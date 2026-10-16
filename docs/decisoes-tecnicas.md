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
- Horizonte de 2026 a 2070, sem a área hachurada depois da projeção oficial; o selo do topo diz "Machine learning pausado".
- Controle da taxa de envelhecimento desativado até o cenário do modelo existir.
- Exportar baixa os dados reais pela rota `/exportar` em CSV ou XLSX (gerado com a biblioteca padrão do Python, sem nova dependência).

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

**Correção aplicada (14/10/2026) e nova medição**
1. A tendência nacional dos arranjos é calculada uma vez e fica em memória (`Dados.derivado`).
2. Por localidade, fica em memória o que não depende dos controles: os domicílios da
   localidade, os parâmetros das células, a taxa de chefia, as proporções observadas e a
   população por faixa e por grupo (`base_da_localidade`). A cada requisição, só a
   projeção com `intensidade` e `k` é recalculada.
3. As páginas do Supabase são lidas em paralelo (6 ao mesmo tempo, depois da primeira, que
   informa o total). A população das 27 UFs, por idade e por sexo, é lida uma vez, e o
   Brasil, as regiões e as UFs são somados em memória.

| Medida | Antes | Depois |
|---|---|---|
| Leitura da população das 27 UFs (130.221 linhas) | 65,6 s (em sequência) | 14,2 s (6 páginas em paralelo; 12 não melhoram) |
| Pré-carga em segundo plano até a série do Brasil responder rápido | não cobria as regiões | cerca de 42 s |
| Pré-carga completa, com a pirâmide de todas as UFs | sem dado | cerca de 82 s |
| `/projecoes/serie`, primeira chamada de uma região (Nordeste) | 7,31 s | 0,03 s |
| `/projecoes/serie`, depois da primeira (Brasil, Nordeste, SP) | 0,18 a 0,28 s | 0,008 s |
| `/arranjos/composicao`, depois da primeira | 0,12 a 0,24 s | 0,002 s |
| `/estrutura-etaria/piramides`, primeira chamada de uma UF | 1,63 s | 0,01 s |

Com e sem valores de simulação os tempos são os mesmos. A meta (menos de 1 s depois da
primeira carga de cada localidade) é cumprida com folga; depois da pré-carga, a primeira
carga de qualquer localidade também fica abaixo de 0,1 s. Rodar as cargas da pré-carga ao
mesmo tempo foi testado e piorou (cerca de 93 s), porque elas disputam as mesmas conexões.

## Panorama: indicadores e rótulos (15/10/2026)

- O gráfico tem três indicadores, todos calculados no back-end: consumo por pessoa (TBC
  padronizada), consumo total do recorte (calibrado, exibido em bilhões de kWh/mês) e
  participação no consumo residencial da localidade (%). "Todos os domicílios" abre no
  consumo por pessoa; os outros recortes, na participação, porque a média por pessoa de um
  grupo não sobe só porque o grupo cresce. A decomposição dos efeitos vale para os três.
- Rótulos da interface: `taxas` é "Envelhecimento e arranjos", `taxas_arranjos_fixos` é "Só o
  envelhecimento" e `contrafactual` é "Sem mudanças desde 2026". O texto do TCC mantém os
  termos técnicos.
- Layout conferido num Chrome de verdade (headless, protocolo DevTools) em 1920x1080, 1600x900 e
  1366x768: sem sobreposição dos rótulos do fim das linhas, sem rolagem no painel "Leitura do
  ano" e sem controle escondido.

**Cache por localidade (16/10/2026).** A pré-carga também prepara as 33 localidades (Brasil, 5
regiões e 27 UFs): base da projeção e somas de população por idade e por sexo. Medição: a
primeira consulta de uma região ou UF depois da pré-carga leva de 0,002 a 0,034 s (série,
pirâmide e composição).
