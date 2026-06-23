"""Medium article retrieval: search, full-text fetch, and RSS feeds.

Medium has no usable public read/search API (the official API is publish-only
and deprecated). This module provides the three things a research workflow
needs, built on the existing open-web primitives rather than hand-rolled:

  - search_medium_query():   build a `site:medium.com <topic>` query for any
                             SearchHit-returning adapter (Brave/SearxNG/...).
  - fetch_medium_article():  full article text via a fallback ladder —
                             (1) authenticated fetch with the member `sid`
                             cookie, (2) Freedium proxy, (3) archive.today —
                             so paywalled member-only stories are recoverable.
  - parse_medium_feed():     full article text from RSS `content:encoded` for a
                             known author or publication (no paywall bypass
                             needed; tag feeds are truncated and URL-only).

Auth: a Medium membership `sid` cookie unlocks first-party full text for
member-only stories. Pass it explicitly or set `MEDIUM_SID` (and optionally
`MEDIUM_UID`) in the environment. When the cookie is absent or stale the
fallback ladder degrades gracefully to the public proxies.

The fetch path reuses `SourceFetcher` (httpx + trafilatura + SPA auto-render +
tool-call observability); the cookie is injected via an httpx client.
"""

from __future__ import annotations

import logging
import os
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

from open_web_retrieval.fetch_extract import SourceFetcher
from open_web_retrieval.models import FetchedResource, FetchRequest
from open_web_retrieval.observability import ToolCallLogger

logger = logging.getLogger(__name__)

# RSS feed URL patterns. Insert "/feed" after medium.com; user profiles REQUIRE
# the leading "@". Author and publication feeds carry full `content:encoded`;
# tag feeds are truncated (description previews only) and useful for URL
# discovery, not content.
_FEED_AUTHOR = "https://medium.com/feed/@{handle}"
_FEED_PUBLICATION = "https://medium.com/feed/{slug}"
_FEED_TAG = "https://medium.com/feed/tag/{tag}"

# Paywall-bypass proxies (verified live mid-2026). 12ft.io and scribe.rip are
# dead and deliberately omitted.
_FREEDIUM = "https://freedium.cfd/{url}"
_ARCHIVE = "https://archive.ph/newest/{url}"

# Substrings that indicate a truncated member-only ("paywalled") article when
# the fetch was unauthenticated or the cookie was stale.
_PAYWALL_MARKERS = (
    "member-only story",
    "create an account to read the full story",
    "this story available to medium members only",
    "the author made this story available to medium members only",
    "sign up with google",  # the gate's signup widget leaks into extracted text
)

# Below this many characters an extracted Medium article is almost certainly a
# truncated gate page rather than a real post.
_MIN_FULL_TEXT_CHARS = 1200

# RSS `content:encoded` lives in this namespace.
_CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}encoded"


class MediumArticle(BaseModel):
    """A retrieved Medium article with provenance about how it was obtained."""

    url: str = Field(description="The canonical Medium article URL requested.")
    final_url: str = Field(description="The URL actually fetched (may be a proxy or archive).")
    title: str | None = Field(default=None, description="Article title, if extracted.")
    author: str | None = Field(default=None, description="Author or publication, if extracted.")
    text: str = Field(default="", description="Extracted plain-text article body.")
    markdown: str = Field(default="", description="Extracted markdown article body, if available.")
    paywalled: bool = Field(default=False, description="Whether the source appeared to be a truncated member-only gate.")
    method: str = Field(description="How full text was obtained: cookie | direct | freedium | archive | failed.")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal issues encountered while retrieving.")


class MediumFeedItem(BaseModel):
    """One item from a Medium RSS feed, with full text when available."""

    url: str = Field(description="The article URL from the feed item.")
    title: str | None = Field(default=None, description="Article title.")
    published: str | None = Field(default=None, description="Publication date string from the feed.")
    text: str = Field(default="", description="Full article text from content:encoded (empty for truncated tag feeds).")
    truncated: bool = Field(default=False, description="True when the feed only provided a preview (tag feeds).")


def search_medium_query(topic: str, *, publications: list[str] | None = None) -> str:
    """Build a search-engine query scoped to Medium for a topic.

    Pass the result as the `query` to any SearchHit-returning adapter
    (brave_search, searxng_search, ...). Medium itself has no search API, so a
    site-scoped general search is the most reliable discovery path.

    Args:
        topic: The subject to search for.
        publications: Optional extra Medium publication domains to include
            (e.g. ["towardsdatascience.com"]).

    Returns:
        A query string like ``site:medium.com (topic)``.
    """
    sites = ["medium.com", *(publications or [])]
    site_filter = " OR ".join(f"site:{s}" for s in sites)
    return f"({site_filter}) {topic}".strip()


def _looks_paywalled(text: str) -> bool:
    """Heuristic: did this extraction land on a truncated member-only gate?"""
    if len(text) < _MIN_FULL_TEXT_CHARS:
        return True
    lowered = text.lower()
    return any(marker in lowered for marker in _PAYWALL_MARKERS)


def _build_cookie_client(
    sid: str | None, uid: str | None, *, timeout_seconds: float | None
) -> httpx.Client:
    """Build an httpx client carrying the Medium membership cookies, if any."""
    cookies: dict[str, str] = {}
    if sid:
        cookies["sid"] = sid
    if uid:
        cookies["uid"] = uid
    return httpx.Client(cookies=cookies or None, timeout=timeout_seconds)


def _fetch_and_extract(
    fetcher: SourceFetcher,
    url: str,
    *,
    render: bool,
    trace_id: str | None,
    task: str | None,
) -> tuple[str, str, str | None, str | None, str, list[str]]:
    """Fetch + extract a URL via SourceFetcher.

    Returns (text, markdown, title, author, final_url, warnings).
    """
    request = FetchRequest(url=url, render_mode="always" if render else "auto")
    resource = fetcher.fetch(request, trace_id=trace_id, task=task)
    doc = fetcher.extract(resource, trace_id=trace_id, task=task)
    return doc.text, doc.markdown, doc.title, doc.publisher_guess, doc.final_url, list(doc.warnings)


def _browser_available() -> bool:
    """Whether Playwright (the [render] extra) is importable."""
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except Exception:
        return False


def _fetch_via_browser(
    url: str,
    *,
    sid: str | None,
    uid: str | None,
    timeout_seconds: float | None,
) -> tuple[str, str, str | None, str | None, str]:
    """Fetch a Medium URL in a real browser with membership cookies injected.

    A headless Chromium both passes Medium's edge anti-bot (which 403s plain
    httpx from datacenter IPs) and authenticates as the member when the `sid`
    cookie is present, yielding full member-only text. Extraction reuses the
    SourceFetcher trafilatura path on the rendered HTML.

    Returns (text, markdown, title, author, final_url). Raises on browser error.
    """
    from playwright.sync_api import sync_playwright

    timeout_ms = int((timeout_seconds or 30.0) * 1000)
    cookies = []
    if sid:
        cookies.append({"name": "sid", "value": sid, "domain": ".medium.com", "path": "/"})
    if uid:
        cookies.append({"name": "uid", "value": uid, "domain": ".medium.com", "path": "/"})

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            ctx = browser.new_context()
            if cookies:
                ctx.add_cookies(cookies)
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            html = page.content()
            final_url = page.url
        finally:
            browser.close()

    # Reuse the trafilatura extraction path; mark as render so it isn't re-rendered.
    from hashlib import sha256 as _sha256

    html_bytes = html.encode("utf-8")
    resource = FetchedResource(
        requested_url=url,
        final_url=final_url,
        status=200,
        content_type="text/html",
        content_bytes=html_bytes,
        retrieved_at_utc=_utc_now(),
        fetch_method="render_playwright",
        sha256=_sha256(html_bytes).hexdigest(),
    )
    fetcher = SourceFetcher(enable_auto_render=False)
    try:
        doc = fetcher.extract(resource)
    finally:
        fetcher.close()
    return doc.text, doc.markdown, doc.title, doc.publisher_guess, final_url


def _utc_now():
    """Aware UTC timestamp for synthesized FetchedResource records."""
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc)


def fetch_medium_article(
    url: str,
    *,
    sid: str | None = None,
    uid: str | None = None,
    enable_fallback: bool = True,
    timeout_seconds: float | None = 30.0,
    tool_call_logger: ToolCallLogger | None = None,
    trace_id: str | None = None,
    task: str | None = None,
) -> MediumArticle:
    """Fetch a Medium article's full text, handling the member-only paywall.

    Fallback ladder:
      1. Authenticated fetch with the membership ``sid`` cookie (first-party
         full text for member-only stories). Cookie comes from the ``sid`` arg
         or the ``MEDIUM_SID`` env var (``uid`` / ``MEDIUM_UID`` optional).
      2. If still paywalled and ``enable_fallback``: Freedium (freedium.cfd).
      3. If still paywalled: archive.today (archive.ph/newest).

    Args:
        url: The Medium article URL.
        sid / uid: Membership cookies. Fall back to MEDIUM_SID / MEDIUM_UID env.
        enable_fallback: Try Freedium then archive.today when authenticated
            fetch is missing/stale and the article looks paywalled.
        timeout_seconds: Per-request timeout.

    Returns:
        A ``MediumArticle`` whose ``method`` records which path produced the
        text and whose ``paywalled`` flag is True if no path yielded full text.
    """
    sid = sid or os.environ.get("MEDIUM_SID")
    uid = uid or os.environ.get("MEDIUM_UID")
    warnings: list[str] = []

    # ── Step 1: authenticated (or plain) direct fetch ────────────────────────
    client = _build_cookie_client(sid, uid, timeout_seconds=timeout_seconds)
    fetcher = SourceFetcher(client=client, tool_call_logger=tool_call_logger)
    try:
        text, markdown, title, author, final_url, warns = _fetch_and_extract(
            fetcher, url, render=False, trace_id=trace_id, task=task
        )
    except Exception as exc:
        logger.info("MEDIUM direct fetch failed url=%s err=%s", url, exc)
        text, markdown, title, author, final_url, warns = "", "", None, None, url, [f"direct fetch failed: {exc}"]
    finally:
        fetcher.close()
    warnings += warns

    method = "cookie" if sid else "direct"
    if not _looks_paywalled(text):
        return MediumArticle(
            url=url, final_url=final_url, title=title, author=author,
            text=text, markdown=markdown, paywalled=False, method=method, warnings=warnings,
        )

    if not sid:
        warnings.append("no MEDIUM_SID cookie set; could not try authenticated fetch")

    # ── Step 2: real browser with cookie (passes anti-bot + authenticates) ───
    # Medium's edge 403s plain httpx from many IPs; a headless browser with the
    # sid cookie both gets past anti-bot and unlocks member-only full text.
    if _browser_available():
        try:
            b_text, b_md, b_title, b_author, b_final = _fetch_via_browser(
                url, sid=sid, uid=uid, timeout_seconds=timeout_seconds
            )
            if not _looks_paywalled(b_text):
                return MediumArticle(
                    url=url, final_url=b_final, title=b_title or title, author=b_author or author,
                    text=b_text, markdown=b_md, paywalled=False,
                    method="browser_cookie" if sid else "browser", warnings=warnings,
                )
            warnings.append("browser fetch returned truncated/paywalled content")
        except Exception as exc:
            logger.info("MEDIUM browser fetch failed url=%s err=%s", url, exc)
            warnings.append(f"browser fetch failed: {exc}")
    else:
        warnings.append("Playwright not installed; skipped browser fetch (pip install open_web_retrieval[render])")

    if not enable_fallback:
        return MediumArticle(
            url=url, final_url=final_url, title=title, author=author,
            text=text, markdown=markdown, paywalled=True, method=method, warnings=warnings,
        )

    # ── Steps 3 & 4: public proxies (no cookie) ──────────────────────────────
    for proxy_method, template in (("freedium", _FREEDIUM), ("archive", _ARCHIVE)):
        proxy_url = template.format(url=url if proxy_method == "freedium" else quote(url, safe=""))
        proxy_fetcher = SourceFetcher(tool_call_logger=tool_call_logger, timeout_seconds=timeout_seconds)
        try:
            p_text, p_md, p_title, p_author, p_final, p_warns = _fetch_and_extract(
                proxy_fetcher, proxy_url, render=False, trace_id=trace_id, task=task
            )
        except Exception as exc:
            logger.info("MEDIUM %s fetch failed url=%s err=%s", proxy_method, proxy_url, exc)
            warnings.append(f"{proxy_method} failed: {exc}")
            continue
        finally:
            proxy_fetcher.close()
        if not _looks_paywalled(p_text):
            return MediumArticle(
                url=url, final_url=p_final, title=p_title or title, author=p_author or author,
                text=p_text, markdown=p_md, paywalled=False, method=proxy_method,
                warnings=warnings + p_warns,
            )
        warnings.append(f"{proxy_method} returned truncated/short content")

    # ── All paths exhausted ──────────────────────────────────────────────────
    warnings.append("all fetch paths returned paywalled/truncated content")
    return MediumArticle(
        url=url, final_url=final_url, title=title, author=author,
        text=text, markdown=markdown, paywalled=True, method="failed", warnings=warnings,
    )


def _feed_url(handle: str, kind: str) -> str:
    """Resolve a feed URL for an author handle, publication slug, or tag."""
    handle = handle.lstrip("@")
    if kind == "author":
        return _FEED_AUTHOR.format(handle=handle)
    if kind == "publication":
        return _FEED_PUBLICATION.format(slug=handle)
    if kind == "tag":
        return _FEED_TAG.format(tag=handle)
    raise ValueError(f"unknown feed kind '{kind}' (use author | publication | tag)")


def parse_medium_feed(
    handle: str,
    *,
    kind: str = "author",
    limit: int = 20,
    timeout_seconds: float | None = 30.0,
) -> list[MediumFeedItem]:
    """Read a Medium RSS feed and return items with full text where available.

    Author (``/feed/@handle``) and publication (``/feed/<slug>``) feeds carry
    full article HTML in ``content:encoded`` — no paywall bypass needed. Tag
    feeds (``/feed/tag/<tag>``) are truncated previews, returned with
    ``truncated=True`` and empty text (use them to discover URLs, then call
    ``fetch_medium_article``).

    Args:
        handle: Author handle (with or without @), publication slug, or tag.
        kind: One of "author", "publication", "tag".
        limit: Max items to return.

    Returns:
        A list of ``MediumFeedItem``.
    """
    import xml.etree.ElementTree as ET

    feed_url = _feed_url(handle, kind)
    resp = httpx.get(feed_url, timeout=timeout_seconds, follow_redirects=True)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    items: list[MediumFeedItem] = []
    for item in root.iter("item"):
        if len(items) >= limit:
            break
        link = item.findtext("link") or ""
        title = item.findtext("title")
        published = item.findtext("pubDate")
        content_html = item.findtext(_CONTENT_NS) or ""
        if content_html:
            # Convert the embedded article HTML to plain text via trafilatura.
            text = _html_to_text(content_html, url=link)
            items.append(MediumFeedItem(url=link, title=title, published=published, text=text, truncated=False))
        else:
            items.append(MediumFeedItem(url=link, title=title, published=published, text="", truncated=True))
    return items


def _html_to_text(html: str, *, url: str | None = None) -> str:
    """Extract plain text from a chunk of article HTML (content:encoded)."""
    try:
        from trafilatura import extract
    except ModuleNotFoundError:
        logger.info("trafilatura not installed — feed text extraction limited. pip install open_web_retrieval[extract]")
        return ""
    return extract(html, url=url, favor_recall=True) or ""
