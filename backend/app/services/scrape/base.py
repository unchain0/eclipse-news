from __future__ import annotations

from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import BaseModel

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
)
HEADERS = {"User-Agent": USER_AGENT}


class ScrapedArticle(BaseModel):
    title: str
    url: str


class Scraper(ABC):
    base_url: str
    default_tag: str = "a"

    def fetch_elements(
        self,
        *,
        url: str | None = None,
        tag: str | None = None,
    ) -> list[Tag]:
        """
        Fetches all elements with the given tag from the given URL.

        Args:
            url: The URL to fetch elements from. Defaults to None.
            tag: The tag to fetch elements with. Defaults to None.

        Returns:
            A list of Tag objects.
        """
        target_url = url or self.base_url
        target_tag = tag or self.default_tag
        return fetch_elements(target_url, tag=target_tag)

    @abstractmethod
    def scrape(self) -> list[ScrapedArticle]:
        """
        Return a list of scraped articles for this site.

        Returns:
            A list of ScrapedArticle objects.
        """
        raise NotImplementedError


def fetch_elements(url: str, tag: str = "a") -> list[Tag]:
    """
    Fetches all elements with the given tag from the given URL.

    Args:
        url (str): The URL to fetch elements from.
        tag (str, optional): The tag to fetch elements with. Defaults to "a".

    Returns:
        list[Tag]: A list of Tag objects.

    Raises:
        requests.RequestException: If there is an error while fetching the URL.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error fetching {url}: {exc}", url=url, exc=exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.find_all(tag)
    return [el for el in elements if isinstance(el, Tag)]
