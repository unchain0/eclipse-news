from __future__ import annotations

import re

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class VejaScraper(Scraper):
    base_url = "https://veja.abril.com.br/"
    default_tag = "a"

    def scrape(self) -> list[ScrapedArticle]:
        noticias = self.fetch_elements()
        tg_class = "title"

        articles: list[ScrapedArticle] = []
        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            title: str | None = None
            url = noticia.get("href")

            for heading in [noticia.h2, noticia.h3, noticia.h4]:
                if heading is None:
                    continue

                tag_class = heading.get("class")
                if tag_class is None:
                    continue

                if tg_class in tag_class:
                    raw_title = heading.get_text().strip()
                    title = re.sub(r"^\d+", "", raw_title).strip()
                    break

            if title and isinstance(url, str):
                articles.append(ScrapedArticle(title=title, url=url))

        return articles
