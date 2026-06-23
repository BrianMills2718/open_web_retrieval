# Open Web Retrieval Concern Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Open Concerns

| ID | Concern | Severity | Current mitigation | Next evidence/action |
|---|---|---:|---|---|
| OWR-PORT-001 | Infrastructure can look abstract without a downstream trace. | High | Dossier frames it as supporting evidence. | Publish one applied retrieval trace from a claim/citation. |
| OWR-PORT-002 | Retrieval may be mistaken for analytic validation. | High | Validation register separates retrieval trace from downstream analysis. | Tie each portfolio claim to a downstream artifact. |
| OWR-PORT-003 | Anti-bot scope can creep into an arms race. | Medium | Requirements and ADR exclude CAPTCHA/proxy/broad bypass work. | Keep Crawl4AI as bounded optional escalation. |
| OWR-PORT-004 | Provider behavior can drift. | Medium | Adapter tests and roadmap track provider-specific controls. | Add periodic live smoke checks where useful. |
| OWR-PORT-005 | Multi-provider orchestration boundary remains open. | Medium | Capability decomposition keeps it an explicit uncertainty. | Decide only after a real consumer proves the need. |

## Portfolio Judgment

`open_web_retrieval` is valuable supporting evidence for AI-engineering and
OSINT-style workflows. It should not lead the portfolio, but it makes applied
research systems more credible because public-source acquisition has typed
contracts, provenance, and failure semantics.
