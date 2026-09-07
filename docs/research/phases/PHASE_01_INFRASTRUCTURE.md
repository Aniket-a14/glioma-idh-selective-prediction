# Phase 01 — Storage, Environment, and GPU Infrastructure Validation

**Duration:** ~4 days · **Gate:** C-prerequisite · **Compute:** CPU + one GPU probe

## Scientific purpose
Establish that the compute environment can actually run the planned experiments *before* the plan commits to patch sizes, batch sizes, and run counts. Hardware constraints that force architecture changes must be discovered now and checked against the specification, not discovered mid-training and silently accommodated.

## Engineering purpose
Portable symlink-based storage; verified environment on both machines; captured hardware fingerprint; the seven-step pre-training authorization harness.

## Specification requirements satisfied
SPEC §3.1 (16–24 GB VRAM envelope), §3.2 (250–500 GB working storage), §3.5 (≥32 GB RAM), §3.7 (local sufficient; cloud optional fallback).

## RQs / claims addressed
None directly. Gates all GPU work for RQ1–RQ4.

## Entry criteria
Phase 00 complete; `paths.py` merged; external SSD physically available; SSH access to the GPU server confirmed.

## Inputs
`utils/paths.py`; `.env.example`; SSD mount point; GPU server credentials.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T01.1 | `scripts/bootstrap_storage.py` — idempotent symlink creation | A | — | Codex | CPU | no | T01.2 |
| T01.2 | SSD directory tree; verify free space ≥ 500 GB | A | — | Human | none | no | Phase 02 |
| T01.3 | `scripts/capture_environment.py` — full hardware/software fingerprint | A | — | Codex | CPU | yes | T01.5 |
| T01.4 | Run environment capture on **both** machines; record results | A | — | Human | GPU probe | no | T01.5 |
| T01.5 | **Verify MONAI/PyTorch/CUDA compatibility against measured driver**; pin `pyproject.toml` | A | — | Claude | none | no | Phase 06 |
| T01.6 | Install locked environment on both machines; confirm identical lock hash | A | — | Human | CPU | no | Phase 06 |
| T01.7 | GPU memory benchmark: SegResNet-scale forward/backward at 96³ and 128³ | A | — | Claude | GPU | no | Phase 06 |
| T01.8 | `tests/integration/test_storage.py` — broken symlink, missing target, refuses overwrite | A | — | Codex | CPU | yes | — |
| T01.9 | Define recovery runbooks: SSH drop, OOM, crash, partial checkpoint, power loss | A | — | Claude | none | yes | Phase 06 |

**T01.1 requirements** (master prompt, verbatim): idempotent · refuses dangerous overwrites · verifies target exists · clearly reports broken symlinks · supports macOS and Linux · no machine-specific absolute path committed · `.env` gitignored · `.env.example` provided · Pathlib-based · generated data cannot enter Git.

**T01.5 is a genuine gate, not a formality.** Actual VRAM, CUDA runtime, and driver version are **unknown**. If the measured VRAM is below the SPEC §3.1 envelope of 16 GB, the patch size or batch size must change — and that change is recorded as a deviation and checked against the specification (SPEC §4.2 specifies 96³ or 128³ crops), **not silently applied**.

## Human allocation
**A:** all. **B/C:** none. Storage and environment are single-operator tasks by nature.

## Claude tasks
T01.5 (compatibility reasoning across three interacting version constraints), T01.7 (memory benchmark interpretation — what the number means for the training plan), T01.9 (recovery design).

## Codex tasks
T01.1, T01.3, T01.8 — bounded, testable tooling.

## Parallelization map
```
T01.1 ─> T01.2 ─────────────────> Phase 02 may begin
T01.3 ─> T01.4 ─> T01.5 ─> T01.6 ─> T01.7
T01.8, T01.9 in parallel throughout
```

## Worktrees / branches
```
agent/codex/p01-bootstrap-storage    agent/codex/p01-env-capture
agent/claude/p01-compat-and-recovery
```

## Files / modules expected
`scripts/bootstrap_storage.py`, `scripts/capture_environment.py`, `pyproject.toml` (**now pinned**), lock file, `tests/integration/test_storage.py`, `docs/research/protocols/RECOVERY_RUNBOOK.md`, `docs/research/protocols/ENVIRONMENT_RECORD.md`.

## Data required
None. Storage is prepared but empty.

## Compute required
CPU throughout; one short GPU session for T01.4 and T01.7.

## Outputs / artifacts
Working `data/` and `artifacts/` symlinks on both machines · environment fingerprint for both machines · locked dependency file with matching hashes · GPU memory benchmark table (patch size × batch size × peak VRAM) · recovery runbook.

## Tests
Storage: idempotence (run twice, same result); refuses to overwrite a non-symlink; detects and reports a broken symlink; fails clearly when `GLIOMA_STORAGE_ROOT` is unset. Environment: capture produces every required field or fails loudly.

## Quality gates
Gate B for merges. **Gate C cannot be satisfied by any later phase until Phase 01 exits** — no scientific run may proceed without a recorded environment.

## Scientific validation
The measured VRAM and the benchmark table are compared against SPEC §3.1's 16–24 GB envelope and §4.2's 96³/128³ patch specification. Any shortfall produces a decision-log entry with the proposed accommodation, reviewed against the specification before Phase 06 begins.

## Acceptance criteria
1. `bootstrap_storage.py` runs twice on both machines with identical results and zero errors.
2. `data/` and `artifacts/` resolve to the correct SSD locations; `git status` shows neither as untracked content.
3. Free space on the storage root ≥ 500 GB (SPEC §3.2 upper estimate).
4. Environment fingerprint captured on both machines, containing all fourteen required fields (nvidia-smi, GPU model, VRAM, CUDA runtime, driver, CPU, RAM, free disk, Python, PyTorch, MONAI, `torch.cuda` capability, git SHA, lock hash).
5. Identical dependency-lock hash on both machines.
6. GPU benchmark table recorded for {96³, 128³} × {batch 1, 2}, with peak VRAM per cell.
7. `torch.cuda.is_available()` is `True` on the server and the reported capability matches the installed PyTorch build.
8. Recovery runbook covers all six failure modes.

## Failure conditions
Measured VRAM < 16 GB (triggers a specification-checked accommodation decision) · MONAI/PyTorch/CUDA incompatibility with no compatible combination · SSD free space < 250 GB (below SPEC §3.2 lower bound) · symlink bootstrap not idempotent.

## Rollback / recovery
Storage bootstrap is idempotent and reversible (remove symlinks, re-run). Environment can be rebuilt from the lock file. No scientific artifacts exist to lose.

## Risks
R-H04 (OOM — this phase exists to measure it in advance), R-H05 (server downtime), R-M07 (SSD failure — nothing irreplaceable is stored yet).

## Decisions requiring Research Lead approval
Final Python/PyTorch/MONAI versions · patch size if the benchmark forces a change from 128³ · whether cloud GPU fallback is provisioned now or deferred.

## Exit criteria
All acceptance criteria met; `ENVIRONMENT_RECORD.md` committed; benchmark table committed; Gate B passed.

## Dependencies for next phase
Phase 02 needs T01.2 (SSD tree) to have somewhere to download into. Phase 06 needs T01.5–T01.7 complete.
