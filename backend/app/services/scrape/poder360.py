from __future__ import annotations

from bs4 import Tag

from .base import ScrapedArticle, Scraper

_VALID_CLASSES = [
    "box-news-list__highlight-subhead",
    "box-news-list__subhead",
    "box-queue__subhead",
]


class Poder360Scraper(Scraper):
    base_url = "https://www.poder360.com.br/"
    default_tag = "h2"
    min_title_length = 30
    allowed_domains = ["poder360.com.br", "www.poder360.com.br"]

    def get_elements(self) -> list[Tag] | None:
        h2_elements = self.fetch_elements(tag="h2") or []
        h3_elements = self.fetch_elements(tag="h3") or []
        return h2_elements + h3_elements or None

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if (link := element.a) is None:
            return None

        if not (h_class := element.get("class")) or not any(
            cls in _VALID_CLASSES for cls in h_class
        ):
            return None

        if not isinstance(url := link.get("href"), str):
            return None

        return ScrapedArticle(title=element.get_text().strip(), url=url)
