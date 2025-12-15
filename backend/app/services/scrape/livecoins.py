from __future__ import annotations

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class LivecoinsScraper(Scraper):
    base_url = "https://livecoins.com.br/"
    default_tag = "a"
    allowed_domains = ["livecoins.com.br", "www.livecoins.com.br"]

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if (rel := element.get("rel")) is None or "bookmark" not in rel:
            return None

        if not isinstance(url := element.get("href"), str):
            return None

        if not isinstance(title := element.get("title"), str):
            return None

        return ScrapedArticle(title=title.strip(), url=url)
