# Open Web Retrieval Validation Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Validation Position

`open_web_retrieval` has implementation evidence for shared retrieval behavior.
It still needs a public applied trace to become strong portfolio evidence.

The key distinction:

- **contract-valid:** provider adapters, fetch/extract models, and error
  classifications satisfy tests;
- **trace-valid:** a source path records query, provider, URL, fetch,
  extraction, and provenance;
- **analysis-valid:** a downstream project uses the retrieved evidence
  correctly for a claim.

This repo owns the first two categories. Downstream projects own the third.

## Current Evidence

| Evidence area | Current artifact | Claim licensed |
|---|---|---|
| Requirements and scope | `docs/REQUIREMENTS.md` | Retrieval capabilities and boundaries are explicit. |
| Versioned progress | `docs/ROADMAP.md` | Search/fetch/extract/render/provider controls shipped in stages. |
| SOTA research | `docs/SOTA_RESEARCH.md` | Borrow-vs-build choices were researched. |
| Capability ownership | `docs/ops/CAPABILITY_DECOMPOSITION.md` | Shared boundary is documented. |
| Trace shape | `docs/RETRIEVAL_TRACE_EXAMPLE.md` | Portfolio evidence format exists, but needs a populated case. |

## Evidence Not Yet Present

Do not claim the following without new evidence:

- downstream claims are correct because retrieval succeeded;
- broad anti-bot bypass capability;
- recursive crawling or scraping-framework behavior;
- provider quality superiority without a task-specific comparison;
- v1.0 public package readiness before the roadmap gate is met.

## Commands

Core checks:

```bash
make test
make lint
make typecheck
python scripts/check_markdown_links.py PROJECT.md docs/METHODOLOGY.md docs/ARTIFACTS.md docs/VALIDATION.md docs/CONCERNS.md docs/wiki_manifest.yaml
git diff --check
```

Optional live checks:

```bash
python scripts/e2e_test.py
```

Run live checks only when API keys, network, and budget are appropriate.

## Portfolio Readiness Gate

The repo is portfolio-ready as supporting infrastructure when framed with its
current caveats. It becomes stronger externally when it has:

1. One downstream applied trace.
2. A saved source-path table.
3. A visible failure/partial-failure example.
4. A consumer integration note showing how retrieved text supports a claim.
