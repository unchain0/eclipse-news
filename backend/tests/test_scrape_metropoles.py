from __future__ import annotations

import pytest
from bs4 import BeautifulSoup, Tag

from app.services.scrape import base as base_module
from app.services.scrape.metropoles import MetropolesScraper

_HTML_METROPOLES_HOME = """
<html>
  <body>
    <a href="https://www.metropoles.com/politica/noticia-1">
      Manchete muito importante sobre politica brasileira
    </a>
    <a href="https://www.metropoles.com/politica/titulo-curto">
      Titulo curto
    </a>
    <a href="https://www.metropoles.com/servico/ignorar">
      Link de servico
    </a>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "a") -> list[Tag]:
    soup = BeautifulSoup(_HTML_METROPOLES_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_metropoles_scraper_matches_news_pattern(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = MetropolesScraper()
    articles = scraper.scrape()

    assert len(articles) == 1
    article = articles[0]

    assert article.url == "https://www.metropoles.com/politica/noticia-1"
    assert article.title.startswith("Manchete muito importante")
