from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from app.services.scrape import base as base_module
from app.services.scrape.cnn import CNNScraper

_HTML_CNN_HOME = """
<html>
  <body>
    <figure class="group flex grow shrink-0 h-auto other">
      <figcaption>
        <a href="https://www.cnnbrasil.com.br/politica/noticia-1">
          <h2>1) Manchete numerada</h2>
        </a>
      </figcaption>
    </figure>
    <figure class="group flex grow shrink-0 h-auto">
      <figcaption>
        <a href="https://www.cnnbrasil.com.br/mundo/noticia-2">
          <h3>2- Outra manchete</h3>
        </a>
      </figcaption>
    </figure>
    <figure class="sem-classes-corretas">
      <figcaption>
        <a href="https://www.cnnbrasil.com.br/ignorar">
          <h2>Ignorar</h2>
        </a>
      </figcaption>
    </figure>
  </body>
</html>
"""


def _fake_fetch_elements(url: str, tag: str = "figure"):
    soup = BeautifulSoup(_HTML_CNN_HOME, "html.parser")
    return list(soup.find_all(tag))


def test_cnn_scraper_extracts_clean_titles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(base_module, "fetch_elements", _fake_fetch_elements)

    scraper = CNNScraper()
    articles = scraper.scrape()

    titles = {article.title for article in articles}
    urls = {article.url for article in articles}

    assert titles == {"Manchete numerada", "Outra manchete"}
    assert urls == {
        "https://www.cnnbrasil.com.br/politica/noticia-1",
        "https://www.cnnbrasil.com.br/mundo/noticia-2",
    }
