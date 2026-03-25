# open_web_retrieval — Requirements

**Status**: Active
**Last updated**: 2026-03-25
**Owner**: Brian Mills

---

## What This Is

A shared Python library that gives any project the ability to search the web,
fetch pages, and extract clean text — with provenance, error classification,
and configurable resilience. It's shared infrastructure per the root CLAUDE.md:
"general capabilities any project uses."

## What This Is NOT

- Not a web crawler (no link-following, sitemaps, or recursive crawling)
- Not a scraping framework (no CSS selectors, no DOM manipulation)
- Not an anti-bot bypass service (no CAPTCHA solving, no proxy rotation)
- Not a search engine (wraps Brave/SearxNG, doesn't index anything)

---

## Consumers

| Consumer | Uses | Needs |
|----------|------|-------|
| **research_v3 loop.py** | Search (Brave), Fetch, Extract | Fast search, resilient fetch (skip paywalls), clean text for LLM extraction |
| **research_v3 tools/brave_search.py** | Search (Brave) | Normalized search results |
| **sam_gov** (potential) | Search, Fetch | Government site fetching |
| **Future OSINT projects** | All | Full pipeline |

---

## Capabilities (current v0 + planned)

### Search — find URLs for a query

| Feature | Status | Notes |
|---------|--------|-------|
| Brave API search | **Shipped** | Via adapter |
| SearxNG search | **Shipped** | Via adapter |
| Normalized SearchHit output | **Shipped** | Provider-agnostic Pydantic model |
| Recency filtering | **Shipped** | `recency_days` param |
| Domain allow/deny lists | **Shipped** | `domains_allow`, `domains_deny` |
| Result deduplication across providers | **Not started** | Same URL from Brave + SearxNG |
| Search result caching | **Shipped** | TTL-based via `cache.py` |

### Fetch — retrieve page content from a URL

| Feature | Status | Notes |
|---------|--------|-------|
| HTTP fetch (httpx) | **Shipped** | Direct GET with follow-redirects |
| Playwright JS rendering | **Shipped** | Optional, `render_mode="always"` |
| Provenance (method, SHA256, timestamps) | **Shipped** | On FetchedResource |
| Byte limit enforcement | **Shipped** | `max_bytes` param |
| **HTTP error classification** | **Not started** | 403/401/404 = permanent, 429/5xx = retryable |
| **Retry with backoff** | **Not started** | For retryable errors only |
| **Known-blocked domain skip** | **Not started** | Configurable set, skip immediately |
| **Respect Retry-After header** | **Not started** | On 429 responses |
| Rate limiting (requests/second) | **Not started** | Prevent overwhelming hosts |
| Robots.txt respect | **Not started** | Ethical default |

### Extract — turn HTML into clean text

| Feature | Status | Notes |
|---------|--------|-------|
| Trafilatura extraction | **Shipped** | Primary path |
| Fallback tag stripping | **Shipped** | When trafilatura fails |
| Markdown output | **Not started** | Currently text-only |
| Metadata extraction (title, author, date) | **Shipped** | Via ExtractedDocument fields |

### Cross-Cutting

| Feature | Status | Notes |
|---------|--------|-------|
| Full pipeline (search → fetch → extract) | **Shipped** | Via `OpenWebRetrievalClient` |
| Provenance on every operation | **Shipped** | Provider, URL, method, timestamps |
| Pydantic models for all contracts | **Shipped** | Frozen, validated |
| pip-installable | **Shipped** | `pip install -e ~/projects/open_web_retrieval` |

---

## Success Criteria

The library succeeds when:

1. **research_v3 loop completes F1 in <10 minutes** (currently times out at 20+ due to 403 retries)
2. **No consumer hand-rolls search, fetch, or extraction** — all go through this library
3. **Failures are classified** — consumers can distinguish "try again" from "give up"
4. **Provenance is complete** — every fetched page traces back to query → search hit → URL → content

## Failure Criteria

The library fails if:

1. It adds >500ms latency to the happy path (cooperative sites that return 200)
2. It requires Playwright/browser for basic HTTP fetches
3. It silently swallows errors (violates "fail loud" principle)
4. Consumers need to import httpx or trafilatura directly to work around limitations

---

## Priority Order (what to build next)

Based on consumer needs and dependency chain:

1. **HTTP error classification + retry** — #1 blocker. Use `retryhttp` or `httpx-retries`,
   not hand-rolled. 403 = permanent (skip), 429 = backoff, 5xx = retry.
2. **Known-blocked domain skip** — configurable set passed to SourceFetcher constructor.
   Prevents even attempting paywalled sites.
3. **Retry-After header respect** — on 429, wait the specified duration.
4. **Rate limiting** — prevent overwhelming Brave API or target hosts.
5. **Markdown output** — consumers (research_v3 loop, future agents) want markdown, not raw text.
6. **Result dedup** — when using multiple search providers.

Items 1-2 unblock research_v3 eval. Items 3-6 are quality-of-life.

---

## Boundaries

### This library owns:
- HTTP transport (httpx client lifecycle, retries, error classification)
- Search provider adapters (Brave, SearxNG)
- Content extraction (trafilatura, fallback)
- Provenance tracking (what was fetched, when, how)
- Caching (TTL-based result cache)

### This library does NOT own:
- What to search for (consumer decides queries)
- What to do with extracted text (consumer's LLM pipeline)
- Anti-bot bypass (if needed, add Crawl4AI as optional dep — Phase 2 of Plan #1)
- Domain-specific ranking or filtering (consumer layer)
- Proxy management or rotation (out of scope for v0)
