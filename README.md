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

## Documentação

- `docs/contrato-api.md`: endpoints
- `docs/premissas.md`: premissas adotadas e fontes
- `docs/banco-supabase.md`: o que existe no banco
