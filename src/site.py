from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag


@dataclass
class News:
    title: str
    url: str


class Site:
    def __init__(self, site: str):
        self.site = site
        self.news: list[News] = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }

    def update_news(self):
        match self.site.lower():
            case "globo":
                self.scrape_globo()
            case "cnn":
                self.scrape_cnn()
            case "veja":
                self.scrape_veja()
            case "r7":
                self.scrape_r7()

    def _get_noticias(self, url: str, tag: str = "a"):
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find_all(tag)

    def scrape_globo(self):
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
                title = noticia.get_text(strip=True)
                url = noticia.get("href")
                if isinstance(url, str):
                    self.news.append(News(title=title, url=url))

    def scrape_cnn(self):
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
                title = noticia.get_text(strip=True)
                url = noticia.get("href")
                if isinstance(url, str):
                    self.news.append(News(title=title, url=url))

    def scrape_veja(self):
        noticias = self._get_noticias(
            "https://veja.abril.com.br/",
            tag="a",
        )
        tg_class = "title"

        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            title = None
            for tag in [noticia.h2, noticia.h3, noticia.h4]:
                if tag is None:
                    continue

                tag_class = tag.get("class")
                if tag_class is None:
                    continue

                if tg_class in tag_class:
                    raw_title = noticia.get_text(strip=True)
                    cleaned_title = " ".join(raw_title.split())
                    title = cleaned_title
                    break

            if title:
                url = noticia.get("href")
                if isinstance(url, str):
                    self.news.append(News(title=title, url=url))

    def scrape_r7(self):
        noticias = self._get_noticias(
            "https://www.r7.com/",
            tag="h3",
        )

        for noticia in noticias:
            if not isinstance(noticia, Tag):
                continue

            if noticia.a is None:
                continue

            title = noticia.a.get_text(strip=True)
            url = noticia.a.get("href")
            if isinstance(url, str):
                self.news.append(News(title=title, url=url))
