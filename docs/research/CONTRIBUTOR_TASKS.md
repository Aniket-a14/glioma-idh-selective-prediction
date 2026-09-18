# CONTRIBUTOR TASKS

A standing backlog of small, bounded, off-critical-path work for the team's five other
collaborators — Akshita1395, priyaagrawal2, ShantanuTripathi2745, solankisuryansh,
udaypratapchauhan — and whichever AI agent they're running (Antigravity, Codex free tier, or
anything else). The critical research path (phases in `docs/research/phases/`) stays owned by
the Research Lead, Claude, and Codex per `AGENT_WORKTREE_PROTOCOL.md`. This file is the *only*
sanctioned exception to that protocol's directory-ownership table — a task listed here may touch
exactly the paths it names, nothing else.

**Agents: start at `docs/research/prompts/CONTRIBUTOR_PROMPT.md`, not here.** That prompt tells
you how to pick up your row safely. Reading this file alone is not enough context to act on.

**This file is edited only by the Research Lead — never by a contributor or a contributor's
agent, not even to claim a row or add a PR link.** That used to be a contributor step, and it was
the actual cause of a real merge conflict (PR #4 and PR #5 both touched this file's table and
collided). Every row below is now pre-assigned — person, branch name, and allowed paths are all
fixed before any agent starts — so there is nothing left for a contributor to write here. If your
agent thinks it needs to edit this file, it has misread its instructions; it should stop and say
so instead.

**Humans: this file is curated by the Research Lead, weekly**, ahead of the Friday capstone
discussion. Add rows here only when you (Research Lead) have picked a bounded, safe piece of
work off the critical path, picked the exact person, and filled in an exact branch name — never
let a contributor agent invent its own scope or its own branch name.

---

## Open

**Every row is pre-assigned to a specific person and a specific branch name.** There is no
first-come claiming and nothing to edit to "claim" a row — an agent claims a task simply by
reading it and starting work on the named branch. This removes two failure modes at once: two
agents racing for the same row, and two agents' edits to this file colliding with each other.

**Agents: only act on the row whose "Assigned to" is your operator's GitHub username** (confirm
it with `gh api user -q .login` — don't trust an assumption or a name in chat, confirm it against
the actual authenticated account). If no remaining row names your operator, stop and report that
rather than acting on someone else's row or inventing a new task.

| ID | Task | Allowed paths | Assigned to | Branch | Notes |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## In progress

| ID | Task | Assigned to | Branch | PR |
|---|---|---|---|---|
| — | — | — | — | — |

## Done

| ID | Task | Closed by | PR | Merged |
|---|---|---|---|---|
| C-001 | Add edge-case unit tests for `utils/paths.py` | solankisuryansh | [#1](../../../pull/1) | 2026-09-15 |
| C-002 | Proofread top-level docs for typos, broken internal links, and inconsistent terminology | priyaagrawal2 | [#2](../../../pull/2) | 2026-09-17 |
| C-004 | Proofread the protocol docs for typos, broken internal links, and inconsistent terminology | Akshita1395 | [#4](../../../pull/4) | 2026-09-18 |
| C-003 | Draft a related-work paragraph summarizing 3–5 recent papers on selective prediction / conformal prediction in medical imaging | ShantanuTripathi2745 | [#5](../../../pull/5) | 2026-09-18 |
| C-005 | Draft a related-work paragraph on missing-modality robustness | udaypratapchauhan | — (no PR) | closed 2026-09-18 by Research Lead decision, not completed — round closed out to start Phase 01; re-queue as a fresh row if this content is still wanted later |

---

## Hard rules (same as every other agent role in this repo)

- **Never edit this file.** Assignment, branch naming, and PR-link tracking are Research-Lead-only
  — see the note at the top. This is the one rule in this list that's new relative to how the
  first round worked, and it exists specifically to stop contributor branches from conflicting
  with each other on this table.
- Never touch `PROJECT_STATE.md`, `DECISION_LOG.md`, dataset splits/manifests, `.env`, or anything
  under `data/`/`artifacts/`.
- Never merge your own PR. Every PR here goes through the same branch protection as everyone
  else's: 1 review, conversation resolution, Research Lead decides.
- Never work outside the "Allowed paths" column of your assigned task. If the task turns out to
  need more, stop and say so in the PR description rather than expanding scope silently.
- One assigned task at a time per person. If you finish early and want more, ask the Research
  Lead for a new row rather than picking your own.
- Use the exact branch name in the "Branch" column — don't invent your own slug. This, plus each
  row's disjoint "Allowed paths", is what guarantees no two contributors' work can collide at
  merge time: different branch, different files, and (per the rule above) nobody but the Research
  Lead ever writes to this table.
