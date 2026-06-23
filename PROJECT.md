# Open Web Retrieval Project Dossier

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Role

`open_web_retrieval` is supporting retrieval infrastructure. It is a
Brian-built shared library for search, fetch, render escalation, extraction,
provenance, caching, and fetch-error classification.

It should not be presented as a standalone analyst product. Its portfolio value
appears when a downstream workflow can show that a claim, citation, or evidence
item came from a retrievable, inspectable public-source path.

## Current Status

Safe current claims:

- normalized search adapters exist for Brave, SearxNG, Tavily, and Exa;
- direct HTTP fetch, optional Playwright rendering, optional Crawl4AI
  escalation, and SPA detection are implemented;
- extraction returns text/markdown with metadata when available;
- all major contracts are Pydantic models;
- provenance tracks provider, URL lineage, fetch method, and extraction method;
- retry/error classification distinguishes transient from permanent failures;
- shared retrieval controls exist for depth, detail, corpus, and Exa ranking
  instruction support;
- the repo has requirements, roadmap, SOTA research, capability ownership, and
  trace-example docs.

Do not claim:

- this is a crawler, scraping framework, or anti-bot bypass platform;
- it solves CAPTCHA, proxy rotation, or broad anti-bot evasion;
- it owns downstream query planning, ranking, or analysis;
- retrieval alone proves an analytic claim;
- infrastructure should lead the portfolio without an applied trace.

## Reviewer Path

1. Read [README.md](README.md) for installation, API examples, and capability
   overview.
2. Read [docs/RETRIEVAL_TRACE_EXAMPLE.md](docs/RETRIEVAL_TRACE_EXAMPLE.md) for
   the portfolio trace shape.
3. Read [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for scope and failure
   criteria.
4. Read [docs/ops/CAPABILITY_DECOMPOSITION.md](docs/ops/CAPABILITY_DECOMPOSITION.md)
   for shared-infrastructure ownership boundaries.
5. Read [docs/ROADMAP.md](docs/ROADMAP.md) and
   [docs/SOTA_RESEARCH.md](docs/SOTA_RESEARCH.md) for implementation history
   and borrow-vs-build context.
6. Read [docs/VALIDATION.md](docs/VALIDATION.md) and
   [docs/CONCERNS.md](docs/CONCERNS.md) before making reliability or OSINT
   claims.

## Why It Matters For An AI Engineer / Analyst Portfolio

Open-source analysis depends on source acquisition quality. This project shows
the engineering layer beneath analyst-facing systems: normalized provider
contracts, fetch resilience, extraction quality, provenance, explicit
partial-failure behavior, and typed controls that downstream systems can
inspect.

The best public framing is: "I built the shared web retrieval substrate so
research and OSINT systems can fetch public sources with provenance and typed
failure behavior instead of hand-rolling brittle HTTP code."

## Next Evidence To Create

The next portfolio-strengthening artifact is one applied retrieval trace:

1. Start from a downstream claim or citation.
2. Show query, provider, search hit, fetch metadata, extraction metadata, and
   provenance.
3. Show how the downstream project consumed the retrieved text.
4. Include any retry, render, blocked-domain, or permanent-failure decision.
