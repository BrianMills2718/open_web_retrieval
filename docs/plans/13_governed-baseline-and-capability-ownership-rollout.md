# Plan #13: Governed Baseline And Capability Ownership Rollout

**Status:** 🚧 In Progress
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** truthful shared capability ownership coverage for open_web_retrieval

---

## Gap

**Current:** `open_web_retrieval` is already a shared substrate and audits
`PASS`, but it still lives on a bootstrap-minimal governance surface:

- `scripts/relationships.yaml` only defines default required reading
- `meta-process.yaml` is absent
- there is no repo-local capability ownership source of record

**Target:** deepen the governed baseline, declare repo-local capability
ownership, and make the shared-substrate role discoverable from local docs.

**Why:** this repo should be as truthful about shared ownership as
`llm_client`, `prompt_eval`, and `agentic_scaffolding`, without quietly taking
on a sanctioned-worktree rollout in the same wave.

---

## References Reviewed

- `CLAUDE.md`
- `README.md`
- `docs/REQUIREMENTS.md`
- `docs/ROADMAP.md`
- `docs/plans/CLAUDE.md`
- `scripts/relationships.yaml`
- `Makefile`
- `~/projects/project-meta/docs/plans/50_open-web-retrieval-governed-baseline-and-capability-ownership-rollout.md`
- `~/projects/project-meta/scripts/meta/audit_governed_repo.py`
- `~/projects/project-meta/scripts/meta/install_governed_repo.py`

---

## Files Affected

- `docs/plans/13_governed-baseline-and-capability-ownership-rollout.md` (create)
- `docs/plans/CLAUDE.md` (modify)
- `README.md` (modify)
- `CLAUDE.md` (modify)
- `AGENTS.md` (modify via renderer)
- `docs/ops/CAPABILITY_DECOMPOSITION.md` (create)
- `meta-process.yaml` (create)
- `scripts/relationships.yaml` (modify)
- other bounded installer outputs required for truthful governed baseline repair
- `KNOWLEDGE.md` (modify)

---

## Plan

1. Create this plan and keep the plan index aligned.
2. Run the shared governed-repo installer in the clean worktree and accept only
   bounded baseline-repair outputs.
3. Add `docs/ops/CAPABILITY_DECOMPOSITION.md` and declare
   `meta_process.capability_ownership`.
4. Update README/CLAUDE discoverability so the ownership source is easy to find.
5. Leave sanctioned worktrees out of scope unless the plan is explicitly
   amended.

---

## Required Tests

### Existing Tests (Must Pass)

| Test Pattern | Why |
|--------------|-----|
| `python ~/projects/project-meta/scripts/meta/audit_governed_repo.py --repo-root . --json` | governed baseline and ownership truth stay explicit |
| `python scripts/sync_plan_status.py --check` | plan index stays truthful |
| `python scripts/check_markdown_links.py README.md CLAUDE.md docs/plans/CLAUDE.md docs/plans/13_governed-baseline-and-capability-ownership-rollout.md` | local docs remain navigable |

---

## Acceptance Criteria

- [ ] `open_web_retrieval` no longer relies on a bootstrap-minimal-only governed surface
- [ ] repo-local capability ownership is declared truthfully
- [ ] local docs make the ownership source discoverable
- [ ] the wave stays baseline-plus-ownership and does not quietly become sanctioned-worktree rollout

---

## Notes

- matching shared registry and canonical-source updates happen under
  `project-meta` Plan 50
