from __future__ import annotations

from urllib.parse import urlparse

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class UOLScraper(Scraper):
    base_url = "https://www.uol.com.br/"
    default_tag = "a"
    min_title_length = 30

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if not isinstance(url := element.get("href"), str) or not url.startswith("http"):
            return None

        if "uol.com.br" not in (parsed := urlparse(url)).netloc:
            return None

        if len(path_parts := [p for p in parsed.path.split("/") if p]) < 3:
            return None

        if not any(len(part) == 4 and part.isdigit() for part in path_parts):
            return None

        if "-" not in path_parts[-1]:
            return None

        raw_title = element.get_text(separator="\n").strip()
        lines = [line.strip() for line in raw_title.splitlines() if line.strip()]
        if not (long_lines := [line for line in lines if len(line) >= 30]):
            return None

        return ScrapedArticle(title=long_lines[-1], url=url)
