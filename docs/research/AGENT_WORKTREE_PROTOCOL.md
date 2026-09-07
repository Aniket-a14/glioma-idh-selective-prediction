# AGENT / WORKTREE PROTOCOL

How Claude and Codex work in parallel without corrupting each other or `main`.

---

## 1. Branch model

`main` is a protected integration branch. **Neither agent commits to it directly.** Only the Research Lead merges.

```
agent/claude/pXX-task-name      # e.g. agent/claude/p07-conformal-design
agent/codex/pXX-task-name       # e.g. agent/codex/p07-ece-implementation
```

Worktrees live outside the repository so an agent cannot accidentally read or edit another's tree:

```
../worktrees/claude-pXX-task-name
../worktrees/codex-pXX-task-name
```

---

## 2. Command templates

```bash
# --- create a worktree (from a known main commit) -------------------------
git fetch origin
git worktree add -b agent/codex/p04-n4-correction \
    ../worktrees/codex-p04-n4-correction main

# --- work happens there; small atomic commits ------------------------------
cd ../worktrees/codex-p04-n4-correction
# ... edits ...
git add src/glioma_selective/preprocessing/n4.py tests/unit/test_n4.py
git commit -m "preprocessing: N4 bias-field correction with configurable iterations"

# --- Gate A locally before requesting integration --------------------------
pre-commit run --all-files
pytest tests/unit -q

# --- integrate (RESEARCH LEAD ONLY, from the main tree) --------------------
cd /path/to/Glioma
git checkout main
git merge --no-ff agent/codex/p04-n4-correction
pytest tests/ -q -m "not gpu"        # Gate B

# --- clean up --------------------------------------------------------------
git worktree remove ../worktrees/codex-p04-n4-correction
git branch -d agent/codex/p04-n4-correction
git worktree prune
```

---

## 3. Directory ownership

**No directory has two owners in the same phase.** This table is the authority; a phase file may narrow it but never contradict it.

| Directory | Default owner | Notes |
|---|---|---|
| `src/glioma_selective/models/` | **Claude** | Architecture reasoning |
| `src/glioma_selective/training/` | **Claude** | Loop, checkpointing, resume |
| `src/glioma_selective/calibration/` | **Claude** (design) → Codex (impl) | Split by task, never concurrent |
| `src/glioma_selective/selective/` | **Claude** | Core scientific logic |
| `src/glioma_selective/uncertainty/` | **Claude** | |
| `src/glioma_selective/preprocessing/` | **Codex** | Bounded, testable components |
| `src/glioma_selective/data/` | **Codex** | Cohort adapters |
| `src/glioma_selective/leakage/` | **Codex** (impl), Claude (review) | High scientific risk — joint review mandatory |
| `src/glioma_selective/splits/` | **Codex** (impl), Claude (review) | Same |
| `src/glioma_selective/evaluation/` | **Codex** | Metrics |
| `src/glioma_selective/statistics/` | **Codex** | |
| `src/glioma_selective/visualization/` | **Codex** | |
| `src/glioma_selective/utils/` | **Codex** | Paths, seeding, IO |
| `src/glioma_selective/cli/` | **Codex** | Thin wrappers |
| `src/glioma_selective/tracking/` | **Codex** | |
| `tests/` | **Codex** | Except tests for Claude-owned modules, written by Claude |
| `configs/` | **Claude** | Experiment definitions are scientific |
| `scripts/` | **Codex** | |
| `docs/research/` | **Claude** | |
| `paper/` | **Human (A/C)** | Agents draft into it only when asked |
| `.github/workflows/` | **Codex** | |

---

## 4. The independent-implementation pattern

The single highest-value use of two agents. Applied to **every mathematically checkable component**: AURC, risk–coverage, conformal quantiles, ECE, Brier, DeLong, bootstrap, BH correction, selective risk.

1. **Claude** writes the contract: function signature, docstring with the mathematical definition, and hand-calculated toy fixtures in `tests/fixtures/` — small enough to verify with a pencil.
2. **Codex** implements *from the specification text and the contract alone*, in its own worktree, **without seeing Claude's implementation**.
3. Both implementations run against the shared fixtures. **They must agree to within a stated tolerance.**
4. Disagreement is investigated before either is merged. The disagreement itself is recorded — it usually means the specification was ambiguous, which is worth knowing.

This catches the error class that unit tests written by the implementer cannot: a wrong shared mental model of the formula.

---

## 5. Merge order

Within a phase, merge in dependency order, never chronological:

```
utils/ paths  →  data adapters  →  leakage/splits  →  preprocessing
      →  models  →  training  →  calibration/uncertainty  →  selective
      →  evaluation  →  statistics  →  visualization  →  cli/scripts  →  docs
```

Integration tests run after each merge, not batched at the end.

---

## 6. Predictable conflict regions

| Region | Why | Mitigation |
|---|---|---|
| `pyproject.toml` dependencies | Both agents add packages | Only the Research Lead edits; agents *request* dependencies in the PR description |
| `configs/` schema | Shared structure | Claude owns; Codex proposes via issue |
| `src/glioma_selective/utils/paths.py` | Everything imports it | Frozen after Phase 01; changes require Research Lead approval |
| `tests/fixtures/` | Shared test data | Append-only; never edit an existing fixture (it may pin a verified result) |
| `.pre-commit-config.yaml`, CI | Both touch tooling | Codex owns; Claude reviews |

---

## 7. Hard rules

- Both branches originate from a **known** `main` commit, recorded in the task record.
- Small atomic commits, one logical concern each. **No giant "phase complete" commits.**
- No force-pushing shared branches.
- **No agent edits another agent's active worktree.** Ever.
- Never commit datasets, checkpoints, caches, or `.env`.
- Integration happens only after the task's acceptance criteria pass.
- Merge conflicts are resolved by the Research Lead, not by an agent.
- **Record the git SHA for every scientifically meaningful experiment.** A dirty tree blocks Gate C.
- An agent that needs a file outside its ownership opens a task for the owner rather than editing it.
