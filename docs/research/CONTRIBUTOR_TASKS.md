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

**This round, each row below is pre-assigned to a specific person** (see "Assigned to") rather
than first-come — five people were independently landing on C-001 at the same time under the old
pure first-come model, since it was the first row in the table and nothing stopped two agents
claiming it within the same few minutes (the claim step is a plain commit-and-push to `main`;
without a lock, whoever pushes second either gets a rejected non-fast-forward push and doesn't
know why, or force-pushes over the first person's claim). Pre-assigning by name and giving each
person a non-overlapping set of paths removes the collision by construction for this round.
Once these five are done and the backlog is refreshed, new rows may go back to open first-come —
if so, the claim step below (git pull immediately before editing) still applies.

**Agents: only claim the row with your operator's GitHub username in "Assigned to."** If that
row is gone (already moved to Claimed/Done) and none of the remaining Open rows name your
operator, stop and report that rather than claiming someone else's row or inventing a new task.

| ID | Task | Allowed paths | Assigned to | Notes |
|---|---|---|---|---|
| C-001 | Add edge-case unit tests for `utils/paths.py` (empty env var, relative path rejected, trailing slash, nonexistent parent) | `tests/unit/test_paths.py` only | Akshita1395 | Do not modify `src/glioma_selective/utils/paths.py` itself — tests only. 26 tests already exist; add to them, don't replace them. |
| C-002 | Proofread top-level docs for typos, broken internal links, and inconsistent terminology | `README.md`, `docs/research/README.md`, `docs/research/prompts/**/*.md` (content edits only, no structural/heading changes, no YAML state blocks) | priyaagrawal2 | Do not edit `PROJECT_STATE.md`'s status block or `DECISION_LOG.md` entries — flag anything that looks wrong there instead of fixing it. |
| C-003 | Draft a related-work paragraph summarizing 3–5 recent papers on selective prediction / conformal prediction in medical imaging | `paper/RELATED_WORK_DRAFT.md` (new file) | ShantanuTripathi2745 | Draft only — citations and claims get checked by the Research Lead before anything moves into the actual manuscript. |
| C-004 | Proofread the protocol docs for typos, broken internal links, and inconsistent terminology | `docs/research/AGENT_WORKTREE_PROTOCOL.md`, `docs/research/DATA_GOVERNANCE_PROTOCOL.md`, `docs/research/EXTERNAL_VALIDATION_PROTOCOL.md`, `docs/research/REPRODUCIBILITY_PROTOCOL.md`, `docs/research/RISK_REGISTER.md`, `docs/research/PUBLICATION_PLAN.md`, `docs/research/phases/**/*.md` (content edits only, no structural/heading changes) | solankisuryansh | Disjoint from C-002's paths — don't touch files outside this list even if you spot a typo there; flag it instead. Do not edit any YAML state blocks. |
| C-005 | Draft a related-work paragraph summarizing 3–5 recent papers on missing-modality robustness in multimodal MRI deep learning | `paper/RELATED_WORK_MISSING_MODALITY_DRAFT.md` (new file) | udaypratapchauhan | Draft only, disjoint file from C-003 — citations and claims get checked by the Research Lead before anything moves into the actual manuscript. |

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
- When a row names an "Assigned to" GitHub username, only that person's agent may claim it.
  When the column is blank or absent (a future, refreshed round of this table), it's first-come —
  `git pull --ff-only` immediately before editing this file, and if the push is rejected as
  non-fast-forward, pull again and check whether someone else already claimed it before retrying;
  never force-push over another person's claim.
