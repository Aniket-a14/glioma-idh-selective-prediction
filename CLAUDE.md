# CLAUDE.md

## Project map

Calibrated selective prediction for MRI-based glioma IDH classification — an empirical trustworthiness study, not a new-architecture paper. Current phase is the live source of truth in `docs/research/PROJECT_STATE.md`; this file is not.

Required reading, in order: `glioma-idh-selective-prediction-research-specification.md` (scientific source of truth), `docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md` (execution source of truth), `docs/research/README.md` (start here), `docs/research/phases/` (phase-by-phase detail).

New machine or new collaborator: read `docs/research/prompts/SETUP_PROMPT.md` and follow it — it clones, creates the virtualenv, installs the package and git hooks, and verifies everything CI checks. On Windows, run it inside WSL2. Datasets and artifacts are never committed; they live on an external SSD reached through the `data/` and `artifacts/` symlinks that same prompt sets up.

Continuing research work: `docs/research/prompts/CLAUDE_PHASE_PROMPT.md` ("read this and continue working") figures out the current phase from `PROJECT_STATE.md` and does the next piece of Claude-owned work itself. Picking up small side-work instead: `docs/research/prompts/CONTRIBUTOR_PROMPT.md` + `docs/research/CONTRIBUTOR_TASKS.md`.

Before touching external data or governed protocols: `docs/research/EXTERNAL_VALIDATION_PROTOCOL.md` before UCSF-PDGM or EGD, `docs/research/DATA_GOVERNANCE_PROTOCOL.md` before downloading anything. Three things that would invalidate this project outright: patient-level leakage across UTSW / UCSF-PDGM / EGD / BraTS / TCGA, looking at external performance before Gate E, and scope creep into architecture search.

## How to work

Do the acceptance criteria the phase file actually lists — every one, verified, not assumed — with tests and docs in the same commit. That is the whole standard here; there is no separate bar to hit beyond what the phase file and the quality gates already require.

The one direction *not* to take that seriously in: don't do more than the phase file scopes. **Scope creep into architecture search is one of the three things that invalidates this project** (see Project map). "More thorough" here means more rigorously verified against the stated acceptance criteria, not more features, more abstraction, or more than was asked. A bug fix doesn't need surrounding cleanup; a config tweak doesn't need a new subsystem.

You can outsource the typing. You cannot outsource the understanding. Before calling anything done, be able to explain why it's correct and exactly where it would break. Tests passing is not understanding.

Hit an ambiguity, a contradiction, or a judgment call the phase file doesn't resolve? That's `DECISION_LOG.md`, not a coin flip — see **Confusion protocol** below. Never silently resolve it and never silently expand scope to route around it.

## Roles and branches

Full detail: `docs/research/AGENT_WORKTREE_PROTOCOL.md`. Three branch namespaces, three roles, never mixed:

```
agent/claude/pXX-task-name      # Claude's phase-file tasks
agent/codex/pXX-task-name       # Codex's phase-file tasks
contrib/<github-username>/slug  # the team's other 5 collaborators, off the critical path
```

Worktrees live outside the repo (`../worktrees/<role>-<task-name>`), created from a known `main` commit, one branch per worktree. Small atomic commits, one logical concern each — never a "phase complete" mega-commit.

**Who merges:** `main` is protected — PR plus one review, no self-merge, same for everyone including the 5 contributors. `PROJECT_STATE.md`'s `integration_mode` field governs Claude/Codex only: `research-lead` (default) means an agent leaves branches ready and stops; `agent` means it merges itself with `--no-ff` after Gate B passes. **Phases 05, 11, and 12 always require the Research Lead**, whatever that field says — they freeze the pre-registration, authorize external evaluation, and run the single external evaluation, none of which is reversible.

The Research Lead (Aniket) can and does commit operational metadata directly to `main` — `PROJECT_STATE.md`, this file, cross-repo doc wiring — and can explicitly authorize an agent to do the same for a specific piece of work in a specific request. That authorization is per-request, not standing; don't infer it from a past instance.

**Directory ownership** (`AGENT_WORKTREE_PROTOCOL.md` §3): `models/`, `training/`, `selective/`, `uncertainty/`, `calibration/` (design) and `configs/` are Claude's; `preprocessing/`, `data/`, `evaluation/`, `statistics/`, `visualization/`, `utils/`, `cli/`, `tracking/`, `scripts/`, `tests/`, `.github/workflows/` are Codex's; `leakage/` and `splits/` are Codex-implemented with mandatory Claude review; `paper/` is human-owned, agents draft into it only when asked. No directory has two owners in the same phase. `CONTRIBUTOR_TASKS.md` is the one sanctioned exception — it hands a narrow, explicitly-scoped slice of an otherwise-owned directory to a contributor for that task only.

**The independent-implementation pattern** — the highest-value use of two agents, applied to every mathematically checkable component (AURC, risk-coverage, conformal quantiles, ECE, Brier, DeLong, bootstrap, BH correction, selective risk): Claude writes the contract (signature, docstring with the mathematical definition, hand-calculated toy fixtures in `tests/fixtures/`); Codex implements from the specification text alone, never seeing Claude's implementation; both must agree within a stated tolerance against the shared fixtures. Disagreement is investigated and recorded before either merges — it usually means the spec was ambiguous, which is worth knowing on its own.

Hard rules that don't bend: no agent edits another agent's active worktree, ever; no force-pushing a shared branch; never commit datasets, checkpoints, caches, or `.env`; contributors never touch `PROJECT_STATE.md`, `DECISION_LOG.md`, dataset splits/manifests, or `.env`, no task can override that.

## Scientific invariants — never violate

IDH is the primary endpoint; **1p/19q is exploratory only**; **MGMT is not an endpoint**. UTSW-Glioma is the only development cohort — UCSF-PDGM and EGD are external test sets, never development sets, never split (evaluated whole). Splitting is patient-level, stratified on IDH, computed after de-duplication. Missing modalities are **zeroed, never imputed**. Normalization statistics come from the UTSW training split only, never pooled. **No architecture search.** AUROC is never reported without ECE/Brier/AURC/coverage alongside it. **Negative results are valid** — never re-run, re-tune, or re-scope an experiment because its outcome refutes a claim. `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` stays `0` until Gate E; nothing computes a metric against UCSF-PDGM or EGD labels before then.

## Task model — the phase file is the triage

Work is organized by phase (`docs/research/phases/PHASE_NN_*.md`), not by ad hoc sizing. Each phase file already states owner, executor, compute needs, and acceptance criteria per task — that table is the triage. There is no separate small/medium/large ceremony to run on top of it.

**Quality gates** (`docs/research/README.md`): Gate A on every commit (pre-commit, `scripts/check_invariants.py`, `pytest tests/unit -q`); Gate B on every merge to `main` (full CPU suite, mypy, radon, docs updated); Gate C before any scientific run (clean tree, valid config, frozen manifests, environment recorded); Gate D at phase completion (every acceptance criterion met, independent review); Gate E, the strictest, authorizes external evaluation exactly once; Gate F freezes results for publication.

Small work outside any phase's scope (a doc fix, a typo, a config correction) still gets Gate A run against it before committing. State which gate(s) applied in the report — don't invent a bigger ritual than the change needs, and don't skip the one that applies.

## Tests

Gate A and Gate B above are the two lanes; there's no third. Every behavior change ships its test in the same commit — no "tests later." Mathematically checkable components follow the independent-implementation pattern (above), not solo unit tests written by the same agent that wrote the implementation, since that catches a different error class (a shared wrong mental model of the formula) that self-authored tests structurally cannot.

## Verify before shipping

Anything a reader or the next agent will run — a command, a config value, a path, a claimed test count — gets actually run or checked before it ships, not reasoned about. A claim about data (a count, a hash, a split size) gets checked against the actual manifest, not assumed from memory of an earlier draft. If something can't be verified in this session (needs hardware, needs a human), say so plainly and name what would settle it — don't launder an unchecked claim into confident prose.

## Tie every change to something checkable

Every task traces back to a phase file's acceptance criteria, a SPEC requirement (`SPEC_TRACEABILITY_MATRIX.md`), or an explicit Research Lead request. "It works" is not a stopping point — "acceptance criterion N, verified by running X, output Y" is.

## Tech choices

Logged in `DECISION_LOG.md`, not decided silently (e.g. D-013: Hydra over OmegaConf/pydantic-settings). A new runtime dependency needs a decision-log entry if it's a genuine tech choice, and `pyproject.toml` dependency edits are Research-Lead territory per `AGENT_WORKTREE_PROTOCOL.md` §6 — agents *request* a dependency in the PR description rather than adding it unilaterally, except where an already-logged decision (like D-013) requires it to actually run, which is itself worth calling out explicitly when it happens.

Search before building: check for an existing library or pattern first (Layer 1), then a newer one with real traction (Layer 2), and only write custom code with a documented reason when the conventional approach genuinely doesn't apply here (Layer 3). Check installed Claude Code skills before reimplementing something one already covers.

## Confusion protocol — this is what `DECISION_LOG.md` is for

Stop and log rather than guess when: a decision in `DECISION_LOG.md` marked `OPEN` and `Blocking: YES` is due this phase; the previous phase's exit criteria aren't actually met; required data, credentials, or hardware is absent; a task would compute a metric against UCSF-PDGM/EGD labels before Gate E; or a task looks like it would change *what* the science asks rather than *how* it's engineered. Name the ambiguity in one sentence, present the alternatives with a recommendation, append it to `DECISION_LOG.md`, and stop — do not pick one and proceed. These exist precisely because they need a human.

## Completion status

At the end of a task, report one of: **DONE** (acceptance criteria verified, not assumed, tests/gates run, files named); **DONE_WITH_CONCERNS** (done, but something needs the Research Lead's attention — name it); **BLOCKED** (a Confusion Protocol stop, or a Gate C prerequisite missing); **NEEDS_CONTEXT** (state exactly what's missing). "Partially done" isn't a status.

## Safety

- Never commit secrets, datasets, checkpoints, caches, or `.env` — verify `.gitignore` before any commit that touches those.
- Never touch `data/` or `artifacts/` except through `utils/paths.py` and `scripts/bootstrap_storage.py` — nothing hard-codes a filesystem root.
- `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` stays `0`. Never set it to `1` as part of any task — it flips exactly once, by the Research Lead, at Gate E.
- Never push to `main` directly unless the Research Lead has explicitly authorized it for that specific piece of work.
- Never skip pre-commit hooks with `--no-verify`. If a hook fails, fix the underlying issue.
- Never run destructive git operations (`reset --hard`, `clean -f`, force-push) without explicit confirmation, and never on a shared branch or `main`.
- Never merge your own PR unless the Research Lead says so.

## How Aniket wants to be talked to

- Direct. Short. Concrete. No preamble.
- Specific file names, function names, line numbers — `src/glioma_selective/utils/paths.py:47`, not "there's an issue in the path resolver."
- No AI vocabulary (delve, crucial, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, pivotal, landscape, tapestry, underscore, foster, showcase, intricate, vibrant, fundamental, significant, interplay).
- No banned phrases: "here's the kicker", "here's the thing", "plot twist", "let me break this down", "the bottom line", "make no mistake".
- If something is broken, say so plainly.
- End responses with the next action, not a recap of what was just done.
