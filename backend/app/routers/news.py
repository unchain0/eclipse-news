from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Sequence

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NewsModel, SiteModel
from app.schemas import NewsOut, PaginatedNewsOut
from app.services.scraping_core import SUPPORTED_SITE_SLUGS

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=PaginatedNewsOut)
def list_news(
    sites: str | None = Query(
        None,
        description="Comma-separated list of site slugs, e.g. veja,globo,cnn",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(
        None,
        description="Search term to filter news by title",
        min_length=1,
        max_length=200,
    ),
    time_range: str | None = Query(
        None,
        description=(
            "Relative time range for scraped_at. Supported values: "
            "'1h', '6h', '24h', '7d'"
        ),
        min_length=2,
        max_length=3,
    ),
    db: Session = Depends(get_db),
) -> PaginatedNewsOut:
    if sites is None or not sites.strip():
        slug_list = SUPPORTED_SITE_SLUGS
    else:
        requested = [slug.strip() for slug in sites.split(",") if slug.strip()]
        slug_list = [slug for slug in requested if slug in SUPPORTED_SITE_SLUGS]

    if not slug_list:
        return PaginatedNewsOut(
            items=[], total=0, page=page, page_size=page_size, pages=0
        )

    base_query = (
        db.query(NewsModel)
        .join(SiteModel, NewsModel.site_id == SiteModel.id)
        .filter(SiteModel.slug.in_(slug_list))
        .order_by(NewsModel.scraped_at.desc())
    )

    if search is not None and search.strip():
        pattern = f"%{search.strip()}%"
        base_query = base_query.filter(NewsModel.title.ilike(pattern))

    if time_range is not None and time_range.strip():
        now = datetime.now(timezone.utc)
        delta: timedelta | None = None

        match time_range:
            case "1h":
                delta = timedelta(hours=1)
            case "6h":
                delta = timedelta(hours=6)
            case "24h":
                delta = timedelta(hours=24)
            case "7d":
                delta = timedelta(days=7)

        if delta is not None:
            min_scraped_at = now - delta
            base_query = base_query.filter(NewsModel.scraped_at >= min_scraped_at)

    if (total := base_query.count()) == 0:
        return PaginatedNewsOut(
            items=[], total=0, page=page, page_size=page_size, pages=0
        )

    pages = ceil(total / page_size)

    current_page = page if page <= pages else pages

    items: Sequence[NewsModel] = (
        base_query.offset((current_page - 1) * page_size).limit(page_size).all()
    )

    return PaginatedNewsOut(
        items=[NewsOut.model_validate(item) for item in items],
        total=total,
        page=current_page,
        page_size=page_size,
        pages=pages,
    )
