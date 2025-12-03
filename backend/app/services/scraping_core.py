from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
)
HEADERS = {"User-Agent": USER_AGENT}

SUPPORTED_SITE_SLUGS = [
    "veja",
    # "r7",
    "globo",
    "cnn",
    "livecoins",
    "poder360",
]

SITE_DISPLAY_NAMES: dict[str, str] = {
    "veja": "VEJA",
    "r7": "R7",
    "globo": "Globo",
    "cnn": "CNN Brasil",
    "livecoins": "Livecoins",
    "poder360": "Poder360",
}


@dataclass
class ScrapedArticle:
    title: str
    url: str


def _fetch_elements(url: str, tag: str = "a") -> list[Tag]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error fetching {url}: {exc}", url=url, exc=exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.find_all(tag)
    return [el for el in elements if isinstance(el, Tag)]


def _scrape_globo() -> list[ScrapedArticle]:
    noticias = _fetch_elements("https://www.globo.com/", tag="a")
    tg_classes = [
        "post__title",
        "post-multicontent__link--title__text",
        "post__header__text__title",
    ]

    articles: list[ScrapedArticle] = []
    candidate_urls: set[str] = set()

    for noticia in noticias:
        if noticia.h2 is None:
            continue

        h2_class = noticia.h2.get("class")
        if h2_class is None:
            continue

        if any(class_name in tg_classes for class_name in h2_class):
            url = noticia.get("href")
            if isinstance(url, str):
                candidate_urls.add(url)

    # Para cada URL candidata, busca o título diretamente na página do artigo
    for url in candidate_urls:
        headings = _fetch_elements(url, tag="h1")
        title: str | None = None

        for heading in headings:
            raw_title = heading.get_text().strip()
            if raw_title:
                title = raw_title
                break

        if title:
            articles.append(ScrapedArticle(title=title, url=url))

    return articles


def _scrape_cnn() -> list[ScrapedArticle]:
    figuras = _fetch_elements("https://www.cnnbrasil.com.br/", tag="figure")

    articles: list[ScrapedArticle] = []
    for figura in figuras:
        classes = figura.get("class")
        if not classes:
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

        url = link.get("href")
        if not isinstance(url, str):
            continue

        heading = link.find(["h2", "h3"])
        if heading is None:
            continue

        raw_title = heading.get_text(strip=True)
        cleaned_title = re.sub(r"^\d+[\s\-\.)]+", "", raw_title).strip()
        if not cleaned_title:
            continue

        articles.append(ScrapedArticle(title=cleaned_title, url=url))

    return articles


def _scrape_veja() -> list[ScrapedArticle]:
    noticias = _fetch_elements("https://veja.abril.com.br/", tag="a")
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


def _scrape_r7() -> list[ScrapedArticle]:
    noticias = _fetch_elements("https://www.r7.com/", tag="h3")

    articles: list[ScrapedArticle] = []
    for noticia in noticias:
        if noticia.a is None:
            continue

        title = noticia.a.get_text().strip()
        url = noticia.a.get("href")
        if isinstance(url, str):
            articles.append(ScrapedArticle(title=title, url=url))

    return articles


def _scrape_livecoins() -> list[ScrapedArticle]:
    noticias = _fetch_elements("https://livecoins.com.br/", tag="a")
    tg_class = "bookmark"
    processed_urls: set[str] = set()

    articles: list[ScrapedArticle] = []
    for noticia in noticias:
        tag_class = noticia.get("rel")
        if tag_class is None:
            continue

        if tg_class in tag_class:
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


def _scrape_poder360() -> list[ScrapedArticle]:
    noticias_h2 = _fetch_elements("https://www.poder360.com.br/", tag="h2")
    noticias_h3 = _fetch_elements("https://www.poder360.com.br/", tag="h3")
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

        h_class = noticia.get("class")
        if not h_class:
            continue

        if not any(class_name in tg_classes for class_name in h_class):
            continue

        title = noticia.get_text().strip()
        url = noticia.a.get("href")
        if isinstance(url, str):
            articles.append(ScrapedArticle(title=title, url=url))

    return articles


SCRAPER_MAP: dict[str, Callable[[], list[ScrapedArticle]]] = {
    "globo": _scrape_globo,
    "cnn": _scrape_cnn,
    "veja": _scrape_veja,
    "r7": _scrape_r7,
    "livecoins": _scrape_livecoins,
    "poder360": _scrape_poder360,
}


def scrape_site(slug: str) -> list[ScrapedArticle]:
    scraper = SCRAPER_MAP.get(slug)
    if scraper is None:
        logger.warning("No scraper configured for site slug: {slug}", slug=slug)
        return []

    logger.info("Scraping site {slug}", slug=slug)
    return scraper()
