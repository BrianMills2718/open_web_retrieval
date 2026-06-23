"""Contract tests for the Medium retrieval module.

Network-touching paths are exercised via monkeypatched fetchers so the suite
stays offline and deterministic; live behavior is verified separately.
"""

from __future__ import annotations

import pytest

from open_web_retrieval import medium
from open_web_retrieval.medium import (
    MediumArticle,
    MediumFeedItem,
    _feed_url,
    _looks_paywalled,
    fetch_medium_article,
    search_medium_query,
)


class TestSearchQuery:
    def test_basic_scope(self):
        assert search_medium_query("osint") == "(site:medium.com) osint"

    def test_extra_publications(self):
        q = search_medium_query("ml", publications=["towardsdatascience.com"])
        assert q == "(site:medium.com OR site:towardsdatascience.com) ml"


class TestPaywallHeuristic:
    def test_short_text_is_paywalled(self):
        assert _looks_paywalled("too short") is True

    def test_marker_is_paywalled(self):
        body = "x" * 2000 + " this is a Member-only story you cannot read"
        assert _looks_paywalled(body) is True

    def test_long_clean_text_is_not_paywalled(self):
        assert _looks_paywalled("word " * 400) is False


class TestFeedUrl:
    def test_author_requires_at(self):
        assert _feed_url("@alice", "author") == "https://medium.com/feed/@alice"
        # handle without @ is normalized the same way
        assert _feed_url("alice", "author") == "https://medium.com/feed/@alice"

    def test_publication(self):
        assert _feed_url("towards-data-science", "publication") == "https://medium.com/feed/towards-data-science"

    def test_tag(self):
        assert _feed_url("osint", "tag") == "https://medium.com/feed/tag/osint"

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError):
            _feed_url("x", "bogus")


class TestFetchLadder:
    """The fetch ladder's branching, with the network mocked out."""

    def test_clean_direct_fetch_short_circuits(self, monkeypatch):
        long_text = "word " * 400

        def fake_fae(fetcher, url, *, render, trace_id, task):
            return long_text, "# md", "Title", "Author", url, []

        monkeypatch.setattr(medium, "_fetch_and_extract", fake_fae)
        art = fetch_medium_article("https://medium.com/p/abc", sid="s")
        assert isinstance(art, MediumArticle)
        assert art.paywalled is False
        assert art.method == "cookie"
        assert art.text == long_text

    def test_paywalled_then_freedium_succeeds(self, monkeypatch):
        good = "word " * 400
        calls = {"n": 0}

        def fake_fae(fetcher, url, *, render, trace_id, task):
            calls["n"] += 1
            # first call = the medium.com direct fetch → looks paywalled
            if "freedium.cfd" in url:
                return good, "", "T", "A", url, []
            return "member-only story", "", None, None, url, []

        monkeypatch.setattr(medium, "_fetch_and_extract", fake_fae)
        # no sid → browser step also skipped (no playwright in test env)
        monkeypatch.setattr(medium, "_browser_available", lambda: False)
        art = fetch_medium_article("https://medium.com/p/abc", enable_fallback=True)
        assert art.paywalled is False
        assert art.method == "freedium"

    def test_no_fallback_returns_paywalled(self, monkeypatch):
        def fake_fae(fetcher, url, *, render, trace_id, task):
            return "member-only story", "", None, None, url, []

        monkeypatch.setattr(medium, "_fetch_and_extract", fake_fae)
        monkeypatch.setattr(medium, "_browser_available", lambda: False)
        art = fetch_medium_article("https://medium.com/p/abc", sid="s", enable_fallback=False)
        assert art.paywalled is True


class TestFeedParsing:
    def test_content_encoded_yields_full_text(self, monkeypatch):
        rss = """<?xml version="1.0"?>
        <rss xmlns:content="http://purl.org/rss/1.0/modules/content/">
          <channel>
            <item>
              <title>Hello</title>
              <link>https://medium.com/p/1</link>
              <pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
              <content:encoded><![CDATA[<p>full article body here</p>]]></content:encoded>
            </item>
          </channel>
        </rss>"""

        class FakeResp:
            content = rss.encode("utf-8")
            def raise_for_status(self): pass

        monkeypatch.setattr(medium.httpx, "get", lambda *a, **k: FakeResp())
        monkeypatch.setattr(medium, "_html_to_text", lambda html, url=None: "full article body here")
        items = medium.parse_medium_feed("@x", kind="author")
        assert len(items) == 1
        assert isinstance(items[0], MediumFeedItem)
        assert items[0].truncated is False
        assert "full article body" in items[0].text

    def test_missing_content_encoded_marks_truncated(self, monkeypatch):
        rss = """<?xml version="1.0"?>
        <rss><channel>
          <item><title>T</title><link>https://medium.com/p/2</link></item>
        </channel></rss>"""

        class FakeResp:
            content = rss.encode("utf-8")
            def raise_for_status(self): pass

        monkeypatch.setattr(medium.httpx, "get", lambda *a, **k: FakeResp())
        items = medium.parse_medium_feed("osint", kind="tag")
        assert len(items) == 1
        assert items[0].truncated is True
        assert items[0].text == ""
