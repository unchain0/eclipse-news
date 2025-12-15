# Elipse News – Backend

API backend para o projeto **Eclipse News**, responsável por:

- Fazer **scraping periódico** de notícias de vários portais.
- Persistir sites e notícias em **PostgreSQL**.
- Expor endpoints REST em **FastAPI** para o frontend Angular consumir.

## Stack

- **Python** 3.13
- **FastAPI**
- **SQLAlchemy** (ORM)
- **Alembic** (migrações)
- **PostgreSQL**
- **loguru** (logging)

## Pré‑requisitos

- PostgreSQL rodando via Docker Compose.
- Ambiente virtual criado e dependências instaladas (ex.: `uv sync`).

## Configuração

1. Crie o banco de desenvolvimento, por exemplo:

   ```sql
   CREATE DATABASE eclipse_news_dev;
   ```

2. Copie o arquivo `.env.example` para `.env`:

   ```bash
   cp .env.example .env
   ```

3. Rode as migrações do banco:

```bash
uv run alembic upgrade head
```

### Executando o Scraper

O scraper roda como um processo separado.

#### Execução Direta

```bash
uv run run_scraper.py --mode continuous

uv run run_scraper.py --mode single

uv run run_scraper.py --mode continuous --interval 120
```

## Variáveis de Ambiente

### Configuração do Banco

- `DATABASE_URL` - String de conexão PostgreSQL (obrigatório)

### Configuração do Scraping

- `SCRAPE_INTERVAL_SECONDS` - Intervalo entre ciclos de scraping (padrão: 60)
- `ALLOWED_DOMAINS` - Lista de domínios permitidos para scraping (separados por vírgula)
- `MAX_RETRIES` - Máximo de tentativas de retry para requisições HTTP (padrão: 3)
- `RETRY_DELAY_SECONDS` - Delay entre retries (padrão: 1.0)
- `REQUEST_TIMEOUT_SECONDS` - Timeout de requisições HTTP (padrão: 10)

### Configuração de Busca

- `MAX_SEARCH_RESULTS` - Máximo de resultados de busca para prevenir DoS (padrão: 1000)
- `SEARCH_QUERY_TIMEOUT_SECONDS` - Timeout de queries de busca no banco (padrão: 5)
- `MAX_SEARCH_PATTERN_LENGTH` - Tamanho máximo de padrão de busca (padrão: 50)

### Configuração da API

- `ALLOWED_ORIGINS` - Lista de origens permitidas para CORS (separadas por vírgula)

### Endpoints principais

- `GET /sites` – lista todos os sites cadastrados (schema `SiteOut`).
- `GET /news` – lista notícias paginadas, com filtros por site via query params:
  - `sites`: lista de slugs separados por vírgula (ex.: `veja,globo,cnn`).
  - `page`: página (default `1`).
  - `page_size`: tamanho da página (default `20`, máx `100`).

## Exemplo

```bash
curl "http://localhost:8000/news?sites=veja,globo&page=1&page_size=3"
```

```json
{
  "items": [
    {
      "id": 3814,
      "site_id": 2,
      "title": "Polícia identifica dupla que roubou obras de Matisse e Portinari",
      "url": "https://g1.globo.com/sp/sao-paulo/noticia/2025/12/08/policia-identifica-e-tenta-prender-os-dois-criminosos-que-roubaram-13-obras-de-matisse-e-portinari-em-biblioteca-de-sp.ghtml",
      "scraped_at": "2025-12-08T12:39:24.928916Z"
    },
    {
      "id": 3810,
      "site_id": 1,
      "title": "Flávio Bolsonaro vai receber líderes partidários após anunciar candidatura",
      "url": "https://veja.abril.com.br/politica/flavio-bolsonaro-vai-receber-presidentes-de-pl-uniao-brasil-e-pp-em-brasilia/",
      "scraped_at": "2025-12-08T12:36:12.237642Z"
    },
    {
      "id": 3807,
      "site_id": 2,
      "title": "As mudanças de posição que salvaram Vitória e Inter; veja cronologia",
      "url": "https://ge.globo.com/rs/futebol/brasileirao-serie-a/noticia/2025/12/08/cronologia-do-z-4-as-mudancas-de-posicao-que-salvaram-vitoria-e-inter-na-ultima-rodada.ghtml",
      "scraped_at": "2025-12-08T12:34:01.916124Z"
    }
  ],
  "total": 595,
  "page": 1,
  "page_size": 3,
  "pages": 199
}
```
