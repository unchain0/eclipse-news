from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from app.services.scrape import base as base_module
from app.services.scrape.livecoins import LivecoinsScraper

_HTML_LIVECOINS_HOME = """
<html>
  <body>
    <a href="https://livecoins.com.br/noticia-1" rel="bookmark" title="Noticia 1"></a>
    <a href="https://livecoins.com.br/noticia-2" rel="bookmark" title="Noticia 2"></a>
    <a href="https://livecoins.com.br/ignorar" rel="nofollow" title="Ignorar"></a>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "a"):
    soup = BeautifulSoup(_HTML_LIVECOINS_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_livecoins_scraper_filters_by_rel_bookmark(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = LivecoinsScraper()
    articles = scraper.scrape()

    titles = {article.title for article in articles}
    urls = {article.url for article in articles}

    assert titles == {"Noticia 1", "Noticia 2"}
    assert urls == {
        "https://livecoins.com.br/noticia-1",
        "https://livecoins.com.br/noticia-2",
    }
