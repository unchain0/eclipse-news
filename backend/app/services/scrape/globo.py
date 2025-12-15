from __future__ import annotations

from bs4 import Tag

from .base import ScrapedArticle, Scraper

_VALID_CLASSES = [
    "post__title",
    "post-multicontent__link--title__text",
    "post__header__text__title",
]


class GloboScraper(Scraper):
    base_url = "https://www.globo.com/"
    default_tag = "a"
    min_title_length = 30
    allowed_domains = ["globo.com", "www.globo.com"]

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if (h2 := element.h2) is None:
            return None

        if (h2_class := h2.get("class")) is None or not any(
            cls in _VALID_CLASSES for cls in h2_class
        ):
            return None

        if not isinstance(url := element.get("href"), str):
            return None

        return ScrapedArticle(title=h2.get_text().strip(), url=url)
