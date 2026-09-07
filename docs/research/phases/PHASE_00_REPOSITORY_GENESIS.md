# Phase 00 — Repository Genesis, Specification Extraction, Governance, Tooling

**Duration:** ~3 days · **Gate:** B · **Compute:** none

## Scientific purpose
Convert the specification from prose into machine-checkable invariants before any code can violate them. The scientific invariants SI-01…SI-15 become CI checks, config-schema constraints, and test targets in this phase — after this, violating them requires deliberately disabling something rather than merely forgetting.

## Engineering purpose
Create the repository, the quality toolchain, and the configuration system. Establish the single canonical path abstraction so that no script ever hard-codes a filesystem root.

## Specification requirements satisfied
SPEC §1.3 (RQs), §1.4 (claims), §2 (dataset roles), §8.1–8.2 (novelty boundary) — extracted into `docs/research/`. §4.11 prohibitions encoded as CI checks.

## RQs / claims addressed
None directly. Establishes the traceability substrate for all of RQ1–RQ4 and C1–C6.

## Entry criteria
- Both source documents present.
- Master execution plan approved by the Research Lead.

## Inputs
`glioma-idh-selective-prediction-research-specification.md`; `Master_Research_Execution_prompt.md`; `docs/research/` corpus.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T00.1 | `git init`, branch protection convention, `.gitignore`, `.env.example` | A | — | Human | none | no | all |
| T00.2 | `pyproject.toml` skeleton — **no version pins yet** (Phase 01 verifies CUDA/MONAI compat first) | A | — | Codex | none | yes | T00.3 |
| T00.3 | Ruff + mypy + pytest + pytest-cov + Radon configuration | A | — | Codex | none | yes | T00.6 |
| T00.4 | `pre-commit` hooks incl. detect-secrets, codespell | A | — | Codex | none | yes | — |
| T00.5 | `src/glioma_selective/utils/paths.py` — **THE canonical path abstraction** | A | — | Claude | none | no | Phase 01 |
| T00.6 | CI workflows: Gate A (push) and Gate B (PR) | A | — | Codex | none | yes | — |
| T00.7 | Config system decision + skeleton (Hydra/OmegaConf) | A | — | Claude | none | no | Phase 05 |
| T00.8 | Invariant CI checks: no `mgmt` endpoint; no hard-coded `/Volumes/`,`/mnt/`,`../../data`; no `evaluation/`→`visualization/` import | A | — | Codex | none | yes | — |
| T00.9 | `paper/` continuously-maintained skeleton incl. `NEGATIVE_RESULTS.md`, `LIMITATIONS.md` | C | A (+1d) | Claude | none | yes | Phase 14 |
| T00.10 | Experiment registry skeleton `experiments/REGISTRY.md` | A | — | Codex | none | yes | Phase 06 |

**T00.5 is the load-bearing task.** `paths.py` resolves `GLIOMA_STORAGE_ROOT` / `GLIOMA_DATA_ROOT` / `GLIOMA_ARTIFACT_ROOT` from the environment, returns `pathlib.Path` objects, and is the only module permitted to touch filesystem roots. Everything downstream imports it. Frozen after Phase 01; later changes need Research Lead approval.

## Human allocation
**A:** all repository and governance decisions. **C:** `paper/` skeleton, bibliography scaffold. **B:** none (Phase 02 is B's start). **D–F:** none.

## Claude tasks
T00.5 (path abstraction — cross-cutting, every module depends on its interface), T00.7 (config system — experiment definitions are scientific), T00.9 (paper skeleton — manuscript-facing).

## Codex tasks
T00.2, T00.3, T00.4, T00.6, T00.8, T00.10 — all bounded tooling with clear acceptance criteria.

## Parallelization map
```
T00.1 ──┬─> T00.2 ─> T00.3 ─┬─> T00.6
        ├─> T00.4           │
        ├─> T00.5 (Claude) ─┘
        ├─> T00.7 (Claude)
        ├─> T00.8, T00.10 (Codex)
        └─> T00.9 (Claude)
```
Claude and Codex work concurrently throughout: Claude in `utils/`, `configs/`, `paper/`; Codex in tooling and CI. No shared files.

## Worktrees / branches
```
agent/claude/p00-path-abstraction    ../worktrees/claude-p00-path-abstraction
agent/claude/p00-config-system       ../worktrees/claude-p00-config-system
agent/codex/p00-tooling              ../worktrees/codex-p00-tooling
agent/codex/p00-ci                   ../worktrees/codex-p00-ci
```
Merge order: tooling → path abstraction → config → CI → paper skeleton.

## Files / modules expected
`pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/{gate_a,gate_b}.yml`, `src/glioma_selective/utils/paths.py`, `src/glioma_selective/utils/__init__.py`, `configs/` skeleton, `tests/unit/test_paths.py`, `paper/{NEGATIVE_RESULTS,LIMITATIONS,REGISTRY}.md`, `experiments/REGISTRY.md`.

## Data required
None.

## Compute required
None.

## Outputs / artifacts
Initialized repository at a tagged `phase-00-complete` commit; passing Gate A and Gate B; the planning corpus committed.

## Tests
`test_paths.py`: resolution from environment; missing-variable error is clear and actionable; `Path` types returned; no absolute path leaks into the return for an unset root. Config parsing round-trip test. CI self-test that the invariant greps in T00.8 actually fire on a planted violation.

## Quality gates
**Gate A** on every commit. **Gate B** before merging to `main`.

## Scientific validation
Independent read-back: a person who has not read the specification reads `MASTER_RESEARCH_EXECUTION_PLAN.md` §2–8 and correctly states the primary endpoint, the two stressor conditions, and why MGMT is excluded. If they cannot, the extraction is inadequate.

## Acceptance criteria
1. `git log` shows the repository initialized with the planning corpus committed.
2. `pre-commit run --all-files` exits 0.
3. `pytest tests/unit -q` exits 0 with ≥1 real test.
4. CI Gate A and Gate B both green.
5. `paths.py` passes its test suite; grep finds zero hard-coded `/Volumes/`, `/mnt/`, or `../../data` in `src/`.
6. T00.8 invariant checks demonstrably fail on a planted violation and pass on the clean tree.
7. `SPEC_TRACEABILITY_MATRIX.md` lists every RQ, every claim C1–C6, and every SPEC § requirement, with no empty cells other than the reverse-trace table.
8. `DECISION_LOG.md` contains D-001…D-012.

## Failure conditions
Path abstraction leaks machine-specific paths · CI does not actually block on failure (a green check that never fails is worse than none) · traceability matrix has empty cells.

## Rollback / recovery
Phase 00 produces no scientific artifacts; any part may be redone freely. Reset the branch and redo.

## Risks
R-C08 (scope creep — resist building research functionality here), R-M01 (agent file conflicts — mitigated by disjoint ownership).

## Decisions requiring Research Lead approval
Config system choice (Hydra vs. plain OmegaConf vs. pydantic-settings) · coverage thresholds per module · which invariant checks block CI vs. warn.

## Exit criteria
All acceptance criteria met; Gate B passed; `phase-00-complete` tag created.

## Dependencies for next phase
Phase 01 needs `paths.py` merged and stable. Phase 02 needs nothing from here and **may start in parallel** — indeed the EGD DUA should be submitted on Phase 02 day 1 regardless of Phase 00 status.
