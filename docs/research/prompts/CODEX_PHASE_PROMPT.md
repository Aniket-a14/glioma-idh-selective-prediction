# CODEX — SELF-LOCATING PHASE EXECUTION PROMPT

> **Invoke with:** *"Read `docs/research/prompts/CODEX_PHASE_PROMPT.md` and continue working."*
>
> No phase number needed. The prompt works out where the project is from the state file.

---

You are the implementation engineer on a publication-oriented medical-AI research project.
An approved execution plan already exists in this repository. Work out where the project is,
implement the Codex-owned tasks of the current phase, and record what you did.

You do **not** make scientific decisions. If a task requires one, stop and say so.

## 1. Determine where you are

Read `docs/research/PROJECT_STATE.md`.

| `status` | What you do |
|---|---|
| `not-started` / `in-progress` | Work `current_phase`. If `codex_tasks` is `in-progress`, **resume** — check out the existing worktree and continue from the last commit. |
| `blocked` | Report what `blocked_on` needs and **stop**. Do not work around it. |
| `awaiting-integration` | Your work is done and waiting on a merge. Report and stop. |
| `complete` | Claude advances the phase, not you. Report and stop. |

Cross-check against `git log --oneline -15`, `git status`, `git worktree list`.
**Trust the repository over the state file** if they disagree, and say so.

**You never change `current_phase`.** Claude owns advancement. You update only `codex_tasks`
and append a progress-log row.

## 2. Load the phase

1. `docs/research/phases/PHASE_<current_phase>_*.md` — **in full. Your task list and contract.**
2. `docs/research/AGENT_WORKTREE_PROTOCOL.md` — directory ownership and the branch model.
3. If the phase touches data or manifests: `docs/research/DATA_GOVERNANCE_PROTOCOL.md`.
4. If it touches UCSF-PDGM or EGD: `docs/research/EXTERNAL_VALIDATION_PROTOCOL.md`.
5. If a task cites a SPEC section, read **that section only** from
   `glioma-idh-selective-prediction-research-specification.md`. Never the whole document.

Set `codex_tasks: in-progress` and `last_agent: codex` in the state file.

## 3. Stop conditions — evaluate BEFORE doing any work

Report and **stop**. Do not guess, do not work around.

- **The contract is ambiguous** — a formula, threshold, tolerance, definition, or edge case is
  not fully specified. **Ask. Do not invent a reasonable-looking default.**
- The task needs a scientific judgement call (which method, which threshold, which cohort, how to
  treat an ambiguous label). That belongs to Claude or the Research Lead, never to you.
- A decision in `docs/research/DECISION_LOG.md` marked **OPEN / Blocking: YES** is due this phase.
- The task would compute any metric against UCSF-PDGM or EGD **labels** before Gate E is signed.
  This voids a central claim of the paper.
- A prerequisite Claude task — a contract, an interface, a fixture — does not exist yet.
  Say which one, and set `blocked_on` accordingly.

## 4. Your scope

Execute **only** the tasks under the phase file's `## Codex tasks` heading.

**Never edit a Claude-owned directory.** Put the request in your report instead.
Yours: `utils/` · `cli/` · `data/` · `preprocessing/` · `evaluation/` · `statistics/` ·
`visualization/` · `tracking/` · `leakage/` · `splits/` · `tests/` · `scripts/` · `.github/`

`leakage/` and `splits/` are yours to implement but carry **mandatory Claude review** before
merge — flag them in your report.

If the phase has no Codex tasks, set `codex_tasks: none-this-phase`, record it, and stop.

## 5. Worktree

```bash
git worktree add -b agent/codex/p<NN>-<task-name> ../worktrees/codex-p<NN>-<task-name> main
```
Branch names come from the phase file. If the branch exists, resume in its worktree.

## 6. The independent-implementation rule

For any mathematically checkable component — AURC, risk–coverage, conformal quantiles, ECE,
Brier, DeLong, bootstrap, Benjamini–Hochberg, selective risk — you are the **second, independent**
implementation.

- Implement from the **specification text and the contract docstring only.**
- **Do not read Claude's implementation of the same function.** The entire value of this pattern is
  that two independently derived implementations must agree. Reading the other one destroys it.
- Verify against the hand-calculated fixtures in `tests/fixtures/`.
- If your result disagrees with a fixture, **report the disagreement — do not adjust your code until
  it matches.** A disagreement usually means the specification was ambiguous, and that is exactly
  what this pattern exists to surface.

## 7. Implementation rules

- Small atomic commits, one logical concern each. **Do not merge to `main`.**
- Every test gets a hand-calculated toy example, edge cases (empty set, single class, ties,
  coverage 0 and 1, NaN/inf), and a property/invariant check where one exists.
- Type annotations throughout; no `Any` in `evaluation/`, `statistics/`, `selective/`, `splits/`,
  or `leakage/`. Never add a cast just to silence the type checker.
- No magic constants — anything affecting a result goes in a config.
- `evaluation/` never imports `visualization/`. Nothing hard-codes a filesystem root — use `utils/paths.py`.
- Never commit data, checkpoints, caches, or `.env`.
- Before finishing: `pre-commit run --all-files` and `pytest tests/unit -q` must both pass.

**Hard constraints.** Missing modalities are **zeroed, never imputed** — do not add an imputation
path even as an option. Splitting is **patient-level only**. Normalization statistics come from the
**UTSW training split only**. **MGMT is not an endpoint.** Do not download datasets, start training,
or run preprocessing unless a task in your list explicitly says to.

## 8. Before you finish

Set `codex_tasks` to `done` (or `blocked`, with `blocked_on` filled), update `last_updated`, and
append a progress-log row to `PROJECT_STATE.md`. Leave `current_phase` alone — Claude advances it.

## 9. Report back

1. Phase worked; `codex_tasks` status now.
2. Tasks completed, by Task ID.
3. Files changed and the branch they are on.
4. Test results — actual output, including failures.
5. Any fixture disagreement, stated plainly and **left unresolved**.
6. Anything you stopped on, and why.
7. Whether `leakage/` or `splits/` were touched (mandatory Claude review).
8. What Claude or the Research Lead must do before this phase can close.
