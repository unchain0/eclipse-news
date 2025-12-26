from datetime import datetime, timezone
from math import ceil
from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NewsModel, SiteModel
from app.schemas import NewsOut, NewsQueryParams, PaginatedNewsOut
from app.services.scraping_core import SUPPORTED_SITE_SLUGS
from app.utils import parse_time_range

router = APIRouter(prefix="/news", tags=["news"])


@router.get(
    "",
    response_model=PaginatedNewsOut,
    summary="Listar notícias com filtros e paginação",
    response_description="Lista paginada de notícias com metadados de paginação",
)
def list_news(
    params: Annotated[NewsQueryParams, Query()],
    db: Session = Depends(get_db),
) -> PaginatedNewsOut:
    """Retorna uma lista paginada de notícias com suporte a múltiplos filtros.

    Este endpoint permite filtrar notícias por sites específicos, buscar por termos
    no título, aplicar filtros temporais e navegar através de páginas de resultados.

    **Exemplos de uso:**

    - Listar todas: `GET /news`
    - Por sites: `GET /news?sites=veja,globo`
    - Com busca: `GET /news?search=economia`
    - Últimas 24h: `GET /news?time_range=24h`
    - Completo: `GET /news?sites=cnn&search=política&time_range=7d&page=2`

    **Filtro temporal (formato: {número}{unidade}):**
    - Unidades: `h` (horas), `d` (dias), `w` (semanas), `m` (meses)
    - Exemplos: `1h`, `6h`, `24h`, `7d`, `14d`, `2w`, `30d`, `3m`

    **Resposta:**
    - `items`: Lista de notícias da página atual
    - `total`: Total de notícias que correspondem aos filtros
    - `page`: Número da página retornada
    - `page_size`: Tamanho da página usado
    - `pages`: Total de páginas disponíveis
    """
    if params.sites is None or not params.sites.strip():
        slug_list = SUPPORTED_SITE_SLUGS
    else:
        requested = [slug.strip() for slug in params.sites.split(",") if slug.strip()]
        slug_list = [slug for slug in requested if slug in SUPPORTED_SITE_SLUGS]

    if not slug_list:
        return PaginatedNewsOut(
            items=[],
            total=0,
            page=params.page,
            page_size=params.page_size,
            pages=0,
        )

    base_query = (
        db.query(NewsModel)
        .join(SiteModel, NewsModel.site_id == SiteModel.id)
        .filter(SiteModel.slug.in_(slug_list))
        .order_by(NewsModel.scraped_at.desc())
    )

    if params.search is not None and params.search.strip():
        pattern = f"%{params.search.strip()}%"
        base_query = base_query.filter(NewsModel.title.ilike(pattern))

    if params.time_range is not None and params.time_range.strip():
        now = datetime.now(timezone.utc)
        delta = parse_time_range(params.time_range.strip())
        min_scraped_at = now - delta
        base_query = base_query.filter(NewsModel.scraped_at >= min_scraped_at)

    if (total := base_query.count()) == 0:
        return PaginatedNewsOut(
            items=[],
            total=0,
            page=params.page,
            page_size=params.page_size,
            pages=0,
        )

    pages = ceil(total / params.page_size)

    current_page = params.page if params.page <= pages else pages

    items: Sequence[NewsModel] = (
        base_query.offset((current_page - 1) * params.page_size)
        .limit(params.page_size)
        .all()
    )

    return PaginatedNewsOut(
        items=[NewsOut.model_validate(item) for item in items],
        total=total,
        page=current_page,
        page_size=params.page_size,
        pages=pages,
    )
