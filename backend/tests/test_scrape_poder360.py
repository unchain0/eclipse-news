from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from app.services.scrape import base as base_module
from app.services.scrape.poder360 import Poder360Scraper

_HTML_PODER360_HOME = """
<html>
  <body>
    <h2 class="box-news-list__subhead">
      <a href="https://www.poder360.com.br/politica/noticia-1">Titulo de noticia longa numero 1</a>
    </h2>
    <h3 class="box-queue__subhead">
      <a href="https://www.poder360.com.br/economia/noticia-2">Titulo de noticia longa numero 2</a>
    </h3>
    <h2 class="outra-classe">
      <a href="https://www.poder360.com.br/ignorar">Ignorar</a>
    </h2>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "h2"):
    soup = BeautifulSoup(_HTML_PODER360_HOME, "html.parser")
    return list(soup.find_all(["h2", "h3"]))


def test_poder360_scraper_filters_by_known_classes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = Poder360Scraper()
    articles = scraper.scrape()

    titles = {article.title for article in articles}
    urls = {article.url for article in articles}

    assert titles == {
        "Titulo de noticia longa numero 1",
        "Titulo de noticia longa numero 2",
    }
    assert urls == {
        "https://www.poder360.com.br/politica/noticia-1",
        "https://www.poder360.com.br/economia/noticia-2",
    }
