# Arquitetura do Sistema

A arquitetura do **PROCED** foi desenhada para atender a dois requisitos centrais aparentemente contraditórios:

1. **Rigor Científico e Demográfico:** Processamento de microdados com planos amostrais complexos (POF), interpolação censitária (Censo 2022) e séries demográficas de longo prazo do IBGE com projeções até 2070.
2. **Alta Performance e Interatividade em Tempo Real (RNF02):** Resposta imediata (sub-10ms em consultas de série temporal e sub-2ms em composições após aquecimento) na manipulação de múltiplos filtros e controles de simulação no navegador.

Para atingir esses objetivos, o sistema adota um padrão de **Três Camadas Desacopladas** complementado por um mecanismo de **Cache e Indexação em Memória no Backend**.

---

## 1. Diagrama de Arquitetura de Alto Nível

O fluxo global de ponta a ponta compreende a camada de dados em nuvem, a camada de aplicação FastAPI, e a interface frontend SPA:

```mermaid
graph TD
    subgraph Fontes de Dados Primárias
        BD[Base dos Dados / BigQuery<br/>POF 2017-2018 & Censo 2022]
        IBGE_FTP[IBGE Microdados FTP<br/>POFs 2002-2003 e 2008-2009]
        IBGE_PROJ[IBGE Planilhas de Projeção<br/>Revisão 2024 de 2000 a 2070]
    end

    subgraph Pipeline de Engenharia de Dados ETL
        SQL1[CREATE-pof.sql]
        SQL2[CREATE-pof-historica.sql]
        PY1[migraDados.py]
        ETL_HIST[python -m etl.historica]
    end

    subgraph Banco de Dados em Nuvem Supabase
        PG[(PostgreSQL 15+<br/>Supabase BaaS)]
        T1[fato_consumo_domiciliar<br/>52.102 domicílios]
        T2[fato_consumo_pof_historica<br/>88.726 domicílios]
        T3[projecoes_populacao_idade<br/>639.639 linhas]
        T4[cenario_salvo<br/>JSONB de Simulações]
    end

    subgraph Backend FastAPI
        API_MAIN[app.main / Uvicorn]
        CACHE[Motor de Cache em Memória<br/>Dados.derivado & 33 Localidades]
        CALC[Motor Demográfico e Analítico<br/>app.calculo.Projecao]
        ROUTER[Rotas REST: /projecoes, /arranjos,<br/>/estrutura-etaria, /simulador, /comparacao, /exportar]
    end

    subgraph Frontend Web SPA
        REACT[React 18 + Vite]
        ROUTER_HASH[Roteamento Hash: #pan, #dom, #eta, #sim, #comp]
        SVG_CHARTS[Gráficos Vetoriais SVG Nativos<br/>Séries, Pirâmides e Barras]
    end

    BD --> SQL1 --> T1
    IBGE_FTP --> SQL2 --> ETL_HIST --> T2
    IBGE_PROJ --> PY1 --> T3

    T1 & T2 & T3 -->|PostgREST Async Paginado| CACHE
    T4 <-->|Gravação & Leitura de Simulações| ROUTER
    CACHE --> CALC --> ROUTER
    ROUTER -->|JSON REST API| REACT
    REACT --> SVG_CHARTS
```

---

## 2. Diagrama de Ciclo de Vida da Requisição

Quando o usuário manipula um controle de simulação ou altera a localidade no navegador, a requisição percorre as camadas do sistema conforme o diagrama de sequência abaixo:

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Usuário
    participant UI as Frontend React
    participant API as FastAPI Router
    participant Mem as In-Memory Cache (Dados)
    participant Calc as Motor de Projeção (app.calculo)
    participant BD as Supabase (PostgreSQL)

    Usuario->>UI: Ajusta controle k=1.2 e intensidade=0.8
    UI->>API: GET /projecoes/serie?recorte=todos_domicilios&localidade=SP&k=1.2&intensidade=0.8
    API->>Mem: Recupera base_da_localidade("SP")
    Note over Mem: Dados pré-indexados:<br/>domicílios ponderados, chefia,<br/>e população por faixa etária
    Mem-->>API: Parâmetros e Proporções de SP
    API->>Calc: Projecao(base_sp, intensidade=0.8, k=1.2).executar()
    Note over Calc: Projeta domicílios anuais,<br/>aplica tendência log-linear,<br/>calcula TBC e calibra com IBGE
    Calc-->>API: Série temporal 2026-2070 + Decomposição
    API-->>UI: 200 OK (JSON com pontos e efeitos) [~8 ms]
    UI->>Usuario: Gráfico SVG atualizado dinamicamente
```

---

## 3. Estratégia de Inicialização, Pré-Carga e Cache em Memória

Uma das principais inovações técnicas do PROCED é a sua estratégia de **pré-carga assíncrona em memória**. 

Como o Supabase impõe um limite máximo de 1.000 linhas por requisição HTTP via PostgREST e não suporta agregação nativa via REST simples sem functions RPC, ler as tabelas em tempo real sob demanda do usuário causaria lentidão inaceitável (de 7 a 65 segundos por tela).

Para eliminar esse gargalo:

```mermaid
flowchart TD
    Start[Inicialização do Uvicorn / Startup Event] --> Step1[Inicia Leitura em Background]
    Step1 --> Worker1[Worker Assíncrono Paralelo: 6 Conexões HTTP ao Supabase]
    Worker1 --> Fetch1[Lê fato_consumo_domiciliar: 52.102 linhas com peso_final]
    Worker1 --> Fetch2[Lê fato_consumo_pof_historica: 88.726 linhas]
    Worker1 --> Fetch3[Lê projecoes_populacao_idade: 130.221 linhas de 27 UFs]
    
    Fetch1 & Fetch2 & Fetch3 --> Audit[Auditoria em Memória: Confere total lido contra Content-Range]
    Audit --> CalcDeriv[Calcula Tendência Nacional dos Arranjos - P13]
    CalcDeriv --> Localities[Gera Cache Indexado das 33 Localidades:<br/>Brasil, 5 Regiões e 27 UFs]
    Localities --> Ready[Sistema 100% Aquecido: Consultas Sub-10ms]
```

### Resultados da Otimização de Performance (Medições Reais):

| Métrica de Desempenho | Antes da Otimização | Após Pré-Carga e Cache em Memória | Ganho de Desempenho |
|---|---|---|---|
| Leitura da população das 27 UFs (130 mil linhas) | 65,6 s (em sequência) | **14,2 s** (6 workers paralelos) | **$4,6\times$ mais rápido** |
| `/projecoes/serie` (Brasil, 45 anos) | 4,44 s | **0,008 s (8 ms)** | **$555\times$ mais rápido** |
| `/projecoes/serie` (Nordeste, 45 anos) | 7,31 s | **0,008 s (8 ms)** | **$913\times$ mais rápido** |
| `/arranjos/composicao` (todas as faixas) | 0,29 s | **0,002 s (2 ms)** | **$145\times$ mais rápido** |
| `/estrutura-etaria/piramides` (2026-2070) | 1,63 s | **0,010 s (10 ms)** | **$163\times$ mais rápido** |

---

## 4. Detalhamento das Camadas do Sistema

### 4.1. Camada de Apresentação (Frontend)
* **Framework:** React 18 construído com **Vite** para empacotamento ultrarrápido (*Hot Module Replacement*).
* **Roteamento Leve:** Roteamento por *hash* nativo (`#pan`, `#dom`, `#eta`, `#sim`, `#comp`) sem frameworks pesados de roteamento externo, garantindo portabilidade para execução em qualquer servidor estático ou CDN.
* **Renderização Gráfica em SVG Puro:** Ao contrário de soluções convencionais que importam bibliotecas de terceiros como D3 ou Chart.js (que adicionam centenas de kilobytes ao bundle), todos os gráficos do PROCED (linhas temporais, pirâmides etárias, barras de consumo e sparklines) são **componentes React SVG puros**, desenhados diretamente via código matemático de coordenadas normalizadas.
* **Componentes Modulares:** Arquitetura organizada em páginas (`pages/`), componentes atômicos (`components/`), hooks customizados (`hooks/`) e serviços de comunicação (`services/`).

### 4.2. Camada de Aplicação e Serviços (Backend)
* **Framework:** **FastAPI** rodando sobre o servidor ASGI **Uvicorn**.
* **Validação de Schemas e Contratos:** **Pydantic v2** garante a tipagem estrita de cada parâmetro de consulta (`query params`), rejeitando dados fora do domínio científico (com respostas HTTP 422 padronizadas).
* **Estrutura em Camadas Claras:**
  * `routes/`: Roteadores HTTP por contexto de negócio (Panorama, Domicílios, Estrutura Etária, Simulador, Comparação, Exportação, Fontes, Localidades).
  * `services/`: Orquestradores de regras de negócio e despacho.
  * `schemas/`: Modelos Pydantic de entrada e saída.
  * `dominio.py`: Constantes, enumerações, definições das células e agrupamentos demográficos.
  * `calculo.py`: Motor matemático puro e desacoplado de dependências web.
  * `dados.py`: Camada de acesso e gerenciamento de cache em memória.

### 4.3. Camada de Persistência e Dados (Supabase)
* **SGBD:** PostgreSQL 15 hospedado no Supabase.
* **Tabelas Operacionais em Produção:**
  * `fato_consumo_domiciliar`: 52.102 microdados da POF 2017–2018 com `peso_final`.
  * `fato_consumo_pof_historica`: 88.726 microdados das POFs 2002 e 2008 para estimação da tendência de arranjos (P13).
  * `projecoes_populacao_idade`: 639.639 registros de população IBGE (2000–2070).
  * `cenario_salvo`: Tabela de persistência e aceleração de simulações em `jsonb` (RF09).
* **Tabelas Exploratórias de Baseline:**
  * `dim_coeficiente_consumo` e `consumo_estimado`: Criadas na fase inicial de exploração no BigQuery. Não são consumidas pela API nem pelo motor de projeções, pois foram geradas com médias simples (sem `peso_final`) e resolução binária de idade.
* **Segurança e Isolamento (RLS):** *Row Level Security* (RLS) habilitado em todas as tabelas. As chaves públicas (`anon`) têm acesso negado por padrão; apenas a API do backend, munida da `SUPABASE_SECRET_KEY` via conexões seguras HTTPS/TLS, tem permissão de leitura sobre as tabelas mestras e gravação exclusiva na tabela `cenario_salvo`.

---

## 5. Arquitetura de Exportação e Auditoria

A geração de arquivos em `/exportar` e `/exportar/comparacao` foi desenvolvida sem bibliotecas externas pesadas:
* **Geração CSV:** Biblioteca padrão Python `csv` formatando saídas em UTF-8 com BOM (`\ufeff`) para compatibilidade com o Excel brasileiro.
* **Geração XLSX:** Engine nativa otimizada que gera planilhas Excel estruturadas com formatação tipada de células.
* **Trilha de Auditoria:** Cada linha exportada carrega o `timestamp` de geração com fuso horário, a versão do modelo (`VERSAO_MODELO = "2026-10-14"`), os valores exatos de $k$ e intensidade empregados e a flag booleana de simulação.
