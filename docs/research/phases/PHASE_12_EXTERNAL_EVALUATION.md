# Phase 12 — Frozen Cross-Institutional External Evaluation

**Duration:** ~4 days · **Gate:** E (continued) · **Compute:** GPU (inference only)

> **Run once.** Nothing about the method changes based on what comes back.

## Scientific purpose
Measure, out of sample, whether the selective-prediction advantage survives cross-institutional domain shift, and how far empirical coverage drifts from nominal when exchangeability is violated. **The answer is not presupposed in either direction** — that neutrality is the point of RQ2.

## Engineering purpose
Execute the frozen pipeline on UCSF-PDGM and EGD; freeze the predictions; compute the pre-registered metrics.

## Specification requirements satisfied
SPEC §4.5 (used only once, at the end), §4.7 (risk–coverage for external conditions), §5.5 (statistical protocol), §9 step 8 (run the frozen pipeline once; measure empirical vs. nominal coverage without presupposing the outcome).

## RQs / claims addressed
**RQ1 (external half), RQ2, RQ3, RQ4 (external); C3, C4, C5 externally, C6 externally.**

## Entry criteria
Gate E passed; freeze manifest signed and hashed; `GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1`.

## Inputs
Frozen checkpoints; frozen mechanism parameters; frozen normalization statistics; preprocessed external cohorts; the pre-registered metric and statistical plan.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T12.1 | Inference on UCSF-PDGM: 6 conditions × 6 mechanisms | A | — | Human | GPU | no | T12.3 |
| T12.2 | Inference on EGD: 6 × 6 (if available) | A | — | Human | GPU | no | T12.3 |
| T12.3 | **Freeze external prediction artifacts, immutably** | A | — | Codex | GPU | no | T12.4 |
| T12.4 | Compute pre-registered primary metrics | A | — | Codex | CPU | no | T12.5 |
| T12.5 | Empirical vs. nominal coverage; deviation vs. the frozen band | A | — | Claude | CPU | no | Phase 13 |
| T12.6 | External calibration: ECE, Brier, reliability (RQ3) | A | — | Codex | CPU | yes | Phase 13 |
| T12.7 | Bootstrap CIs and paired tests, external | A | — | Codex | CPU | no | Phase 13 |
| T12.8 | Monotonicity quantification, external (C5) | A | — | Claude | CPU | no | Phase 13 |
| T12.9 | **Adjudicate C3, C4, C5, C6 externally against verbatim criteria** | A | — | Claude | CPU | no | Phase 13 |
| T12.10 | Record refutations in `NEGATIVE_RESULTS.md` immediately | A | — | Human | none | no | Phase 14 |

**The conformal quantile carries over from the internal calibration split.** It is **not** refitted on external data — refitting would fit the external distribution and destroy exactly the exchangeability-violation measurement RQ2 exists to make.

**Expected outcomes, none of which changes anything.** The literature suggests external AUROC may drop substantially (Elyassirad et al. saw 0.90 → 0.734), calibration may collapse (GliomaVista-IDH external Brier 0.32), curves may become non-monotonic (Zadorozhny et al.), and coverage may fall well short of nominal. **All of these are results.** None is a bug. None justifies a method change.

## Human allocation
**A:** owns the run — this is the single most consequential execution in the project. **C:** independent verification of external numbers from frozen artifacts. **B:** none.

## Claude tasks
T12.5, T12.8, T12.9 — coverage analysis, monotonicity, claim adjudication.

## Codex tasks
T12.3, T12.4, T12.6, T12.7 — mechanical computation using already-verified code paths.

## Parallelization map
```
T12.1, T12.2 (GPU, parallel) ─> T12.3 ─> T12.4 ─┬─> T12.5 ─> T12.9 ─> T12.10
                                                 ├─> T12.6
                                                 ├─> T12.7
                                                 └─> T12.8
```

## Worktrees / branches
```
agent/codex/p12-external-inference
```
Minimal new code — this phase runs already-tested code paths. **New code written here is a red flag**: it suggests something was not actually frozen.

## Files / modules expected
`scripts/run_external_evaluation.py`, `artifacts/experiments/external_frozen/`, `results/external/*.json`. **No new scientific modules.**

## Data required
UCSF-PDGM (BraTS-dedup'd) and EGD, preprocessed through the frozen pipeline. Labels accessed for the first time.

## Compute required
GPU inference only. 6 conditions × 6 mechanisms × 2 cohorts, plus MC-dropout sampling and 5-member ensemble passes.

## Outputs / artifacts
**Immutable external prediction artifacts** · external primary metrics with bootstrap CIs · empirical-vs-nominal coverage per condition and α · external calibration metrics · monotonicity report · external claim adjudication · any refutations recorded.

## Tests
No new scientific tests — the code paths were tested in Phases 07–10. Operational assertions only: the firewall permits access; the checkpoint hash matches the freeze manifest; the normalization statistics hash matches; **the config hash matches the freeze manifest** (proving the frozen method was actually the one run).

## Quality gates
Gate E remains in force. Every artifact records the freeze manifest hash so its provenance is verifiable after the fact.

## Scientific validation
1. Verify the checkpoint, config, and normalization hashes match the freeze manifest **before** interpreting any number.
2. C independently recomputes external headline numbers from frozen artifacts.
3. Claim adjudication uses the **verbatim** pre-registered refutation criteria from `SPEC_TRACEABILITY_MATRIX.md` Part 2 — not a paraphrase, not a softened restatement.

## Acceptance criteria
1. Inference complete on UCSF-PDGM (and EGD if available) for all 6 conditions × 6 mechanisms.
2. All hashes verified against the freeze manifest before analysis.
3. External prediction artifacts frozen immutably with run ID, git SHA, checkpoint hash, and freeze-manifest hash.
4. Pre-registered primary metrics computed: selective risk at matched coverage, AURC, monotonicity, coverage deviation.
5. Empirical-vs-nominal coverage computed for every α and condition, with bootstrap CIs.
6. External ECE, Brier, and reliability computed (RQ3).
7. Bootstrap CIs and paired tests complete per the statistical plan.
8. **C3, C4, C5, C6 adjudicated externally against verbatim criteria** — support or refute stated plainly.
9. Every refutation recorded in `NEGATIVE_RESULTS.md` **the day it is found.**
10. **No method change made in response to any result.** Verified by comparing the post-run git SHA to the freeze manifest SHA — they must match.

## Failure conditions
**These are NOT failure conditions:** poor external discrimination (refutes C3) · coverage far from nominal (answers RQ2) · non-monotonic curves (refutes C5) · calibration collapse (answers RQ3) · high abstention. **All are results.**
**Actual failure conditions:** hash mismatch (the frozen method was not what ran — stop, investigate) · firewall bypassed · **any method change made in response to results** · external cohort preprocessing differs from internal.

## Rollback / recovery
**None.** Results are seen and cannot be unseen. A genuine bug is corrected under the post-external categories in `EXTERNAL_VALIDATION_PROTOCOL.md` §4, with both the original and corrected results reported and the bug described.

## Risks
**R-S03, R-S04, R-S05, R-S06** — all expected-possible scientific outcomes, all reportable · R-C03 (must not retroactively tune) · R-H01 (EGD absent → single-cohort result, disclosed).

## Decisions requiring Research Lead approval
Whether an apparent anomaly constitutes a genuine bug (**high bar** — "the result is disappointing" is not evidence of a bug) · whether a re-run is warranted, requiring a decision-log entry and retention of the original result.

## Exit criteria
All acceptance criteria met; external artifacts frozen; claims adjudicated; git SHA unchanged from the freeze manifest.

## Dependencies for next phase
Phase 13 needs frozen external artifacts and adjudicated claims.
