from __future__ import annotations

import re

from bs4 import Tag

from .base import ScrapedArticle, Scraper

_REQUIRED_CLASSES = ["group", "flex", "grow", "shrink-0", "h-auto"]


class CNNScraper(Scraper):
    base_url = "https://www.cnnbrasil.com.br/"
    default_tag = "figure"
    allowed_domains = ["cnnbrasil.com.br", "www.cnnbrasil.com.br"]

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if not (classes := element.get("class")) or not all(
            cls in classes for cls in _REQUIRED_CLASSES
        ):
            return None

        if (figcaption := element.find("figcaption")) is None or not isinstance(
            figcaption, Tag
        ):
            return None

        if (link := figcaption.find("a", href=True)) is None or not isinstance(
            link, Tag
        ):
            return None

        if not isinstance(url := link.get("href"), str):
            return None

        if (heading := link.find(["h2", "h3"])) is None:
            return None

        raw_title = heading.get_text(strip=True)
        if not (title := re.sub(r"^\d+[\s\-\.)]+", "", raw_title).strip()):
            return None

        return ScrapedArticle(title=title, url=url)
