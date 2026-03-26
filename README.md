# open_web_retrieval

Shared Python library for web search, fetch, and extraction with provenance.
Search the web, fetch pages, extract clean text or markdown — with error
classification, rate limiting, and full provenance tracking.

**What it is:** A reusable substrate that any project can `pip install` to get
normalized web retrieval without hand-rolling httpx + HTML parsing.

**What it is not:** Not a web crawler, not a scraping framework, not an anti-bot
bypass service.

## Installation

```bash
# Base (search + fetch only)
pip install -e ~/projects/open_web_retrieval

# With text/markdown extraction (trafilatura)
pip install -e "~/projects/open_web_retrieval[extract]"

# With browser rendering (Playwright)
pip install -e "~/projects/open_web_retrieval[render]"
```

## Quickstart

```python
from open_web_retrieval.client import OpenWebRetrievalClient
from open_web_retrieval.models import SearchQuery

client = OpenWebRetrievalClient(
    brave_api_key="your-key",
    blocked_domains={"paywalled-site.com", "pinterest.com"},
    rate_limit_per_second=2.0,
)

# Search
query = SearchQuery(query="Python web scraping best practices", providers=["brave"], top_k=5)
hits = client.search(query)
for hit in hits:
    print(f"{hit.rank}. {hit.title} — {hit.url}")

# Full pipeline: search + fetch + extract
batch = client.retrieve(query, allow_partial=True)
for record in batch.records:
    doc = record.extracted_document
    if doc:
        print(f"## {doc.title}")
        print(f"Publisher: {doc.publisher_guess}")
        print(f"Date: {doc.published_at_guess}")
        print(f"Method: {doc.extraction_method}")
        print(doc.markdown[:500])  # Markdown output from trafilatura
```

## Features

| Feature | Details |
|---------|---------|
| **Search** | Brave API, SearxNG. Normalized `SearchHit` contract. Dedup by URL across providers. |
| **Fetch** | httpx with error classification. `FetchError.retryable` distinguishes "try again" from "give up." |
| **Blocked domains** | Configurable set — rejected immediately without network request. |
| **Rate limiting** | Per-domain (default 2 req/s). Respects `Retry-After` header on 429. |
| **Extract** | Plain text and markdown via trafilatura. Title, author, date, sitename metadata. |
| **Render** | Optional Playwright fallback (`render_mode="always"`). Install with `[render]`. |
| **Provenance** | Every `SourceRecord` tracks provider, URL lineage, fetch method, extraction method. |
| **Caching** | Optional disk cache for search results and fetched pages (TTL-based). |
| **Observability** | `FetchMetrics` counters: fetched, skipped_blocked, skipped_permanent, retried, failed, total_wait_seconds. |

## Error Handling

All exceptions live in `open_web_retrieval.exceptions`:

```python
from open_web_retrieval.exceptions import FetchError

try:
    resource = client.fetcher.fetch(fetch_request)
except FetchError as e:
    if e.retryable:
        # 429, 5xx, timeout — try again later
        print(f"Transient: {e}")
    else:
        # 401, 403, 404, 410, 451, blocked domain — give up
        print(f"Permanent: {e}")
```

Error codes: `OPEN_WEB_RETRIEVAL_PROVIDER_UNAVAILABLE`,
`OPEN_WEB_RETRIEVAL_RETRIEVAL_ERROR`, `OPEN_WEB_RETRIEVAL_FETCH_ERROR`,
`OPEN_WEB_RETRIEVAL_RENDER_ERROR`, `OPEN_WEB_RETRIEVAL_CAPABILITY_UNSUPPORTED`.

## Configuration

```python
client = OpenWebRetrievalClient(
    brave_api_key="...",                    # Brave API key
    searxng_base_url="http://localhost:8080",  # SearxNG instance
    blocked_domains={"pinterest.com"},      # Skip without fetching
    rate_limit_per_second=2.0,              # Per-domain rate limit
    cache_dir="/tmp/owr_cache",             # Enable disk caching
    cache_ttl_seconds=3600,                 # Cache TTL (default 1 hour)
    timeout_seconds=10.0,                   # HTTP timeout
)
```

## Documentation

- [REQUIREMENTS.md](docs/REQUIREMENTS.md) — what the library does and doesn't do
- [ROADMAP.md](docs/ROADMAP.md) — version history and future plans
- [SOTA_RESEARCH.md](docs/SOTA_RESEARCH.md) — landscape analysis (Crawl4AI, Firecrawl, Tavily, etc.)
