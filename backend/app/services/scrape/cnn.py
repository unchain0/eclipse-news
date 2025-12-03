from __future__ import annotations

import re

from bs4 import Tag

from .base import ScrapedArticle, Scraper


class CNNScraper(Scraper):
    base_url = "https://www.cnnbrasil.com.br/"
    default_tag = "figure"

    def scrape(self) -> list[ScrapedArticle]:
        figuras = self.fetch_elements()

        articles: list[ScrapedArticle] = []
        for figura in figuras:
            if not (classes := figura.get("class")):
                continue

            class_list = list(classes)
            required_classes = ["group", "flex", "grow", "shrink-0", "h-auto"]
            if not all(cls in class_list for cls in required_classes):
                continue

            figcaption = figura.find("figcaption")
            if figcaption is None or not isinstance(figcaption, Tag):
                continue

            link = figcaption.find("a", href=True)
            if link is None or not isinstance(link, Tag):
                continue

            if not isinstance((url := link.get("href")), str):
                continue

            if (heading := link.find(["h2", "h3"])) is None:
                continue

            raw_title = heading.get_text(strip=True)
            cleaned_title = re.sub(r"^\d+[\s\-\.)]+", "", raw_title).strip()
            if not cleaned_title:
                continue

            articles.append(ScrapedArticle(title=cleaned_title, url=url))

        return articles
