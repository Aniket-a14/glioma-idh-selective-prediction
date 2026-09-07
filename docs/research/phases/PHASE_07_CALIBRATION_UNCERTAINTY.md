# Phase 07 — Calibration and Uncertainty Mechanisms

**Duration:** ~14 days · **Gate:** C · **Compute:** GPU (ensemble training)

## Scientific purpose
Implement the four mechanisms the study compares, as **independent, separately testable modules**, so that a failure of one is attributable to that mechanism rather than to shared plumbing. **D-002 resolves here** — the conformal method's identity must be fixed before any quantile is fitted.

## Engineering purpose
Post-hoc calibration and uncertainty layers that operate on frozen checkpoints and write to frozen prediction artifacts.

## Specification requirements satisfied
SPEC §4.6 (four compared methods; conformal as primary and why), §4.2 (post-hoc calibration; thresholds from a held-out calibration split, **never** the test set), §5.2 (Brier, ECE, reliability as secondary metrics), §9 steps 5–6.

## RQs / claims addressed
RQ3 (internal calibration baseline); supplies M2, M3, M4, M5 for RQ1, RQ2, and C1–C6.

## Entry criteria
Phase 06 complete; R2 checkpoint frozen and hashed; calibration-split predictions available.

## Inputs
R2 checkpoint; frozen calibration-split predictions; pre-registered α grid and abstention definition (Phase 05).

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T07.1 | **Resolve D-002** — split CP vs. CRC; fix the primary instrument | A | — | Claude | none | no | T07.5 |
| T07.2 | Raw softmax confidence (M1 scoring) | A | — | Codex | CPU | yes | Phase 09 |
| T07.3 | Temperature scaling on the calibration split (M2) | A | — | Codex | CPU | no | T07.7 |
| T07.4 | MC-dropout predictive entropy (M3) | A | — | Claude | GPU | yes | Phase 09 |
| T07.5 | **Split conformal: nonconformity score + quantile with n+1 correction** (M5) | A | — | Claude | CPU | no | Phase 09 |
| T07.6 | Conformal risk control as the named secondary | A | — | Claude | CPU | yes | Phase 13 |
| T07.7 | ECE, Brier, reliability diagrams | A | — | Codex | CPU | no | Phase 13 |
| T07.8 | **R3–R6: ensemble members, seeds 1–4** (M4) | A | — | Human | GPU | no | Phase 09 |
| T07.9 | Deep-ensemble predictive variance | A | — | Codex | CPU | no | Phase 09 |
| T07.10 | Independent-implementation cross-check of every metric | A | — | Joint | CPU | no | Gate D |
| T07.11 | Freeze prediction artifacts for all mechanisms, internal | A | — | Codex | GPU | no | Phase 08 |

**T07.5 detail.** The conformal quantile uses the finite-sample correction `⌈(n+1)(1−α)⌉/n` on the calibration split — a detail that is easy to omit and that silently breaks the coverage guarantee by O(1/n). It gets its own hand-calculated test fixture. The nonconformity score, the α grid, and the abstention definition all come from the Phase 05 pre-registration and may not be adjusted here.

**T07.10 — the independent-implementation pattern.** Claude writes the contract and hand-calculated fixtures; Codex implements ECE, Brier, and the conformal quantile from the specification text alone; results must agree. This is the phase where that pattern pays for itself, because a wrong ECE binning convention or an off-by-one conformal quantile produces plausible-looking numbers that are simply incorrect.

**Everything is fitted on the calibration split.** Temperature, conformal quantile, and every threshold. Never the internal test set, never external data.

## Human allocation
**A:** owns all mechanisms. **C:** independent verification of calibration metrics from frozen artifacts. **B:** none.

## Claude tasks
T07.1, T07.4, T07.5, T07.6 — the scientific core of the paper's mechanism.

## Codex tasks
T07.2, T07.3, T07.7, T07.9, T07.11 — plus the independent implementations for T07.10.

## Parallelization map
```
T07.1 ─> T07.5 ─> T07.6 ─┐
T07.2, T07.3 ─> T07.7 ───┼─> T07.10 ─> T07.11
T07.4 ───────────────────┤
T07.8 (GPU, ~4 runs) ─> T07.9 ─┘
```
T07.8 occupies the GPU for several days; all CPU work proceeds in parallel.

## Worktrees / branches
```
agent/claude/p07-conformal         agent/claude/p07-mc-dropout
agent/codex/p07-temperature-ece    agent/codex/p07-ensemble-variance
```
`calibration/` is split by task between Claude (conformal) and Codex (temperature/ECE) — **never concurrently on the same file.**

## Files / modules expected
`src/glioma_selective/calibration/{temperature,conformal,crc}.py`, `src/glioma_selective/uncertainty/{mc_dropout,ensemble}.py`, `src/glioma_selective/evaluation/{ece,brier,reliability}.py`, `tests/unit/test_conformal.py`, `tests/unit/test_calibration_metrics.py`, `tests/fixtures/`, `configs/calibration/`.

## Data required
UTSW calibration + internal test. **No external data.**

## Compute required
GPU for T07.8 (4 ensemble members, R3–R6) and MC-dropout inference. Everything else CPU.

## Outputs / artifacts
Temperature parameter (hashed) · conformal quantiles per α (hashed) · ensemble checkpoints R3–R6 · MC-dropout and ensemble uncertainty scores · ECE/Brier/reliability on the internal test set · **frozen prediction artifacts for all mechanisms** · independent-implementation agreement report.

## Tests
Conformal: hand-calculated quantile on a 10-point toy calibration set, worked in the docstring; the n+1 correction is present and correct; empirical coverage on exchangeable held-out data ≥ 1−α−ε over repeated splits; behaviour when the quantile index exceeds n.
Temperature: T=1 leaves probabilities unchanged; optimization reduces NLL on the calibration split; T is a scalar, not per-class.
ECE: hand-calculated on a toy 8-sample example; perfectly calibrated input gives ECE≈0; the binning convention is documented and tested.
Brier: matches the closed-form on toy data.
MC-dropout: dropout is active at inference; N samples give a stable mean; N=1 reduces to deterministic.
Ensemble: variance is zero for identical members; averaging is order-invariant.

## Quality gates
Gate C for the ensemble runs. Gate B for merges. **Independent-implementation agreement is a hard Gate D requirement** — no metric ships on one implementation.

## Scientific validation
1. Conformal empirical coverage on a held-out **exchangeable** internal split must land near nominal. If it does not hold even under exchangeability, the implementation is wrong — and this check must pass *before* the interesting question (coverage under shift) can be asked at all.
2. Temperature scaling must improve ECE on the internal test set, or the calibration split is unrepresentative and that is worth knowing now.
3. Both independent implementations agree on every fixture.

## Acceptance criteria
1. **D-002 resolved**; the primary conformal instrument fixed and recorded.
2. All four mechanisms implemented as independent modules with no shared hidden state.
3. Every parameter fitted on the calibration split only; asserted by test.
4. Conformal quantile includes the n+1 correction; hand-calculated test passing.
5. **Conformal empirical coverage within ±2pp of nominal on exchangeable internal data**, for every α in the grid.
6. Temperature scaling reduces internal-test ECE relative to raw softmax.
7. ECE, Brier, and reliability computed and stored for M1 and M2.
8. Ensemble members R3–R6 trained; the 6-run total (R1–R6) is on budget.
9. Independent implementations agree within tolerance on all fixtures; disagreements investigated and recorded.
10. Prediction artifacts frozen for all mechanisms on the internal test set.

## Failure conditions
Conformal coverage misses nominal on **exchangeable** internal data → implementation bug; stop and fix before Phase 09 · temperature scaling worsens ECE → investigate calibration-split representativeness · independent implementations disagree → neither merges until reconciled · ensemble training exceeds the run budget → reduce N and record it.

## Rollback / recovery
All mechanisms are post-hoc on a frozen checkpoint, so any of them can be recomputed cheaply without retraining. Only T07.8 is expensive, and it resumes from checkpoints.

## Risks
R-C09 (thresholds must come from the pre-registration, not from what looks good) · R-H04 (OOM during ensemble training) · **the silent risk: a subtly wrong conformal quantile that produces plausible numbers** — mitigated by T07.10 and by acceptance criterion 5.

## Decisions requiring Research Lead approval
**D-002** · nonconformity score definition (if the pre-registration left latitude) · MC-dropout sample count N · ensemble size if budget forces a reduction.

## Exit criteria
All acceptance criteria met; Gate D passed; mechanism parameters hashed; artifacts frozen.

## Dependencies for next phase
Phase 08 needs all mechanisms working and the R2 checkpoint.
