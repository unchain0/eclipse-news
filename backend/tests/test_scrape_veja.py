from __future__ import annotations

import pytest
from bs4 import BeautifulSoup, Tag

from app.services.scrape import base as base_module
from app.services.scrape.veja import VejaScraper

_HTML_VEJA_HOME = """
<html>
  <body>
    <a href="https://veja.abril.com.br/politica/noticia-1">
      <h2 class="title">01Manchete sobre politica brasileira</h2>
    </a>
    <a href="https://veja.abril.com.br/mundo/noticia-2">
      <h3 class="title">02Manchete sobre economia mundial</h3>
    </a>
    <a href="https://veja.abril.com.br/economia/noticia-3">
      <h4 class="title">03Manchete sobre tecnologia atual</h4>
    </a>
    <a href="https://veja.abril.com.br/ignorar">
      <h2 class="outra">Ignorar</h2>
    </a>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "a") -> list[Tag]:
    soup = BeautifulSoup(_HTML_VEJA_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_veja_scraper_uses_heading_with_title_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = VejaScraper()
    articles = scraper.scrape()

    titles = {article.title for article in articles}
    urls = {article.url for article in articles}

    assert titles == {
        "Manchete sobre politica brasileira",
        "Manchete sobre economia mundial",
        "Manchete sobre tecnologia atual",
    }
    assert urls == {
        "https://veja.abril.com.br/politica/noticia-1",
        "https://veja.abril.com.br/mundo/noticia-2",
        "https://veja.abril.com.br/economia/noticia-3",
    }
