from __future__ import annotations

from typing import Any

import pytest
import requests
from pydantic import ValidationError

from app.services.scrape.base import ScrapedArticle, fetch_elements

_HTML_SIMPLE = """
<html>
  <body>
    <a href="https://example.com/1">One</a>
    <a href="https://example.com/2">Two</a>
    <span>Ignore</span>
  </body>
</html>
"""


def _make_response(text: str, status_code: int = 200) -> Any:
    class _Response:
        def __init__(self, body: str, code: int) -> None:
            self.text = body
            self.status_code = code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise requests.HTTPError(f"status {self.status_code}")

    return _Response(text, status_code)


def test_scraped_article_valid_instance() -> None:
    article = ScrapedArticle(title="Titulo", url="https://example.com")
    assert article.title == "Titulo"
    assert article.url == "https://example.com"


def test_scraped_article_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        ScrapedArticle(title="", url="https://example.com")


def test_fetch_elements_returns_matching_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> Any:
        return _make_response(_HTML_SIMPLE)

    monkeypatch.setattr(requests, "get", fake_get)

    elements = fetch_elements("https://example.com", tag="a")

    assert len(elements) == 2
    assert all(el.name == "a" for el in elements)


def test_fetch_elements_handles_request_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict[str, str], timeout: int) -> Any:
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    elements = fetch_elements("https://example.com", tag="a")

    assert elements == []
