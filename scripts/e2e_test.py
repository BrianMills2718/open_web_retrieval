#!/usr/bin/env python3
"""End-to-end integration test against real URLs.

Run manually: python scripts/e2e_test.py
Results saved to tests/fixtures/e2e_results.json
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_web_retrieval import FetchError, SourceFetcher
from open_web_retrieval.models import FetchRequest

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

# Test URLs covering diverse scenarios
TEST_URLS = [
    # Cooperative sites (should work)
    ("wikipedia", "https://en.wikipedia.org/wiki/Web_scraping"),
    ("github_raw", "https://raw.githubusercontent.com/unclecode/crawl4ai/main/README.md"),
    ("python_docs", "https://docs.python.org/3/library/asyncio.html"),
    (
        "sec_edgar",
        "https://www.sec.gov/cgi-bin/browse-edgar?company=palantir&CIK=&type=&dateb=&owner=include&count=10&search_text=&action=getcompany",
    ),
    # Should be blocked (paywall)
    ("reuters_blocked", "https://www.reuters.com/technology/"),
    # Should handle gracefully
    ("httpbin_404", "https://httpbin.org/status/404"),
    ("nonexistent", "https://this-domain-definitely-does-not-exist-12345.com/"),
]


def run_e2e() -> int:
    """Fetch test URLs, validate results, save golden fixtures."""
    results: list[dict] = []

    fetcher = SourceFetcher(
        blocked_domains={"reuters.com", "wsj.com", "ft.com"},
        rate_limit_per_second=1.0,
        enable_auto_render=False,  # Don't need Playwright for this test
    )

    with fetcher:
        for name, url in TEST_URLS:
            result: dict = {
                "name": name,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                resource = fetcher.fetch(FetchRequest(url=url))
                doc = fetcher.extract(resource)
                result.update(
                    {
                        "status": "success",
                        "http_status": resource.status,
                        "fetch_method": resource.fetch_method,
                        "bytes": len(resource.content_bytes),
                        "text_len": len(doc.text),
                        "markdown_len": len(doc.markdown),
                        "title": doc.title,
                        "publisher": doc.publisher_guess,
                        "extraction_method": doc.extraction_method,
                        "warnings": doc.warnings,
                        "text_preview": doc.text[:200] if doc.text else "",
                        "markdown_preview": doc.markdown[:200] if doc.markdown else "",
                    }
                )
            except FetchError as e:
                result.update(
                    {
                        "status": "fetch_error",
                        "error": str(e),
                        "retryable": e.retryable,
                    }
                )
            except Exception as e:
                result.update(
                    {
                        "status": "error",
                        "error": f"{type(e).__name__}: {e}",
                    }
                )

            results.append(result)
            status = result.get("status")
            if status == "success":
                print(
                    f"  OK   {name}: {result.get('text_len', 0)} chars, "
                    f"title={result.get('title', 'None')}"
                )
            else:
                print(f"  FAIL {name}: {result.get('error', 'unknown')}")

    # Log metrics
    m = fetcher.metrics
    print(
        f"\nMetrics: fetched={m.fetched} blocked={m.skipped_blocked} "
        f"permanent={m.skipped_permanent} retried={m.retried} failed={m.failed}"
    )

    # Save results
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    output = fixtures_dir / "e2e_results.json"
    output.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to {output}")

    # Validate expectations
    errors: list[str] = []
    for r in results:
        name = r["name"]
        if name == "wikipedia" and r["status"] != "success":
            errors.append(f"wikipedia should succeed, got {r['status']}")
        if name == "wikipedia" and r.get("text_len", 0) < 1000:
            errors.append(f"wikipedia text too short: {r.get('text_len')}")
        if name == "reuters_blocked" and r.get("retryable") is not False:
            errors.append("reuters should be blocked (non-retryable)")
        if name == "httpbin_404" and r.get("retryable") is not False:
            errors.append("404 should be non-retryable")

    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nAll validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_e2e())
