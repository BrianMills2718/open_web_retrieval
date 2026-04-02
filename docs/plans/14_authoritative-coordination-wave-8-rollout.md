# Plan #14: Authoritative coordination Wave 8 rollout

**Status:** ✅ Complete
**Type:** implementation
**Priority:** High
**Blocked By:** None
**Blocks:** truthful authoritative coordination adoption in `osint_tools`

---

## Gap

**Current:** `open_web_retrieval` is mechanically governed, clean in its
canonical root, and a measured clean opt-in candidate for authoritative
coordination, but it still does not expose the sanctioned local coordination
and worktree entrypoints. In `meta-process.yaml`, both:

- `meta_process.claims.enabled`
- `meta_process.worktrees.enabled`

are still `false`, and the local repo is still missing:

- `scripts/meta/check_coordination_claims.py`
- `scripts/meta/create_plan.py`
- `scripts/meta/plan_reservations.py`
- sanctioned worktree-coordination scripts
- sanctioned Makefile worktree targets

**Target:** `open_web_retrieval` adopts the same authoritative coordination
contract already proven in earlier wave repos:

- local coordination/worktree opt-in is explicit in `meta-process.yaml`
- sanctioned local coordination and worktree entrypoints are installed
- governed audit measures the repo as `adopted` for authoritative coordination
- the repo-local rollout remains bounded to the coordination surface

**Why:** Wave 8 is explicitly proving the clean shared-infrastructure opt-in
path. `open_web_retrieval` is the first repo in that pair.

---

## References Reviewed

- `CLAUDE.md`
- `README.md`
- `KNOWLEDGE.md`
- `meta-process.yaml`
- `docs/REQUIREMENTS.md`
- `docs/ROADMAP.md`
- `docs/ops/CAPABILITY_DECOMPOSITION.md`
- `docs/plans/13_governed-baseline-and-capability-ownership-rollout.md`
- `docs/plans/CLAUDE.md`
- `Makefile`
- `/home/brian/projects/project-meta_worktrees/plan-58-authoritative-registry-rollout/docs/plans/70_wave-8-shared-infrastructure-authoritative-coordination-opt-in-rollout.md`
- `/home/brian/projects/project-meta_worktrees/plan-58-authoritative-registry-rollout/docs/ops/AUTHORITATIVE_COORDINATION_ROLLOUT.md`
- `/home/brian/projects/project-meta_worktrees/plan-58-authoritative-registry-rollout/scripts/meta/install_governed_repo.py`
- `/home/brian/projects/llm_client/docs/plans/23_authoritative-coordination-wave-1-rollout.md`
- `/home/brian/projects/project-meta_worktrees/plan-58-authoritative-registry-rollout/scripts/meta/audit_governed_repo.py --repo-root /home/brian/projects/open_web_retrieval --json`

---

## Files Affected

- `docs/plans/14_authoritative-coordination-wave-8-rollout.md` (create/modify)
- `docs/plans/CLAUDE.md` (modify)
- `meta-process.yaml` (modify)
- `Makefile` (modify)
- `scripts/meta/check_coordination_claims.py` (create)
- `scripts/meta/create_plan.py` (create)
- `scripts/meta/plan_reservations.py` (create)
- `scripts/meta/worktree-coordination/check_claims.py` (create)
- `scripts/meta/worktree-coordination/create_worktree.py` (create)
- `scripts/meta/worktree-coordination/safe_worktree_remove.py` (create)

---

## Plan

### Steps

1. Record the local rollout plan and keep the worktree/plan reservation truthful.
2. Enable local coordination and worktree opt-in in `meta-process.yaml`.
3. Install the sanctioned local coordination and worktree entrypoints using the
   bounded installer path from `project-meta`.
4. Re-run governed audit plus local coordination/worktree smoke checks.
5. Commit the rollout as one rollback point.

---

## Required Tests

### Existing Checks (Must Pass)

| Command | Why |
|--------------|-----|
| `python /home/brian/projects/project-meta_worktrees/plan-58-authoritative-registry-rollout/scripts/meta/audit_governed_repo.py --repo-root /home/brian/projects/open_web_retrieval_worktrees/plan-14-authoritative-coordination-wave8 --json` | proves the repo remains governed and authoritative coordination now measures truthfully |
| `python scripts/meta/check_coordination_claims.py --check --project open_web_retrieval --json` | proves the local coordination CLI runs in-repo |
| `python scripts/meta/create_plan.py --dry-run --title "coordination smoke" --no-fetch` | proves the local plan allocation path executes |
| `make worktree-list` | proves the sanctioned Makefile worktree surface is wired |
| `git diff --check` | proves the rollout slice is syntactically clean |

### New Tests

None. The rollout copies the already-tested sanctioned scripts from
`project-meta`; repo-local verification is smoke/audit based.

---

## Acceptance Criteria

- [x] `meta_process.claims.enabled` and `meta_process.worktrees.enabled` are both `true`
- [x] the sanctioned local coordination scripts are present in `scripts/meta/`
- [x] the sanctioned local worktree scripts are present in `scripts/meta/worktree-coordination/`
- [x] the Makefile exposes the sanctioned worktree targets
- [x] governed audit still returns `status=PASS` and `classification=governed`
- [x] the authoritative coordination rollout audit would classify this repo as `adopted`
- [x] `python scripts/meta/check_coordination_claims.py --check --project open_web_retrieval --json` succeeds
- [x] `python scripts/meta/create_plan.py --dry-run --title "coordination smoke" --no-fetch` succeeds
- [x] `make worktree-list` succeeds
- [x] the worktree ends this slice at a clean rollback commit

## Completion Notes

- Repo-local authoritative coordination and worktree entrypoints are installed
  and enabled.
- `make worktree-list` required a repo-local worktree claim in addition to the
  shared authoritative coordination claim; without that local claim, the
  worktree correctly appeared as `ACTIVE (no claim)`.

---

## Notes

- This slice is intentionally bounded to authoritative coordination rollout.
- The repo-local plan exists before bootstrap so the later local `create_plan.py`
  installation is not pretending to have governed the slice retroactively.
- Do not widen this rollout into unrelated retrieval or provider work.
