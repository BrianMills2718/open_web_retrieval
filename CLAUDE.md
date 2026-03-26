# open_web_retrieval - Canonical Repo Instructions

**Version:** 0.4.0
**Last verified:** 2026-03-25

This repo is the shared open-web retrieval boundary.

## Purpose

- Search: Brave and SearxNG adapters in a normalized contract.
- Fetch: `httpx` direct fetch with error classification, blocked domains, per-domain rate limiting, Retry-After.
- Render: optional Playwright-based fallback when direct fetch is insufficient.
- Extract: text and markdown output via Trafilatura, with title/author/date/sitename metadata.
- Provenance: every operation records provider, URL lineage, and fetch/extract method.

## Commands

```bash
# Run all tests
pytest tests/ -q

# Run tests with verbose output
pytest tests/ -v

# Install with extraction support
pip install -e ".[extract]"

# Install with rendering support
pip install -e ".[render]"
```

## CI

GitHub Actions runs on push to main and PRs. Matrix: Python 3.10, 3.12.
Workflow: `.github/workflows/test.yml`

## Canonical Rules

- `open_web_retrieval` is the one canonical place for reusable open-web retrieval
  primitives.
- Domain repos should consume these primitives before hand-rolling web search,
  fetch, render, or extraction logic.
- Keep the API intentionally small; avoid speculative abstractions.
- Fail loudly by default. If partial-failure mode is used, it must be explicit.
- Update schema/capability changes and plan references when contracts change.

## Mandatory Reading

- `docs/` for package contract and operation notes.
- `src/open_web_retrieval/models.py` for schema contract.
- `src/open_web_retrieval/client.py` for retrieval orchestration.

## Work-in-scope

- v0.4 provider support: Brave, SearxNG, direct HTTP fetch with error classification
  and rate limiting, optional Playwright render fallback, Trafilatura extraction
  with markdown output.
- Optional future slices should be added as explicit migrations in
  `docs/plans/` and reflected in ROADMAP.md.

## Maintenance

- Edit this file first.
- Keep `AGENTS.md` as a generated mirror.
- Do not keep implementation shortcuts that silently alter contract behavior.
- Do not merge local-product UI concerns into this substrate.
