from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SiteBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50, strict=True)
    name: str = Field(..., min_length=1, max_length=100, strict=True)


class SiteCreate(SiteBase):
    pass


class SiteOut(SiteBase):
    id: int = Field(..., strict=True)
    created_at: datetime = Field(..., strict=True)

    model_config = ConfigDict(from_attributes=True)


class SiteStats(BaseModel):
    site_slug: str = Field(..., strict=True)
    total_news: int = Field(..., strict=True)
    last_scraped_at: Optional[datetime] = Field(None, strict=True)


class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, strict=True)
    url: str = Field(..., min_length=1, max_length=1000, strict=True)


class NewsCreate(NewsBase):
    site_id: int = Field(..., strict=True)


class NewsOut(NewsBase):
    id: int = Field(..., strict=True)
    site_id: int = Field(..., strict=True)
    scraped_at: datetime = Field(..., strict=True)

    model_config = ConfigDict(from_attributes=True)


class NewsWithSite(NewsOut):
    site: SiteOut


class NewsFilter(BaseModel):
    sites: Optional[List[str]] = Field(
        None, description="List of site slugs to filter by", strict=True
    )
    search: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Search term", strict=True
    )
    time_range: Optional[str] = Field(
        None,
        pattern=r"^(1h|6h|24h|7d)$",
        description="Relative time range",
        strict=True,
    )
    start_date: Optional[datetime] = Field(None, strict=True)
    end_date: Optional[datetime] = Field(None, strict=True)


class NewsQueryParams(BaseModel):
    """Parâmetros de query para listagem e filtro de notícias.

    Modelo Pydantic para validação automática de query parameters.

    Attributes:
        sites: Lista de slugs de sites separados por vírgula.
        search: Termo de busca para filtrar notícias pelo título.
        time_range: Filtro temporal dinâmico no formato '{número}{unidade}'.
        page: Número da página para paginação.
        page_size: Quantidade de itens por página.
    """

    sites: str | None = Field(
        None,
        description="Lista de slugs de sites separados por vírgula (ex: veja,globo,cnn)",
    )
    search: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Termo de busca para filtrar notícias pelo título (case-insensitive)",
    )
    time_range: str | None = Field(
        None,
        pattern=r"^\d+[hdwm]$",
        description=(
            "Filtro temporal no formato '{número}{unidade}'. "
            "Unidades: h (horas), d (dias), w (semanas), m (meses). "
            "Exemplos: 1h, 6h, 24h, 7d, 2w, 3m"
        ),
    )
    page: int = Field(
        1,
        ge=1,
        description="Número da página (mínimo: 1)",
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Quantidade de itens por página (1-100)",
    )


class PaginatedNewsOut(BaseModel):
    items: List[NewsOut] = Field(..., strict=True)
    total: int = Field(..., strict=True)
    page: int = Field(..., strict=True)
    page_size: int = Field(..., strict=True)
    pages: int = Field(..., strict=True)
