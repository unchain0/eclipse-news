from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SiteOut(BaseModel):
    id: int
    slug: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class NewsOut(BaseModel):
    id: int
    site_id: int
    title: str
    url: str
    scraped_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedNewsOut(BaseModel):
    items: list[NewsOut]
    total: int
    page: int
    page_size: int
    pages: int
