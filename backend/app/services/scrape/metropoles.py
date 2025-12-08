from __future__ import annotations

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class MetropolesScraper(Scraper):
    base_url = "https://www.metropoles.com/"
    default_tag = "a"

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if not isinstance(url := element.get("href"), str):
            return None

        if not url.startswith("https://www.metropoles.com"):
            return None

        if len(path_parts := url.split("/")[3:]) < 2:
            return None

        if "-" not in path_parts[-1]:
            return None

        if not (title := element.get_text().strip()):
            return None

        return ScrapedArticle(title=title, url=url)
