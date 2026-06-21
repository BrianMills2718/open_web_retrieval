# Open Web Retrieval Trace Example

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Claim

Open Web Retrieval is support infrastructure for OSINT-style workflows: search, fetch, render when needed, extract text, preserve provenance, and return typed errors. It should be shown through an applied trace, not as a standalone library tour.

## End-to-End Trace Shape

| Step | Evidence to preserve |
|------|----------------------|
| Query | Query text, time, provider, filters, and task context |
| Search result | URL, title, snippet, rank, provider metadata |
| Fetch | HTTP status, final URL, content type, latency, retry/error class |
| Extraction | Extractor used, text length, title, byline/date when available |
| Provenance | Source URL, access time, content hash or stable source identifier |
| Downstream use | Which claim, citation, or analytic artifact consumed the evidence |

## Reviewer Path

1. Read `README.md` for the library capability.
2. Read `docs/REQUIREMENTS.md` for the contract and failure expectations.
3. Read `docs/SOTA_RESEARCH.md` for the retrieval design context.
4. Use an applied trace from Grounded Research, OSINT Tools, or Process Tracing when available.

## Caveat

This project is not the analysis itself. It earns portfolio value when a downstream workflow can show that a claim came from a retrievable, inspectable, and repeatable public source path.
