from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from app.services.scrape import base as base_module
from app.services.scrape.globo import GloboScraper

_HTML_GLOBO_HOME = """
<html>
  <body>
    <a href="https://www.globo.com/noticia1">
      <h2 class="post__title">Titulo de noticia bem longa numero 1</h2>
    </a>
    <a href="https://www.globo.com/noticia2">
      <h2 class="post-multicontent__link--title__text">Titulo de noticia bem longa numero 2</h2>
    </a>
    <a href="https://www.globo.com/ignorar">
      <h2 class="outra-classe">Ignorar</h2>
    </a>
    <a href="https://www.globo.com/sem-h2">
      Sem h2
    </a>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "a"):
    soup = BeautifulSoup(_HTML_GLOBO_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_globo_scraper_extracts_articles_from_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = GloboScraper()
    articles = scraper.scrape()

    titles = {article.title for article in articles}
    urls = {article.url for article in articles}

    assert titles == {
        "Titulo de noticia bem longa numero 1",
        "Titulo de noticia bem longa numero 2",
    }
    assert urls == {
        "https://www.globo.com/noticia1",
        "https://www.globo.com/noticia2",
    }
