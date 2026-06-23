# Open Web Retrieval Methodology

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Goal

`open_web_retrieval` gives projects a reusable, typed, provenance-bearing way
to retrieve public web sources. The goal is not to scrape everything. The goal
is to make ordinary search, fetch, extraction, and failure behavior explicit
enough that downstream research systems can trust and inspect the source path.

The target loop is:

```text
query -> search hit -> fetch/render -> extract -> provenance -> downstream use
```

## Design Method

The repo uses a fast-path plus bounded escalation strategy:

1. Search through normalized provider adapters.
2. Fetch with `httpx` for cooperative sources.
3. Classify fetch errors as transient or permanent.
4. Escalate to Playwright only when rendering is needed.
5. Escalate to Crawl4AI only for narrowly scoped 403 anti-bot cases.
6. Extract clean text/markdown with trafilatura and fallback stripping.
7. Preserve provenance and metrics for downstream consumers.

This is a shared substrate. Consumers decide what to search for and what claims
to make from retrieved content.

## Borrow-Vs-Build

Borrowed:

- `httpx` for transport;
- `trafilatura` for extraction;
- Playwright for optional rendering;
- Crawl4AI for optional anti-bot escalation;
- provider APIs for search.

Built locally:

- normalized Pydantic contracts;
- provider adapters;
- fetch-error classification;
- provenance model;
- typed shared retrieval controls;
- cache and rate-limit behavior;
- tool-call observability emission boundary.

## Modality Split

Deductive / plan-first surfaces:

- Pydantic contracts;
- provider adapter request mapping;
- fetch-error classifications;
- provenance fields;
- cache/rate-limit policies;
- capability ownership boundaries.

Exploratory / ladder surfaces:

- which provider gives best results for a downstream task;
- when browser rendering is worth the latency/cost;
- whether anti-bot escalation should be used at all;
- how much retrieved text is enough for a downstream claim;
- when multi-provider orchestration should become a first-class shared surface.

Exploratory surfaces need applied traces and consumer evidence, not broader
infrastructure claims.

## ADR Map

- [0001_retrieval_substrate_scope.md](adr/0001_retrieval_substrate_scope.md)
  records the scope decision: shared retrieval substrate, not crawler/scraper
  product.

## Main Failure Modes

| Failure mode | Why it matters | Control |
|---|---|---|
| Treating retrieval as analysis | A fetched page does not prove a claim. | Downstream project owns analysis and citation use. |
| Expanding into a crawler/scraper platform | Bloats the shared boundary. | Capability decomposition and ADR scope control. |
| Silent provider fallback | Can hide source-quality problems. | Fail loud unless partial mode is explicit. |
| Browser-first retrieval | Adds latency and operational fragility. | HTTP fast path, render only when needed. |
| Anti-bot arms race | Can become unethical or brittle. | Narrow Crawl4AI escalation; no CAPTCHA/proxy platform. |
