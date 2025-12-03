from __future__ import annotations

from .base import ScrapedArticle, Scraper


class LivecoinsScraper(Scraper):
    base_url = "https://livecoins.com.br/"
    default_tag = "a"

    def scrape(self) -> list[ScrapedArticle]:
        noticias = self.fetch_elements()
        tg_class = "bookmark"
        processed_urls: set[str] = set()

        articles: list[ScrapedArticle] = []
        for noticia in noticias:
            if (tag_class := noticia.get("rel")) is None:
                continue

            if tg_class not in tag_class:
                continue

            title = noticia.get("title")
            url = noticia.get("href")
            if (
                isinstance(url, str)
                and isinstance(title, str)
                and url not in processed_urls
            ):
                articles.append(ScrapedArticle(title=title.strip(), url=url))
                processed_urls.add(url)

        return articles
