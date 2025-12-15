# How to start application

## Backend

Open one terminal and run:

```bash
git clone https://github.com/unchain0/eclipse-news/
cd backend/
uv sync
docker compose up -d
uv run uvicorn app.main:app --reload --reload-dir app --reload-dir migrations
```

## Frontend

Open another terminal and run:

```bash
cd frontend/
npm install
ng serve
```
