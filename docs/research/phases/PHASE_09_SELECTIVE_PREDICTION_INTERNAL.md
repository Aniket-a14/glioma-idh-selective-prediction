# Phase 09 — Selective-Prediction Internal Experiments

**Duration:** ~7 days · **Gate:** C · **Compute:** CPU (from frozen artifacts)

## Scientific purpose
Produce the paper's primary reporting device — risk–coverage curves, AURC, selective risk at matched coverage, empirical-vs-nominal coverage, and abstention–error association — on internal data, where C1, C2, C5, and C6 can be adjudicated before external data is ever unlocked.

## Engineering purpose
The selective-prediction analysis module, computed entirely from frozen prediction artifacts, so that no analysis re-runs a model and no result can be accidentally re-tuned.

## Specification requirements satisfied
SPEC §1.2 (coverage, selective risk, risk–coverage, AURC definitions), §4.7 (computed for every condition and every mechanism; the primary reporting device), §5.2 (primary metric hierarchy), §5.4 (rejected-but-correct rate — the concrete cost of abstention).

## RQs / claims addressed
**RQ1 and RQ2 internally; C1, C2, C5, C6 adjudicated internally. C4 internally** (its external half comes in Phase 12).

## Entry criteria
Phase 08 complete; frozen prediction artifacts for all 6 internal conditions × 6 mechanisms.

## Inputs
Frozen prediction artifacts; pre-registered α grid, coverage grid, abstention definition, and C4 tolerance band.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T09.1 | Abstention decision logic `g(x)` for all mechanisms | A | — | Claude | CPU | no | T09.2 |
| T09.2 | Risk–coverage curve computation | A | — | Claude | CPU | no | T09.3 |
| T09.3 | AURC | A | — | Codex | CPU | no | T09.6 |
| T09.4 | Selective risk at matched coverage | A | — | Codex | CPU | yes | T09.6 |
| T09.5 | Empirical vs. nominal coverage; deviation | A | — | Claude | CPU | yes | T09.6 |
| T09.6 | **Monotonicity violation quantification** | A | — | Claude | CPU | no | Phase 13 |
| T09.7 | Abstention/error enrichment; **rejected-but-correct rate** | A | — | Codex | CPU | yes | Phase 13 |
| T09.8 | Independent-implementation cross-check of AURC and risk–coverage | A | — | Joint | CPU | no | Gate D |
| T09.9 | Internal results tables (machine-readable JSON first) | A | — | Codex | CPU | no | Phase 13 |
| T09.10 | Calibration-split vs. test-split coverage discrepancy report | A | — | Claude | CPU | yes | Phase 13 |

**T09.6 — monotonicity is measured, not eyeballed.** C5 is refuted by non-monotonic curves, so "non-monotonic" needs a number: count violations and sum their magnitude `Σ max(0, R(φᵢ) − R(φⱼ))` for `φᵢ < φⱼ`, with a bootstrap CI on the total. A small violation attributable to finite-sample noise is different from a systematic reversal, and only the quantified version distinguishes them.

**T09.7 — the cost of abstention.** SPEC §5.4 requires explicitly reporting the rate at which rejected cases *would have been correctly classified*. This is the number a clinician actually cares about, and it is easy to omit because it makes selective prediction look worse.

**T09.10 — overfit check on the calibration split.** SPEC §4.11 lists "overfitting the calibration/abstention threshold to the internal calibration split in a way that does not generalize" as a project-killer, and requires the calibration-vs-test coverage discrepancy be reported explicitly. Do it here, internally, where it can still inform interpretation.

**Metric code must not import plotting code.** `evaluation/` and `selective/` are testable headlessly; `visualization/` imports them, never the reverse. Enforced by the Phase 00 CI check.

## Human allocation
**A:** owns the analysis. **C:** independent verification of every headline number from the frozen artifacts — this is C's highest-value contribution. **B:** none.

## Claude tasks
T09.1, T09.2, T09.5, T09.6, T09.10 — the scientific core.

## Codex tasks
T09.3, T09.4, T09.7, T09.9 — plus independent implementations for T09.8.

## Parallelization map
```
T09.1 ─> T09.2 ─┬─> T09.3 ─┐
                ├─> T09.4 ─┼─> T09.6 ─> T09.8 ─> T09.9
                ├─> T09.5 ─┤
                └─> T09.7 ─┘
T09.10 in parallel
```
**This phase runs concurrently with Phase 10** — CPU-only analysis alongside GPU ablation training.

## Worktrees / branches
```
agent/claude/p09-selective-core      agent/codex/p09-aurc-metrics
```

## Files / modules expected
`src/glioma_selective/selective/{abstention,risk_coverage,aurc,coverage}.py`, `src/glioma_selective/evaluation/selective_metrics.py`, `tests/unit/test_risk_coverage.py`, `tests/unit/test_aurc.py`, `results/internal/*.json`.

## Data required
Frozen prediction artifacts only. **No image data, no GPU, no external data.**

## Compute required
CPU, minutes. This is the payoff of the frozen-artifact architecture: the entire internal analysis is cheap and re-runnable, and Person C can verify it without a GPU.

## Outputs / artifacts
Risk–coverage curves for all 36 internal cells · AURC with bootstrap CIs · selective risk at φ ∈ {0.9,0.8,0.7,0.6,0.5} · empirical-vs-nominal coverage per α · monotonicity violation report · abstention/error enrichment and rejected-but-correct rate · calibration-vs-test coverage discrepancy · **machine-readable results JSON** · internal adjudication of C1, C2, C5, C6.

## Tests
`test_risk_coverage.py`: hand-calculated 6-patient example worked in the docstring; coverage 1.0 gives full-set risk; coverage 0 is handled (undefined risk, not a crash); ties in the confidence score are broken deterministically; coverage is monotone non-increasing in τ.
`test_aurc.py`: hand-calculated toy AURC; AURC ∈ [0,1]; a perfect ranker gives lower AURC than a random one; permuting patient order changes nothing.
Coverage: empirical coverage on exchangeable data ≈ nominal; the deviation calculation matches a hand example.
Abstention: enrichment is 1.0 when abstention is random; > 1.0 when errors are preferentially rejected.

## Quality gates
Gate C for the analysis run. **Gate D requires independent-implementation agreement on AURC and risk–coverage.**

## Scientific validation
1. Independent implementations agree on all fixtures.
2. C independently recomputes every headline number from the frozen artifacts.
3. Sanity check: a random-confidence baseline should produce a **flat** risk–coverage curve. If it does not, the sweep has a bug. This is the single most informative negative control in the phase.

## Acceptance criteria
1. Risk–coverage curves computed for all 6 conditions × 6 mechanisms internally.
2. AURC with patient-level bootstrap CI (≥1000 iterations) for every cell.
3. Selective risk at every pre-registered matched-coverage level.
4. Empirical-vs-nominal coverage for every α in the pre-registered grid.
5. Monotonicity violations counted and magnitude-quantified with a bootstrap CI.
6. **Rejected-but-correct rate reported** for every mechanism and condition.
7. Abstention/error enrichment computed with a permutation test.
8. Calibration-vs-test coverage discrepancy reported.
9. Independent implementations agree.
10. All results written as machine-readable JSON **before** any table or figure is produced.
11. **C1, C2, C5, C6 adjudicated internally** against their verbatim pre-registered refutation criteria — support or refute stated explicitly, with no hedging.
12. Any refutation recorded in `paper/NEGATIVE_RESULTS.md` **the day it is found.**

## Failure conditions
Random-confidence baseline does not give a flat curve → sweep bug, stop · AURC outside [0,1] → implementation error · **a claim being refuted is NOT a failure condition** — it is a result, recorded and reported.

## Rollback / recovery
Analysis is cheap and fully recomputable from frozen artifacts. No model re-runs.

## Risks
R-S01 (wide CIs at coverage extremes — expected, report honestly) · **R-S02 (non-monotonic curves — refutes C5; a headline finding, not a bug)** · R-C09 (thresholds come from the pre-registration only).

## Decisions requiring Research Lead approval
Coverage-grid granularity if the power check suggests coarsening · tie-breaking rule for equal confidence scores · **any decision that would alter a pre-registered criterion — which requires a decision-log entry and is presumptively refused.**

## Exit criteria
All acceptance criteria met; Gate D passed; internal claims adjudicated; results JSON committed.

## Dependencies for next phase
Phase 10 needs the selective module. Phase 11's Gate E needs internal results final.
