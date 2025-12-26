# How to start application

## Backend

### 1. Setup inicial (primeira vez)

```bash
git clone https://github.com/unchain0/eclipse-news/
cd backend/
uv sync
docker compose up -d

# Executar migrações do banco de dados
uv run alembic upgrade head
```

### 2. Servidor da API

Open one terminal and run:

```bash
cd backend/
uv run uvicorn app.main:app --reload --reload-dir app --reload-dir migrations
```

### 3. Processo de Scraping

Open another terminal and run:

```bash
cd backend/
uv run run_scraper.py --mode continuous
```

**Opções do scraper:**

- `--mode continuous`: Roda continuamente a cada 60 segundos (padrão)
- `--mode single`: Executa apenas uma vez
- `--interval N`: Define o intervalo em segundos (ex: `--interval 120`)

## Frontend

Open another terminal and run:

```bash
cd frontend/
npm install
ng serve
```
