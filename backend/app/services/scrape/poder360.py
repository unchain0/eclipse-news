from __future__ import annotations

from .base import ScrapedArticle, Scraper


class Poder360Scraper(Scraper):
    base_url = "https://www.poder360.com.br/"
    default_tag = "h2"

    def scrape(self) -> list[ScrapedArticle]:
        noticias_h2 = self.fetch_elements(tag="h2")
        noticias_h3 = self.fetch_elements(tag="h3")
        noticias = noticias_h2 + noticias_h3

        tg_classes = [
            "box-news-list__highlight-subhead",
            "box-news-list__subhead",
            "box-queue__subhead",
        ]

        articles: list[ScrapedArticle] = []
        for noticia in noticias:
            if noticia.a is None:
                continue

            if not (h_class := noticia.get("class")):
                continue

            if not any(class_name in tg_classes for class_name in h_class):
                continue

            if len((title := noticia.get_text().strip())) < 30:
                continue

            if isinstance((url := noticia.a.get("href")), str):
                articles.append(ScrapedArticle(title=title, url=url))

        return articles
