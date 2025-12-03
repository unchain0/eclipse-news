from __future__ import annotations

from .base import ScrapedArticle, Scraper


class MetropolesScraper(Scraper):
    base_url = "https://www.metropoles.com/"
    default_tag = "a"

    def scrape(self) -> list[ScrapedArticle]:
        noticias = self.fetch_elements()

        articles: list[ScrapedArticle] = []
        processed_urls: set[str] = set()

        for noticia in noticias:
            if not isinstance((url := noticia.get("href")), str):
                continue

            if not url.startswith("https://www.metropoles.com"):
                continue

            parts = url.split("/")
            path_parts = parts[3:]
            if len(path_parts) < 2:
                continue

            last_segment = path_parts[-1]
            if "-" not in last_segment:
                continue

            raw_title = noticia.get_text().strip()
            if " " not in raw_title:
                continue

            if url in processed_urls:
                continue

            articles.append(ScrapedArticle(title=raw_title, url=url))
            processed_urls.add(url)

        return articles
