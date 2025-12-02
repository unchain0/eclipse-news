# Prisma News – Plano de Arquitetura e Migração

## 1. Visão Geral do Projeto

- **Nome do projeto:** Prisma News (`prisma-news`).
- **Objetivo:**

  - Transformar o projeto atual (CLI que faz scraping de notícias) em:
    - **Backend**: API REST em FastAPI.
    - **Frontend**: aplicação web em Angular.
  - Usuário escolhe quais sites de notícias quer ver; sistema exibe apenas notícias desses sites.

- **Estado atual:**
  - Projeto Python `asimov-news` com:
    - `scripts/site.py`: classe `Site` com scrapers para `veja`, `r7`, `globo`, `cnn`, `livecoins`, `poder360`.
    - `scripts/utils.py`: dataclasses `News` e `Article`.
    - `scripts/asimov_news.py`: classe `AsimovNews` com:
      - Thread que atualiza notícias periodicamente (\_update_news).
      - Armazenamento em arquivos `news.pkl` e `sites.pkl`.
      - Interface de linha de comando (menu, paginação, seleção de sites).
    - `main.py` que executa `AsimovNews.main_loop()`.

---

## 2. Decisões Técnicas Consolidadas

### 2.1. Stack e Arquitetura

- **Backend**

  - Framework: **FastAPI**.
  - ORM: **SQLAlchemy síncrono**.
  - Migrações: **Alembic**.

- **Frontend**

  - Framework: **Angular** (SPA).
  - Comunicação com backend via HTTP (REST, JSON).

- **Banco de dados**
  - **Desenvolvimento (dev):** PostgreSQL local (Docker ou serviço nativo).
  - **Produção (prod):** PostgreSQL no **Supabase**.
  - Migrações Alembic rodando em ambos os ambientes (dev e prod).

### 2.2. Scraping de Notícias

- Scraping será feito **no servidor**, em um **job de background** contínuo.
- Intervalo do job: **a cada 1 minuto** por site.
- O backend FastAPI, ao subir, inicia uma thread/loop que:
  - Percorre todos os sites configurados.
  - Executa os scrapers existentes (`Site.update_news()` de `scripts/site.py`).
  - Salva as notícias no banco respeitando as regras abaixo.
- Os endpoints **não** executam scraping sob demanda; apenas consultam o banco.

### 2.3. Modelagem de Dados (PostgreSQL)

Tabelas principais:

- **sites**

  - `id` (PK)
  - `slug` (por exemplo: `"veja"`, `"r7"`, `"globo"`) – **único**.
  - `name` (nome amigável, ex.: `"VEJA"`, `"R7"`).
  - `created_at` (timestamp de criação).

- **news**
  - `id` (PK).
  - `site_id` (FK → `sites.id`).
  - `title` (título da notícia).
  - `url` (link da notícia).
  - `scraped_at` (timestamp de quando foi coletada).
  - Índices/constraints:
    - **Unicidade**: `UNIQUE(site_id, url)`.
    - Índice em `scraped_at` para ordenação/consulta.

### 2.4. Política de Histórico

- **Histórico de notícias:**
  - O sistema deve **guardar todas as notícias** (histórico completo), sem apagar automaticamente.
  - Cada scraping pode inserir novos registros.
  - A unicidade é por `(site_id, url)`; se a mesma URL aparecer novamente, ela não será duplicada.

### 2.5. Filtro de Sites

- Filtro será **stateless por query params** na API.
- O cliente (Angular) envia quais sites deseja nos parâmetros da requisição:
  - Exemplo: `GET /news?sites=veja,r7,globo&page=1&page_size=20`.
- O backend não mantém estado de “sites ativos” por usuário; isso é responsabilidade do frontend (estado no cliente, por exemplo em `localStorage`).

### 2.6. Configuração e Secrets

- Uso de arquivos `.env` separados para **dev** e **prod** (por exemplo: `.env` e `.env.prod`), não versionados.
- Variáveis esperadas (inicialmente):
  - `DATABASE_URL`
  - `SCRAPE_INTERVAL_SECONDS` (default: 60).
  - `ALLOWED_ORIGINS` (origens permitidas para CORS, ex.: `http://localhost:4200`).
- Em produção, os valores podem vir de variáveis de ambiente do provedor de deploy.

---

## 3. Backend Prisma News – Arquitetura Planejada

### 3.1. Estrutura de Pastas (Backend)

Proposta de organização dentro do repositório atual:

```text
prisma-news/ (nome lógico do projeto)
  scripts/            # código legado (CLI + scrapers), será removido após refatoração
    site.py           # scrapers atuais (LEGACY; serão reescritos em app/services e depois removidos)
    utils.py          # dataclasses Article/News (podem ser usados como auxiliares, mas serão migradas se necessário)
    asimov_news.py    # CLI legado (não será mais o entrypoint principal)
  app/
    __init__.py
    main.py           # cria a app FastAPI, configura CORS, inclui routers, inicia job de scraping
    config.py         # leitura de variáveis de ambiente (.env)
    database.py       # engine + SessionLocal (SQLAlchemy síncrono) + get_db
    models.py         # modelos SQLAlchemy (SiteModel, NewsModel)
    schemas.py        # modelos Pydantic (SiteOut, NewsOut, PaginatedNewsOut)
    services/
      __init__.py
      scraping_service.py   # lógica de scraping e gravação no banco
    routers/
      __init__.py
      sites.py        # endpoints relacionados a sites (GET /sites)
      news.py         # endpoints relacionados a notícias (GET /news)
```

> Observação: o nome da pasta do repositório físico ainda é `asimov-news` no momento; o nome conceitual do sistema será tratado como Prisma News a partir de agora. Uma etapa futura pode cuidar de renomear caminhos/módulos, se desejado.

### 3.2. Componentes Principais

#### 3.2.1. `app/config.py`

- Responsável por carregar configurações (via `python-dotenv` ou similar):
  - `DATABASE_URL`
  - `SCRAPE_INTERVAL_SECONDS`
  - `ALLOWED_ORIGINS`
- Fornece um objeto/estrutura de configuração acessível pelo resto da aplicação.

#### 3.2.2. `app/database.py`

- Cria o `engine` SQLAlchemy síncrono apontando para `DATABASE_URL`.
- Define `SessionLocal` (factory de sessões).
- Fornece função `get_db()` para injetar sessão nos endpoints via `Depends`.

#### 3.2.3. `app/models.py`

- Contém os modelos ORM:
  - `SiteModel` (tabela `sites`).
  - `NewsModel` (tabela `news`).

#### 3.2.4. `app/schemas.py`

- Modelos Pydantic para entrada/saída da API:
  - `SiteOut`
  - `NewsOut`
  - `PaginatedNewsOut` (contendo `items`, `total`, `page`, `page_size`, `pages`).

#### 3.2.5. `app/services/scraping_service.py`

- Reescreve a lógica de scraping que hoje está em `scripts/site.py` para serviços internos do backend:
  - Um serviço central (`scraping_service.py`) e, se necessário, helpers específicos por site.
  - Sem importar diretamente a pasta `scripts/` (que será removida após a migração).
- Converte os dados raspados → `NewsModel` e grava no banco respeitando:
  - `UNIQUE(site_id, url)`.
  - Histórico completo (não apaga registros antigos; apenas evita duplicar mesma URL).
- Funções planejadas:
  - `scrape_all_sites_once(session_factory)` – roda uma varredura completa de todos os sites.
  - `scraping_loop(session_factory, interval_seconds)` – loop infinito com `sleep(interval_seconds)`.

#### 3.2.6. Job em Background (em `app/main.py`)

- No evento `startup` da aplicação FastAPI:
  - Cria uma thread daemon que executa `scraping_loop(...)` com `interval_seconds` vindo da configuração (default 60).
- O backend continua respondendo requisições enquanto o job de scraping atualiza o banco.

#### 3.2.7. Rotas / Endpoints

- **`GET /health`**

  - Endpoint simples para checar se a API está de pé.

- **`GET /sites`** (em `app/routers/sites.py`)

  - Lê a tabela `sites` do banco.
  - Retorna lista de sites (`SiteOut`).

- **`GET /news`** (em `app/routers/news.py`)
  - Query params planejados:
    - `sites`: lista de slugs de sites (por exemplo, `veja,r7,globo`).
    - `page`: inteiro, default 1.
    - `page_size`: inteiro, default 20.
  - Comportamento:
    - Converte o parâmetro `sites` em lista.
    - Filtra `NewsModel` por `site.slug` nessa lista.
    - Ordena por `scraped_at` (descendente).
    - Aplica paginação.
  - Resposta:
    - Estrutura `PaginatedNewsOut`.

### 3.3. CLI Legado

- O código de CLI atual (`AsimovNews` em `scripts/asimov_news.py`) será **mantido como legado** inicialmente, mas:
  - O entrypoint principal do projeto passará a ser a API FastAPI (`uvicorn app.main:app`).
  - O arquivo `main.py` atual, que executa `AsimovNews.main_loop()`, será substituído/ajustado em uma etapa futura.

---

## 4. Frontend Angular – Arquitetura Planejada

### 4.1. Objetivo do Frontend

- Reproduzir (e depois expandir) as funcionalidades da CLI atual:
  - Permitir que o usuário selecione quais sites de notícias quer visualizar.
  - Exibir a lista de notícias paginada.
  - Abrir links das matérias no navegador.

### 4.2. Estrutura de Pastas (Angular)

Projeto Angular sugerido (por exemplo, `prisma-news-web`):

```text
prisma-news-web/
  src/app/
    core/
      services/
        news.service.ts       # comunicação com a API FastAPI (/sites, /news)
      models/
        site.model.ts
        news.model.ts
    features/
      news/
        news-page.component.ts       # container principal da tela de notícias
        site-filter.component.ts     # seleção de sites (checkboxes, listas)
        news-list.component.ts       # exibição da lista de notícias + paginação
    shared/
      components/                    # componentes genéricos (spinner, mensagens etc.)
```

### 4.3. Fluxo de Uso (Frontend)

1. Ao carregar a aplicação:

   - `newsService.getSites()` busca todos os sites (`GET /sites`).
   - Carrega seleção de sites do `localStorage` (equivalente ao conceito atual de "sites ativos").
   - Chama `newsService.getNews({ sitesSelecionados, page: 1 })` para carregar as notícias.

2. Ao marcar/desmarcar sites:

   - Atualiza a seleção em estado local + `localStorage`.
   - Chama novamente `getNews` com a nova lista de sites.

3. Ao mudar de página:

   - Atualiza `page` (opcionalmente, também query params na URL).
   - Chama `getNews` com a página nova.

4. Ao clicar em uma notícia:
   - Abre `link` da notícia em nova aba/janela.

---

## 5. Fases de Implementação (Backend Primeiro)

### Fase 1 – Infraestrutura de Desenvolvimento

- Configurar Postgres local (Docker ou serviço nativo).
- Criar banco de desenvolvimento (ex.: `prisma_news_dev`).
- Definir `.env` de desenvolvimento com:
  - `DATABASE_URL` apontando para o Postgres local.
  - `SCRAPE_INTERVAL_SECONDS=60`.
  - `ALLOWED_ORIGINS` para o Angular em `http://localhost:4200` (ou similar).

### Fase 2 – Esqueleto do Backend FastAPI

- Criar pasta `app/` com os arquivos mínimos:
  - `main.py` (FastAPI, CORS, `/health`).
  - `config.py` (leitura de `.env`).
  - `database.py` (engine e sessão SQLAlchemy síncrona).
  - Estrutura inicial de `routers/` (mesmo que vazios) e `services/`.

### Fase 3 – Modelos SQLAlchemy e Migrações Alembic

- Implementar `SiteModel` e `NewsModel` em `models.py`.
- Configurar Alembic para o projeto.
- Criar migração inicial (tabelas `sites` e `news`).
- Rodar migração no banco de desenvolvimento.
- Popular tabela `sites` com os slugs atuais suportados.

### Fase 4 – Serviço de Scraping e Job em Background

- Reescrever a lógica de scraping existente na pasta `scripts/` em serviços dentro de `app/services/`:
  - Implementar `scraping_service.py` e, se necessário, módulos auxiliares por site.
  - Funções `scrape_all_sites_once` e `scraping_loop`.
- Integrar o loop de scraping com o evento de `startup` do FastAPI via thread daemon.

### Fase 5 – Endpoints `/sites` e `/news`

- Implementar `GET /sites` em `routers/sites.py`.
- Implementar `GET /news` em `routers/news.py` com filtros por site e paginação.
- Garantir que o frontend possa filtrar notícias por lista de slugs de sites.

### Fase 6 – Descontinuação do CLI e Remoção de Código Legado

- Ajustar o `main.py` raiz do repositório (ou scripts de execução) para usar `uvicorn app.main:app`.
- Remover a pasta `scripts/` (CLI e scrapers legados), após confirmar que toda a lógica necessária foi migrada para `app/`.

### Fase 7 – Frontend Angular

- Criar projeto Angular (`prisma-news-web`).
- Implementar serviços e componentes planejados.
- Integrar com a API FastAPI (CORS/proxy, testes end-to-end locais).

### Fase 8 – Preparação para Produção

- Configurar Supabase (banco de produção) e rodar migrações Alembic nele.
- Definir estratégia de deploy para FastAPI (Railway, Render, Fly.io, VPS etc.).
- Definir estratégia de deploy para Angular (Netlify, Vercel, etc.).
- Configurar `.env.prod` ou variáveis de ambiente correspondentes.

---

## 6. Pontos em Aberto / Decisões Futuras

Algumas decisões foram deixadas para mais tarde, mas o planejamento já prevê espaço para elas:

- **Provedor de deploy do FastAPI em produção** (Railway, Render, Fly.io, VPS própria, etc.).
- **Provedor de deploy do Angular** (Netlify, Vercel, GitHub Pages com ajustes, etc.).
- Possível **renomeação completa de arquivos/classes** (`AsimovNews` → `PrismaNews`, `asimov_news.py` → `prisma_news.py`, etc.).
- Eventuais funcionalidades extras no frontend além das já existentes (filtro por texto, período, auto-refresh da página, temas, etc.).

---

## 7. Convenção de Atualização deste Plano

- Este arquivo `plan.md` deve ser **atualizado sempre que houver mudança relevante no planejamento**:
  - Novas decisões arquiteturais.
  - Mudança na modelagem de dados.
  - Alteração nas fases de implementação.
  - Escolha de provedores de deploy.
- As próximas alterações de planejamento serão refletidas aqui para manter uma visão única e atualizada do estado do projeto Prisma News.

## 8. Checklist de Implementação

- [x] Fase 1 – Infraestrutura de Desenvolvimento (Postgres local, banco `prisma_news_dev`, `.env` de dev)
- [x] Fase 2 – Esqueleto do Backend FastAPI (pasta `app/`, `main.py`, `config.py`, `database.py`, estruturas básicas de `routers/` e `services/`)
- [x] Fase 3 – Modelos SQLAlchemy e Migrações Alembic (`SiteModel`, `NewsModel`, configuração do Alembic e migração inicial)
- [ ] Fase 4 – Serviço de Scraping e Job em Background (reutilizando `scripts/site.py` e integrando com o banco)
- [ ] Fase 5 – Endpoints `/sites` e `/news` com filtros por site e paginação
- [ ] Fase 6 – Descontinuação do CLI como entrypoint principal (usar `uvicorn app.main:app`)
- [ ] Fase 7 – Frontend Angular (projeto `prisma-news-web`, serviços e componentes básicos)
- [ ] Fase 8 – Preparação para Produção (Supabase, deploy do FastAPI e do Angular, `.env.prod`)
