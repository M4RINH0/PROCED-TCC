# PROCED-TCC

PROCED: Projeção de Consumo por Estrutura Demográfica. Aplicação web que projeta o
impacto do envelhecimento populacional sobre o consumo residencial de energia
elétrica no Brasil, no horizonte de 2026 a 2070.

## Como rodar

Pré-requisitos: Python 3.11 ou mais novo, Node.js 20 ou mais novo e Git.
Os comandos abaixo são para o Git Bash no Windows; no PowerShell, troque
`cp` por `copy` e as barras `/` por `\`.

### 1. Baixar o projeto

```bash
git clone https://github.com/M4RINH0/PROCED-TCC.git
cd PROCED-TCC
```

### 2. Back-end (terminal 1)

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env    # só na primeira vez: sobrescreve o .env existente
```

Abra `backend/.env` e preencha `SUPABASE_SECRET_KEY` com a chave secreta do Supabase
(Project Settings, API Keys). Depois:

```bash
.venv/Scripts/python -m uvicorn app.main:app --reload
```

A API sobe em http://localhost:8000 e a documentação fica em http://localhost:8000/docs.
Ao subir, ela lê o banco em segundo plano por cerca de 10 segundos.

### 3. Front-end (terminal 2)

```bash
cd frontend
npm install
cp .env.example .env    # só na primeira vez
npm run dev
```

Abra http://localhost:5173. O front-end precisa estar nessa porta, que é a liberada no CORS da API;
se aparecer "Port 5173 is already in use", feche o outro processo que está nela.

### 4. Testes

```bash
cd backend && .venv/Scripts/python -m pytest   # API e ETL
cd frontend && npm test                        # front-end
```

## Documentação Oficial & GitHub Pages

A documentação completa, interativa e detalhada do projeto está publicada no GitHub Pages:

🔗 **[https://m4rinh0.github.io/PROCED-TCC/](https://m4rinh0.github.io/PROCED-TCC/)**

Deploy automático configurado no GitHub Actions a cada commit na branch `main`.

### Seções da Documentação:
* **[Guia do Usuário](https://m4rinh0.github.io/PROCED-TCC/guia-usuario/):** Como utilizar as telas de Panorama, Domicílios, Estrutura Etária, Simulador, Comparador e Exportação.
* **[Arquitetura do Sistema](https://m4rinh0.github.io/PROCED-TCC/arquitetura/):** Diagramas de blocos, ciclo de vida de requisição, motor assíncrono de cache e decisões técnicas.
* **[Engenharia de Dados & Pipeline ETL](https://m4rinh0.github.io/PROCED-TCC/etl/):** Fases 1 a 6 do ETL (BigQuery, POF 2017, Censo 2022, POF histórica 2002/2008, Supabase e experimento de Machine Learning).
* **[Banco & Dicionário de Dados](https://m4rinh0.github.io/PROCED-TCC/dicionario-dados/):** Diagrama ERD e mapeamento exaustivo das 9 tabelas do Supabase.
* **[Metodologia Científica & Premissas](https://m4rinh0.github.io/PROCED-TCC/metodologia/):** Formulação matemática formal (TBC padronizada, decomposição aditiva de efeitos, calibração populacional e validação temporal).
* **[Resultados & Cenários](https://m4rinh0.github.io/PROCED-TCC/resultados/):** Síntese numérica de 2026 a 2070 e análise do paradoxo do consumo no declínio demográfico.
* **[Contrato da API](https://m4rinh0.github.io/PROCED-TCC/contrato-api/):** Endpoints REST, schemas e validações.
