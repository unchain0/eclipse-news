from __future__ import annotations

import pytest
from bs4 import BeautifulSoup, Tag

from app.services.scrape import base as base_module
from app.services.scrape.uol import UOLScraper

_HTML_UOL_HOME = """
<html>
  <body>
    <!-- Noticia valida: url com ano e slug, titulo em duas linhas -->
    <a href="https://www.uol.com.br/noticias/2025/12/03/noticia-valida.htm">
      Noticias
      <span>Pastores no Senado hoje a noite</span>
    </a>
    <!-- Link de servico: sem ano no path -->
    <a href="https://www.uol.com.br/meu-uol/">
      Meu UOL
    </a>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "a") -> list[Tag]:
    soup = BeautifulSoup(_HTML_UOL_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_uol_scraper_accepts_only_news_like_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = UOLScraper()
    articles = scraper.scrape()

    assert len(articles) == 1
    article = articles[0]

    assert (
        article.url == "https://www.uol.com.br/noticias/2025/12/03/noticia-valida.htm"
    )
    assert article.title == "Pastores no Senado hoje a noite"
