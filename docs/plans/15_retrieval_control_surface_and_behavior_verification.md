# Plan #15: Retrieval Control Surface and Behavior Verification

**Status:** 📋 Planned
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** consumer-expressive shared search behavior

---

## Gap

**Current:** `open_web_retrieval` exposes a small normalized `SearchQuery`
contract, but the adapters still hardcode important search controls:

- Tavily always uses `search_depth="advanced"`
- Exa always uses `type="deep"`
- Exa always requests one fixed highlights shape
- consumers cannot declare semantic guidance or corpus/category intent through
  the shared contract

The repo also lacks a clear reusable verification story for behavior claims
like "the adapter honored the requested search depth."

**Target:** a generic retrieval-control surface that any consumer can use,
plus adapter tests that verify the exposed controls actually propagate to the
provider request payloads.

**Why:** this repo should not fit one consumer's case. It should expose shared,
configurable retrieval controls that downstream repos can declare explicitly.

---

## Pre-Made Decisions

1. This wave expands the normalized contract rather than adding consumer-local
   wrapper knobs.
2. New fields must be generic enough for multiple consumers, not Tyler-named.
3. Provider-specific raw payloads may still remain in `SearchHit.raw_payload`,
   but request-time control surfaces must be first-class typed fields.
4. This wave will not introduce a free-form `dict[str, Any]` options bag at the
   boundary.
5. Behavior verification in this wave means transport-capture adapter tests,
   not a generic cross-repo trace engine.
6. `enforced-planning` follow-through is a separate upstream governance slice;
   this wave only implements the reusable retrieval substrate.

---

## Contract Changes

The shared `SearchQuery` contract should gain explicit, typed controls for:

1. `search_depth`
   - `basic` or `advanced`
   - provider-agnostic recall/depth hint
2. `result_detail`
   - `summary` or `chunks`
   - whether the consumer wants lightweight snippets or richer extracted
     passages when the provider supports it
3. `detail_budget`
   - optional positive integer
   - how many chunks/highlights per result to request when `result_detail`
     needs richer context
4. `retrieval_guidance`
   - optional free-text guidance string
   - for providers that support query-time semantic steering
5. `corpus`
   - optional corpus/category hint such as `general`, `academic`, or
     `government`

These fields must be optional and frozen like the rest of the model.

---

## Provider Mapping Rules

### Tavily

- `search_depth` maps to Tavily `search_depth`
- `domains_allow` maps to `include_domains`
- `domains_deny` maps to `exclude_domains`
- `recency_days` maps to `days`
- `result_detail="chunks"` with `detail_budget=N` maps to `chunks_per_source=N`
- if `result_detail` is unset, preserve the current lightweight default

### Exa

- `search_depth="advanced"` maps to `type="deep"`
- `search_depth="basic"` keeps the shallower/default search type
- `result_detail="chunks"` enables the `contents.highlights` request block
- `detail_budget` controls highlight count/size only when the provider supports it
- `retrieval_guidance` maps to Exa `systemPrompt`
- `corpus` maps to provider category controls where supported

If a provider does not support a field, fail loud only when silently ignoring
it would make the consumer believe the control was honored.

---

## Files Affected

- `docs/plans/15_retrieval_control_surface_and_behavior_verification.md` (create)
- `docs/notebooks/04_retrieval_control_surface_and_behavior_verification.ipynb` (create)
- `docs/plans/CLAUDE.md` (modify)
- `docs/ROADMAP.md` (modify)
- `README.md` (modify)
- `src/open_web_retrieval/models.py` (modify)
- `src/open_web_retrieval/client.py` (modify if cache keys need the new fields)
- `src/open_web_retrieval/adapters/tavily.py` (modify)
- `src/open_web_retrieval/adapters/exa.py` (modify)
- `tests/test_adapters.py` (modify)
- `tests/test_client.py` (modify if cache semantics change)

---

## Success Criteria

### Step 1: Contract Expansion

Pass:

- `SearchQuery` exposes typed retrieval controls for depth, detail, guidance,
  and corpus/category intent
- existing consumers remain valid without setting the new fields

Fail:

- the contract grows a free-form untyped options bag
- the change requires every current caller to be rewritten

### Step 2: Adapter Honor Tests

Pass:

- Tavily tests prove the adapter sends the requested depth and chunk budget
- Exa tests prove the adapter honors depth, detail mode, guidance, and corpus
  when configured

Fail:

- tests only prove defaults
- the adapter still hardcodes values that the contract claims are configurable

### Step 3: Consumer-Facing Docs

Pass:

- README and roadmap describe the new contract as generic shared capability,
  not one consumer's special case

Fail:

- docs still imply provider controls are fixed defaults only

---

## Required Tests

| Test / Check | What It Verifies |
|--------------|------------------|
| `pytest -q tests/test_adapters.py` | adapters honor the declared controls |
| `pytest -q tests/test_client.py` | client behavior and cache semantics still hold |
| notebook JSON parse | planning artifact is valid |

---

## Failure Modes

1. Overfitting the contract to Tyler-specific names instead of shared retrieval
   concepts
2. Adding controls without verifying they reach the provider request body
3. Making the contract so abstract that provider mapping becomes ambiguous
4. Expanding cache keys incorrectly and causing stale cross-query reuse

---

## Exit Condition

This wave is complete when:

- the normalized contract exposes the new typed controls,
- Tavily and Exa adapters honor them where supported,
- and the docs present this as generic shared retrieval capability.
