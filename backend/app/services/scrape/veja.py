from __future__ import annotations

import re

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class VejaScraper(Scraper):
    base_url = "https://veja.abril.com.br/"
    default_tag = "a"
    allowed_domains = ["veja.abril.com.br", "abril.com.br"]

    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        if not isinstance(url := element.get("href"), str):
            return None

        for heading in [element.h2, element.h3, element.h4]:
            if heading is None:
                continue

            if (tag_class := heading.get("class")) is None or "title" not in tag_class:
                continue

            raw_title = heading.get_text().strip()
            title = re.sub(r"^\d+", "", raw_title).strip()
            return ScrapedArticle(title=title, url=url)

        return None
