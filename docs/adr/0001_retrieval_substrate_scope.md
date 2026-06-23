# ADR 0001: Keep Open Web Retrieval A Shared Retrieval Substrate

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Status

Accepted.

## Context

Open-source research systems need search, fetch, extraction, provenance, and
failure classification. It is tempting for a retrieval library to expand into a
crawler, scraping framework, anti-bot bypass product, or project-specific
ranking layer. That would make the shared boundary harder to test and would
move analysis decisions out of downstream projects.

The existing requirements and capability decomposition already distinguish
shared retrieval primitives from downstream query planning and analysis.

## Decision

`open_web_retrieval` remains a shared retrieval substrate:

- own normalized search adapters and Pydantic retrieval contracts;
- own HTTP fetch, optional render escalation, optional bounded anti-bot
  escalation, extraction, cache, rate limiting, provenance, and error
  classification;
- emit compatible tool-call observability records;
- leave query strategy, ranking policy, citation judgment, and analytic claims
  to consuming projects.

Portfolio pages should present this repo through applied downstream traces, not
as a standalone scraping or analysis product.

## Consequences

Benefits:

- keeps the API small and reusable;
- prevents project-specific logic from accumulating in shared infrastructure;
- preserves clear ownership between retrieval and analysis;
- makes provenance and failure behavior easier to inspect.

Costs:

- this repo alone is not a complete analyst workflow;
- some consumer needs may require explicit boundary decisions before they are
  promoted into shared controls;
- anti-bot capability stays intentionally limited.

## Controls

- [docs/REQUIREMENTS.md](../REQUIREMENTS.md) defines scope and failure criteria.
- [docs/ops/CAPABILITY_DECOMPOSITION.md](../ops/CAPABILITY_DECOMPOSITION.md)
  defines ownership boundaries.
- [docs/VALIDATION.md](../VALIDATION.md) separates retrieval evidence from
  downstream analytic validation.
- [docs/CONCERNS.md](../CONCERNS.md) tracks scope-creep and portfolio risks.
