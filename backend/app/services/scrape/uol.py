from __future__ import annotations

from urllib.parse import urlparse

from .base import ScrapedArticle, Scraper


class UOLScraper(Scraper):
    base_url = "https://www.uol.com.br/"
    default_tag = "a"

    def scrape(self) -> list[ScrapedArticle]:
        noticias = self.fetch_elements()

        articles: list[ScrapedArticle] = []
        processed_urls: set[str] = set()

        for noticia in noticias:
            if not isinstance((url := noticia.get("href")), str):
                continue

            if not url.startswith("http"):
                continue

            parsed = urlparse(url)

            if "uol.com.br" not in parsed.netloc:
                continue

            path_parts = [part for part in parsed.path.split("/") if part]
            if len(path_parts) < 3:
                continue

            if not any(len(part) == 4 and part.isdigit() for part in path_parts):
                continue

            last_segment = path_parts[-1]
            if "-" not in last_segment:
                continue

            raw_title = noticia.get_text(separator="\n").strip()
            lines = [line.strip() for line in raw_title.splitlines() if line.strip()]
            if not lines:
                continue

            long_lines = [line for line in lines if len(line) >= 20]
            if not long_lines:
                continue

            title = long_lines[-1]

            if " " not in title:
                continue

            if url in processed_urls:
                continue

            articles.append(ScrapedArticle(title=title, url=url))
            processed_urls.add(url)

        return articles
