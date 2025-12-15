from __future__ import annotations

from typing import Callable

from loguru import logger

from app.services.scrape.base import ScrapedArticle
from app.services.scrape.cnn import CNNScraper
from app.services.scrape.globo import GloboScraper
from app.services.scrape.livecoins import LivecoinsScraper
from app.services.scrape.metropoles import MetropolesScraper
from app.services.scrape.poder360 import Poder360Scraper
from app.services.scrape.uol import UOLScraper
from app.services.scrape.veja import VejaScraper

SUPPORTED_SITE_SLUGS = [
    "veja",
    "globo",
    "cnn",
    "livecoins",
    "poder360",
    "uol",
    "metropoles",
]

SITE_DISPLAY_NAMES: dict[str, str] = {
    "veja": "VEJA",
    "globo": "Globo",
    "cnn": "CNN Brasil",
    "livecoins": "Livecoins",
    "poder360": "Poder360",
    "uol": "UOL",
    "metropoles": "Metrópoles",
}

SCRAPER_MAP: dict[str, Callable[[], list[ScrapedArticle]]] = {
    "globo": GloboScraper().scrape,
    "cnn": CNNScraper().scrape,
    "veja": VejaScraper().scrape,
    "livecoins": LivecoinsScraper().scrape,
    "poder360": Poder360Scraper().scrape,
    "uol": UOLScraper().scrape,
    "metropoles": MetropolesScraper().scrape,
}


def scrape_site(slug: str) -> list[ScrapedArticle]:
    """
    Scrape a site based on its slug.

    Args:
        slug: The slug of the site to scrape.

    Returns:
        A list of scraped articles.

    Notes:
        If no scraper is configured for the site, an empty list is returned.
    """
    scraper = SCRAPER_MAP.get(slug)
    if scraper is None:
        logger.warning("No scraper configured for site slug: {slug}", slug=slug)
        return []

    logger.info("Scraping site {slug}", slug=slug)
    return scraper()
