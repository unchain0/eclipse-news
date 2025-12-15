from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def get_random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


class ScrapedArticle(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)


class Scraper(ABC):
    base_url: str
    default_tag: str = "a"
    min_title_length: int = 20
    deduplicate_urls: bool = True
    allowed_domains: list[str] = []

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
        return fetch_elements(
            target_url, tag=target_tag, allowed_domains=self.allowed_domains
        )

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


def validate_url(url: str, allowed_domains: list[str] | None = None) -> bool:
    """
    Validates URL to prevent SSRF attacks.

    Args:
        url: The URL to validate
        allowed_domains: List of allowed domains for this specific scraper

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            logger.warning("Invalid URL scheme: {scheme}", scheme=parsed.scheme)
            return False

        hostname = parsed.hostname
        if not hostname:
            logger.warning("No hostname in URL: {url}", url=url)
            return False

        blocked_hosts = {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "::",
            "0:0:0:0:0:0:0:1",
        }

        if hostname in blocked_hosts:
            logger.warning("Blocked hostname: {hostname}", hostname=hostname)
            return False

        if hostname.startswith(
            (
                "192.168.",
                "10.",
                "172.16.",
                "172.17.",
                "172.18.",
                "172.19.",
                "172.20.",
                "172.21.",
                "172.22.",
                "172.23.",
                "172.24.",
                "172.25.",
                "172.26.",
                "172.27.",
                "172.28.",
                "172.29.",
                "172.30.",
                "172.31.",
            )
        ):
            logger.warning("Private IP range: {hostname}", hostname=hostname)
            return False

        domains_to_check = allowed_domains or []
        if settings.allowed_domains:
            domains_to_check.extend(settings.allowed_domains)

        if domains_to_check:
            domain_allowed = any(
                hostname == domain or hostname.endswith(f".{domain}")
                for domain in domains_to_check
            )
            if not domain_allowed:
                logger.warning("Domain not in allowlist: {hostname}", hostname=hostname)
                return False

        return True

    except Exception as exc:
        logger.error("URL validation error: {exc}", exc=exc)
        return False


def fetch_elements(
    url: str, tag: str = "a", allowed_domains: list[str] | None = None
) -> list[Tag] | None:
    """
    Fetches all elements with the given tag from the given URL.

    Args:
        url (str): The URL to fetch elements from.
        tag (str, optional): The tag to fetch elements with. Defaults to "a".
        allowed_domains (list[str] | None): List of allowed domains for this scraper.

    Returns:
        list[Tag] | None: A list of Tag objects, or None if the fetch fails.
    """
    if not validate_url(url, allowed_domains):
        logger.error("URL validation failed: {url}", url=url)
        return None

    for attempt in range(settings.max_retries + 1):
        try:
            headers = get_random_headers()
            response = requests.get(
                url, headers=headers, timeout=settings.request_timeout_seconds
            )
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt == settings.max_retries:
                logger.error(
                    "Error fetching {url} after {max_retries} attempts: {exc}",
                    url=url,
                    max_retries=settings.max_retries,
                    exc=exc,
                )
                return None

            delay = settings.retry_delay_seconds * (2**attempt) + random.uniform(0, 1)
            logger.warning(
                "Attempt {attempt} failed for {url}, retrying in {delay:.2f}s: {exc}",
                attempt=attempt + 1,
                url=url,
                delay=delay,
                exc=exc,
            )
            time.sleep(delay)

    soup = BeautifulSoup(response.text, "html.parser")
    elements = soup.find_all(tag)
    return [el for el in elements if isinstance(el, Tag)]
