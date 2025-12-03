from __future__ import annotations

from .base import ScrapedArticle, Scraper


class GloboScraper(Scraper):
    base_url = "https://www.globo.com/"
    default_tag = "a"

    def scrape(self) -> list[ScrapedArticle]:
        noticias = self.fetch_elements()
        tg_classes = [
            "post__title",
            "post-multicontent__link--title__text",
            "post__header__text__title",
        ]

        articles: list[ScrapedArticle] = []
        processed_urls: set[str] = set()

        for noticia in noticias:
            if noticia.h2 is None:
                continue

            if (h2_class := noticia.h2.get("class")) is None:
                continue

            if not any(class_name in tg_classes for class_name in h2_class):
                continue

            if not isinstance((url := noticia.get("href")), str):
                continue

            if url in processed_urls:
                continue

            if len((title := noticia.h2.get_text().strip())) < 30:
                continue

            if " " not in title:
                continue

            articles.append(ScrapedArticle(title=title, url=url))
            processed_urls.add(url)

        return articles
