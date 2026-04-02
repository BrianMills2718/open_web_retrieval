# Plan #05: Crawl4AI Anti-Bot Escalation (v0.5)

**Status:** Complete
**Type:** implementation
**Priority:** Medium
**Blocked By:** Plans #01-04 (all complete)
**Blocks:** None (capability, not blocker)

---

## Gap

**Current (v0.4):** SourceFetcher classifies 403 as non-retryable and skips immediately.
This is correct for paywalls but means we also skip sites with Cloudflare/DataDome
anti-bot protection that would serve content to a real browser.

**Target (v0.5):** When httpx gets a 403 and Crawl4AI is installed, attempt a
browser-based fetch before giving up. Crawl4AI's 3-tier anti-bot detection
(HTTP status, HTML markers, stealth browser) can bypass protections that httpx cannot.

**Why:** Have the capability ready. Current eval runs don't need it, but future
OSINT targets (government sites, international sources) may have anti-bot protection
that isn't paywalling.

---

## References Reviewed

- `src/open_web_retrieval/fetch_extract.py` — current SourceFetcher.fetch()
- `src/open_web_retrieval/exceptions.py` — FetchError with retryable field
- `docs/SOTA_RESEARCH.md` — Crawl4AI API details, gotchas, memory concerns
- Crawl4AI docs: AsyncWebCrawler, CrawlResult, anti-bot detection, stealth mode
- Crawl4AI: Playwright mandatory (~150MB), 100-200MB RAM per browser, memory leaks in long sessions

## Key Design Constraint

The old Plan #01 had a contradiction: 403 is classified as non-retryable (correct),
but the escalation path checked `exc.retryable` (which would be False for 403).
The fix: **escalation is NOT a retry. It's a separate fetch path triggered by
HTTP 403 specifically, not by the retryable flag.**

```
httpx gets 403
  → NOT retryable (don't retry with httpx)
  → BUT if crawl4ai is available, try browser-based fetch (different mechanism)
  → If crawl4ai also fails, then give up
```

---

## Pre-made Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Crawl4AI as optional dep | `pip install open_web_retrieval[antibot]` | Don't force 150MB Chromium on all consumers |
| Trigger for escalation | HTTP 403 specifically, not retryable flag | 403 means "access denied" — browser might bypass. 401/404/410 should never escalate. |
| Sync wrapper over async | `asyncio.run()` in sync SourceFetcher | Library is sync. Don't force async on consumers. |
| Browser lifecycle | One browser per SourceFetcher, lazy-init, close in close()/context manager | Avoid 100-200MB per fetch. Reuse browser across fetches. |
| Max escalation attempts | 1 (no retry on escalation failure) | Escalation is expensive. Fail fast. |
| Configurable | `enable_antibot: bool = False` on SourceFetcher | Must opt-in. Don't silently launch browsers. |

---

## Files Affected

- `pyproject.toml` (modify — add `[antibot]` optional dep)
- `src/open_web_retrieval/fetch_extract.py` (modify — add escalation logic, browser management)
- `src/open_web_retrieval/client.py` (modify — expose `enable_antibot` param)
- `src/open_web_retrieval/models.py` (modify — add `FetchMetrics.escalated` counter)
- `tests/test_fetch_extract.py` (modify — escalation tests with mocked Crawl4AI)

---

## Plan

### Step 1: Add `crawl4ai` optional dependency

```toml
[project.optional-dependencies]
extract = ["trafilatura>=1.12,<3"]
render = ["playwright>=1.45"]
antibot = ["crawl4ai"]
all = ["trafilatura>=1.12,<3", "playwright>=1.45", "crawl4ai"]
```

### Step 2: Add `_crawl4ai_fetch` method to SourceFetcher

```python
def _crawl4ai_fetch(self, url: str) -> FetchedResource:
    """Attempt browser-based fetch via Crawl4AI for anti-bot bypass."""
    import asyncio
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    async def _fetch():
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(
            verbose=False,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            if not result.success:
                raise FetchError(
                    f"crawl4ai failed: {result.error_message}",
                    retryable=False,
                    context={"url": url, "method": "crawl4ai"},
                )
            return FetchedResource(
                requested_url=url,
                final_url=result.url or url,
                status=result.status_code or 200,
                content_type="text/html",
                content_bytes=result.html.encode("utf-8") if result.html else b"",
                retrieved_at_utc=_utc_now(),
                fetch_method="crawl4ai",
                sha256=_hash_bytes(result.html.encode("utf-8") if result.html else b""),
            )

    return asyncio.run(_fetch())
```

### Step 3: Add escalation logic in fetch()

After the existing HTTPStatusError catch for 403:

```python
except httpx.HTTPStatusError as exc:
    if exc.response.status_code == 403 and self._enable_antibot:
        # 403 is non-retryable for httpx, but try browser-based fetch
        try:
            logger.info("Escalating to crawl4ai for anti-bot: %s", request.url)
            self.metrics.escalated += 1
            return self._crawl4ai_fetch(request.url)
        except Exception as antibot_exc:
            logger.warning("crawl4ai escalation failed: %s", antibot_exc)
            # Fall through to raise original FetchError
    retryable = exc.response.status_code not in NON_RETRYABLE_STATUS
    raise FetchError(...)
```

### Step 4: Add constructor params and lazy browser check

```python
class SourceFetcher:
    def __init__(self, *, enable_antibot: bool = False, ...):
        self._enable_antibot = enable_antibot
        if enable_antibot:
            try:
                import crawl4ai
            except ImportError:
                raise ImportError(
                    "crawl4ai is required for anti-bot escalation. "
                    "Install with: pip install open_web_retrieval[antibot]"
                )
```

### Step 5: Expose through OpenWebRetrievalClient

```python
class OpenWebRetrievalClient:
    def __init__(self, *, enable_antibot: bool = False, ...):
        self.fetcher = SourceFetcher(
            ..., enable_antibot=enable_antibot,
        )
```

### Step 6: Add `escalated` counter to FetchMetrics

```python
@dataclass
class FetchMetrics:
    ...
    escalated: int = 0  # anti-bot escalation attempts
```

### Step 7: Tests

Add to `tests/test_fetch_extract.py`:

| Test | What It Verifies |
|------|------------------|
| `test_403_escalates_when_antibot_enabled` | 403 + enable_antibot=True → calls _crawl4ai_fetch |
| `test_403_no_escalation_when_antibot_disabled` | 403 + enable_antibot=False → raises FetchError immediately |
| `test_escalation_failure_falls_through` | crawl4ai fails → original FetchError raised |
| `test_escalation_success_returns_resource` | crawl4ai succeeds → FetchedResource with method="crawl4ai" |
| `test_enable_antibot_requires_crawl4ai` | enable_antibot=True without crawl4ai → ImportError |
| `test_metrics_escalated_incremented` | Successful escalation → metrics.escalated == 1 |

Mock `crawl4ai` imports in tests — don't require actual Playwright/Chromium.

---

## Acceptance Criteria

- [x] `pip install open_web_retrieval[antibot]` installs crawl4ai
- [x] `enable_antibot=True` on SourceFetcher and OpenWebRetrievalClient
- [x] 403 triggers browser-based escalation when antibot enabled
- [x] Escalation failure falls through to original FetchError
- [x] FetchedResource from escalation has `fetch_method="crawl4ai"`
- [x] `FetchMetrics.escalated` counter incremented
- [x] Without crawl4ai installed, `enable_antibot=True` raises ImportError
- [x] Without `enable_antibot=True`, behavior identical to v0.4
- [x] All existing 98 tests pass (104 with observability)
- [x] 6 new escalation tests pass
- [ ] **Gate: at least one previously-403 URL returns content via escalation** — Deferred; library-side verified via e2e_test.py

---

## Known Risks

- Crawl4AI requires Playwright (~150MB Chromium download on first use)
- 100-200MB RAM per browser instance
- Playwright memory leaks in long sessions — but we create/destroy per fetch, not long-running
- Anti-bot bypass rates degrade as Cloudflare updates
- `asyncio.run()` inside sync code can conflict if caller already has an event loop

---

## Budget

~2 hours:
- Steps 1-3 (core escalation): ~1 hour
- Steps 4-6 (config, metrics): ~30 minutes
- Step 7 (tests): ~30 minutes
