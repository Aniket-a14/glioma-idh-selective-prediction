# CONTRIBUTOR TASKS

A standing backlog of small, bounded, off-critical-path work for the team's five other
collaborators — Akshita1395, priyaagrawal2, ShantanuTripathi2745, solankisuryansh,
udaypratapchauhan — and whichever AI agent they're running (Antigravity, Codex free tier, or
anything else). The critical research path (phases in `docs/research/phases/`) stays owned by
the Research Lead, Claude, and Codex per `AGENT_WORKTREE_PROTOCOL.md`. This file is the *only*
sanctioned exception to that protocol's directory-ownership table — a task listed here may touch
exactly the paths it names, nothing else.

**Agents: start at `docs/research/prompts/CONTRIBUTOR_PROMPT.md`, not here.** That prompt tells
you how to claim a task from this file safely. Reading this file alone is not enough context to
act on.

**Humans: this file is curated by the Research Lead, weekly**, ahead of the Friday capstone
discussion. Add tasks here only when you (Research Lead) have picked a bounded, safe piece of
work off the critical path — never let a contributor agent invent its own scope.

---

## Open

Unclaimed. First agent to claim one edits this file to move its row to **Claimed** with the
claimant's GitHub username, before starting any work.

| ID | Task | Allowed paths | Notes |
|---|---|---|---|
| C-001 | Add edge-case unit tests for `utils/paths.py` (empty env var, relative path rejected, trailing slash, nonexistent parent) | `tests/unit/test_paths.py` only | Do not modify `src/glioma_selective/utils/paths.py` itself — tests only. 26 tests already exist; add to them, don't replace them. |
| C-002 | Proofread `docs/research/` for typos, broken internal links, and inconsistent terminology | `docs/research/**/*.md` (content edits only, no structural/heading changes, no changes to YAML state blocks) | Do not edit `PROJECT_STATE.md`'s status block or `DECISION_LOG.md` entries — flag anything that looks wrong there instead of fixing it. |
| C-003 | Draft a related-work paragraph summarizing 3–5 recent papers on selective prediction / conformal prediction in medical imaging | `paper/RELATED_WORK_DRAFT.md` (new file) | Draft only — citations and claims get checked by the Research Lead before anything moves into the actual manuscript. |

## Claimed

| ID | Task | Claimed by | Branch | PR |
|---|---|---|---|---|
| — | — | — | — | — |

## Done

| ID | Task | Closed by | PR | Merged |
|---|---|---|---|---|
| — | — | — | — | — |

---

## Hard rules (same as every other agent role in this repo)

- Never touch `PROJECT_STATE.md`, `DECISION_LOG.md`, dataset splits/manifests, `.env`, or anything
  under `data/`/`artifacts/`.
- Never merge your own PR. Every PR here goes through the same branch protection as everyone
  else's: 1 review, conversation resolution, Research Lead decides.
- Never work outside the "Allowed paths" column of your claimed task. If the task turns out to
  need more, stop and say so in the PR description rather than expanding scope silently.
- One claimed task at a time per person. Finish or explicitly drop it before claiming another.
