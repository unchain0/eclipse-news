import logging
import re

import requests
from bs4 import BeautifulSoup, Tag

from scripts.log_config import setup_logging
from scripts.utils import Article

setup_logging()


class Site:
    def __init__(self, site_name: str):
        self.site = site_name
        self.list_news: list[Article] = []
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) "
                "Gecko/20100101 Firefox/137.0"
            )
        }

    def update_news(self):
        match self.site.lower():
            case "globo":
                self._scrape_globo()
            case "cnn":
                self._scrape_cnn()
            case "veja":
                self._scrape_veja()
            case "r7":
                self._scrape_r7()
            case "livecoins":
                self._scrape_livecoins()
            case "poder360":
                self._scrape_poder360()

    def _get_noticias(self, url: str, tag: str = "a"):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.find_all(tag)
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao buscar notícias de {url}: {e}")
            return []

    def _scrape_globo(self) -> None:
        noticias = self._get_noticias(
            "https://www.globo.com/",
            tag="a",
        )
        tg_classes = [
            "post__title",
            "post-multicontent__link--title__text",
            "post__header__text__title",
        ]

        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            if noticia.h2 is None:
                continue

            h2_class = noticia.h2.get("class")
            if h2_class is None:
                continue

            if any(class_name in tg_classes for class_name in h2_class):
                title = noticia.get_text().strip()
                url = noticia.get("href")
                if isinstance(url, str):
                    self.list_news.append(Article(title=title, url=url))

    def _scrape_cnn(self) -> None:
        noticias = self._get_noticias(
            "https://www.cnnbrasil.com.br/",
            tag="a",
        )
        tg_class = "block__news__title"

        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            if noticia.h3 is None:
                continue

            h3_class = noticia.h3.get("class")
            if h3_class is None:
                continue

            if tg_class in h3_class:
                title = noticia.get_text().strip()
                url = noticia.get("href")
                if isinstance(url, str):
                    self.list_news.append(Article(title=title, url=url))

    def _scrape_veja(self) -> None:
        noticias = self._get_noticias(
            "https://veja.abril.com.br/",
            tag="a",
        )
        tg_class = "title"
        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            title = None
            url = noticia.get("href")

            for tag in [noticia.h2, noticia.h3, noticia.h4]:
                if tag is None:
                    continue

                tag_class = tag.get("class")
                if tag_class is None:
                    continue

                if tg_class in tag_class:
                    title = re.sub(r"^\d+", "", tag.get_text().strip())
                    break

            if title:
                if isinstance(url, str):
                    self.list_news.append(Article(title=title, url=url))

    def _scrape_r7(self) -> None:
        noticias = self._get_noticias(
            "https://www.r7.com/",
            tag="h3",
        )

        # TODO: Corrigir algumas noticias que não estão sendo pegas
        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            if noticia.a is None:
                continue

            title = noticia.a.get_text().strip()
            url = noticia.a.get("href")
            if isinstance(url, str):
                self.list_news.append(Article(title=title, url=url))

    def _scrape_livecoins(self) -> None:
        noticias = self._get_noticias(
            "https://livecoins.com.br/",
            tag="a",
        )
        tg_class = "bookmark"
        processed_urls = set()

        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            tag_class = noticia.get("rel")
            if tag_class is None:
                continue

            if tg_class in tag_class:
                title = noticia.get("title")
                url = noticia.get("href")

                if isinstance(url, str) and isinstance(title, str):
                    if url not in processed_urls:
                        self.list_news.append(Article(title=title.strip(), url=url))
                        processed_urls.add(url)

    def _scrape_poder360(self) -> None:
        noticias = self._get_noticias(
            "https://www.poder360.com.br/",
            tag="h2",
        ) + self._get_noticias(
            "https://www.poder360.com.br/",
            tag="h3",
        )
        tg_classes = [
            "box-news-list__highlight-subhead",
            "box-news-list__subhead",
            "box-queue__subhead",
        ]

        for noticia in noticias:
            if not isinstance(noticia, Tag) or noticia.a is None:
                continue

            if not (h_class := noticia.get("class")):
                continue

            if not any(class_name in tg_classes for class_name in h_class):
                continue

            title = noticia.get_text().strip()
            url = noticia.a.get("href")
            if isinstance(url, str):
                self.list_news.append(Article(title=title, url=url))
