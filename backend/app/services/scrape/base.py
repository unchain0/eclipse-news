from __future__ import annotations

from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import BaseModel, Field

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
)
HEADERS = {"User-Agent": USER_AGENT}


class ScrapedArticle(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)


class Scraper(ABC):
    base_url: str
    default_tag: str = "a"
    min_title_length: int = 20
    deduplicate_urls: bool = True

    def fetch_elements(
        self,
        *,
        url: str | None = None,
        tag: str | None = None,
    ) -> list[Tag] | None:
        """
        Fetches all elements with the given tag from the given URL.

        Args:
            url: The URL to fetch elements from. Defaults to None.
            tag: The tag to fetch elements with. Defaults to None.

        Returns:
            A list of Tag objects, or None if the fetch fails.
        """
        target_url = url or self.base_url
        target_tag = tag or self.default_tag
        return fetch_elements(target_url, tag=target_tag)

    def scrape(self) -> list[ScrapedArticle]:
        """
        Scrapes articles from the site using the template method pattern.

        Returns:
            A list of ScrapedArticle objects.
        """
        if (elements := self.get_elements()) is None:
            return []

        articles: list[ScrapedArticle] = []
        seen_urls: set[str] = set()

        for element in elements:
            if (article := self.extract_article(element)) is None:
                continue

            if len(article.title) < self.min_title_length:
                continue

            if " " not in article.title:
                continue

            if self.deduplicate_urls and article.url in seen_urls:
                continue

            seen_urls.add(article.url)
            articles.append(article)

        return articles

    def get_elements(self) -> list[Tag] | None:
        """
        Gets elements to scrape. Override for custom element fetching.

        Returns:
            A list of Tag objects, or None if the fetch fails.
        """
        return self.fetch_elements()

    @abstractmethod
    def extract_article(self, element: Tag) -> ScrapedArticle | None:
        """
        Extracts an article from an element.

        Args:
            element: The Tag element to extract the article from.

        Returns:
            A ScrapedArticle if extraction succeeds, None otherwise.
        """
        ...


def fetch_elements(url: str, tag: str = "a") -> list[Tag] | None:
    """
    Fetches all elements with the given tag from the given URL.

    Args:
        url (str): The URL to fetch elements from.
        tag (str, optional): The tag to fetch elements with. Defaults to "a".

    Returns:
        list[Tag] | None: A list of Tag objects, or None if the fetch fails.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error fetching {url}: {exc}", url=url, exc=exc)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.find_all(tag)
    return [el for el in elements if isinstance(el, Tag)]
