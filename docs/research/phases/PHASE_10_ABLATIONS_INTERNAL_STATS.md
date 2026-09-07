# Phase 10 — Ablations and Internal Statistical Validation

**Duration:** ~14 days · **Gate:** D · **Compute:** GPU (2 runs) + CPU

## Scientific purpose
Complete the SPEC §4.9 minimum rigorous ablation set and apply the full statistical protocol to internal results, so that everything internal is final before Gate E is even considered.

## Engineering purpose
The statistics module — bootstrap, DeLong, paired tests, BH correction — isolated from model code and operating only on frozen prediction tables.

## Specification requirements satisfied
SPEC §4.9 (six ablation axes), §5.5 (bootstrap CIs, DeLong, paired bootstrap/permutation, Benjamini–Hochberg), §5.2 (metric hierarchy), §5.3 (honest power reporting).

## RQs / claims addressed
RQ1, RQ3 internally; **RQ4 (exploratory)**; C1, C2, C5, C6 with full statistical support.

## Entry criteria
Phase 09 complete; selective module verified.

## Inputs
Frozen artifacts for all internal conditions; R1–R6 checkpoints; statistical analysis plan; **D-007** resolution.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T10.1 | **R7: whole-brain pooling** (no tumour-aware) — H1 ablation | A | — | Human | GPU | yes | T10.5 |
| T10.2 | **R8: two-stage independent seg+classify** — H2 ablation | A | — | Human | GPU | yes | T10.5 |
| T10.3 | Patient-level bootstrap, ≥1000 iterations | A | — | Codex | CPU | no | T10.6 |
| T10.4 | DeLong test for paired AUROC | A | — | Codex | CPU | yes | T10.6 |
| T10.5 | Paired bootstrap / permutation for AURC and selective-risk deltas | A | — | Claude | CPU | no | T10.6 |
| T10.6 | Benjamini–Hochberg across the §4.9 comparison family | A | — | Claude | CPU | no | Phase 13 |
| T10.7 | **RQ4: 1p/19q frozen-encoder probe** (per **D-007**) | A | — | Claude | GPU | yes | Phase 13 |
| T10.8 | Independent-implementation cross-check: bootstrap, DeLong, BH | A | — | Joint | CPU | no | Gate D |
| T10.9 | Internal statistical results, machine-readable | C | A+Codex (+5d) | Codex | CPU | no | Phase 13 |
| T10.10 | Auxiliary segmentation Dice/HD95 reporting | A | — | Codex | CPU | yes | Phase 13 |

**The six ablation axes** (SPEC §4.9): complete vs. missing modalities (from Phase 08) · internal vs. external (deferred to Phase 12) · calibrated vs. uncalibrated (M1 vs. M2) · always-predict vs. selective (M1/M2 vs. M3/M4/M5) · uncertainty-method choice (M3/M4 vs. M5) · **confirmatory** tumour-aware vs. whole-brain and joint vs. independent (R7, R8 — reported briefly, explicitly *not* a contribution).

**T10.3 — resampling respects the design.** The unit is the patient, always. Paired comparisons resample patients **once** and evaluate both mechanisms on the same resample; treating mechanisms as independent samples would be an inappropriate independence assumption (SPEC §5.5) and would understate the correlation between mechanisms sharing a backbone.

**T10.6 — the BH family is pre-registered.** Which comparisons enter the family was fixed in Phase 05 and may not be adjusted now that effect sizes are visible.

**T10.7 — RQ4 stays exploratory.** With 63 codeleted patients before exclusions, this analysis is underpowered by construction. Report wide CIs, make no inferential claim, and **do not interpret a null result as evidence of absence.**

## Human allocation
**A:** ablation runs, statistical design. **C:** owns statistical-result verification and table verification — C's primary contribution. **B:** none.

## Claude tasks
T10.5, T10.6, T10.7 — statistical design and the exploratory endpoint.

## Codex tasks
T10.3, T10.4, T10.9, T10.10 — plus independent implementations for T10.8.

## Parallelization map
```
T10.1, T10.2, T10.7 (GPU, parallel) ──┐
T10.3 ─> T10.5 ─> T10.6 ──────────────┼─> T10.8 ─> T10.9
T10.4, T10.10 (parallel) ─────────────┘
```
**Runs concurrently with Phase 09.**

## Worktrees / branches
```
agent/codex/p10-bootstrap-delong     agent/claude/p10-paired-tests-bh
agent/claude/p10-1p19q-probe
```

## Files / modules expected
`src/glioma_selective/statistics/{bootstrap,delong,permutation,multiple_comparison}.py`, `tests/unit/test_statistics.py`, `results/internal/statistics/*.json`, `results/ablations/*.json`.

## Data required
Frozen artifacts + UTSW for the two ablation training runs. **No external data.**

## Compute required
GPU for R7, R8, and the 1p/19q probe (~1 GPU-hour). CPU for all statistics. Total training runs after this phase: **8 of the 9-run budget**, leaving R9 as reserve.

## Outputs / artifacts
R7 and R8 checkpoints and predictions · bootstrap CIs for every primary and secondary metric · DeLong results · paired bootstrap/permutation results · BH-corrected p-values · 1p/19q exploratory results · segmentation Dice/HD95 · complete internal statistical results, machine-readable.

## Tests
Bootstrap: reproducible under a fixed seed; ≥1000 iterations enforced; **patient-level resampling asserted** (a patient with multiple rows is resampled as a unit); CI coverage validated against a simulated ground truth.
DeLong: matches a reference implementation on a shared example; identical predictors give p≈1.
Permutation: a null-effect case gives a uniform p-distribution.
BH: hand-calculated on a toy p-value vector; monotonicity of adjusted p-values; family membership matches the pre-registration.

## Quality gates
Gate C for R7/R8. **Gate D is the last internal gate — everything internal is final after this.** Independent-implementation agreement required on bootstrap, DeLong, and BH.

## Scientific validation
1. C independently recomputes every headline statistic from frozen artifacts.
2. Bootstrap CI widths compared against the Phase 05 power-check predictions; a large discrepancy means the power model was wrong and that is worth reporting.
3. Confirmatory ablations (R7, R8) compared against the established literature they are meant to reproduce — **as a sanity check on our implementation**, not as a contribution.

## Acceptance criteria
1. All six ablation axes complete (internal-vs-external deferred to Phase 12 by design).
2. R7 and R8 trained; total training runs ≤ 9.
3. Bootstrap CIs (≥1000 patient-level iterations) for AUROC, AUPRC, AURC, selective risk at fixed coverage, ECE, Brier.
4. DeLong applied to all paired AUROC comparisons on the same test set.
5. Paired bootstrap/permutation applied to all AURC and selective-risk deltas.
6. BH correction applied across the pre-registered family; the family membership matches Phase 05 exactly.
7. RQ4 complete, **explicitly labelled exploratory**, wide CIs reported, no inferential claim made.
8. Segmentation Dice/HD95 reported for the auxiliary task.
9. Independent implementations agree on bootstrap, DeLong, and BH.
10. All internal statistics machine-readable and committed.
11. **All internal analysis is final.** Nothing internal changes after this phase.

## Failure conditions
CI widths far exceed the Phase 05 predictions → report honestly; consider coarsening the reported coverage grid, and record the change · 1p/19q too underpowered even for description → drop RQ4 with a decision-log entry · independent implementations disagree → reconcile before Gate D.

## Rollback / recovery
Statistics recompute cheaply from frozen artifacts. R7/R8 resume from checkpoints.

## Risks
R-S01 (wide CIs — expected and reportable) · R-H03 (1p/19q underpowering — known since Phase 03) · R-C08 (the ablations are the last place architecture curiosity could creep in; R7 and R8 are the *only* two permitted).

## Decisions requiring Research Lead approval
Whether to drop RQ4 if the probe is uninterpretable · whether any additional ablation is justified (**presumptively no**) · bootstrap iteration count above 1000 if CIs are unstable.

## Exit criteria
All acceptance criteria met; Gate D passed; **all internal results final and frozen**; the project is ready to consider Gate E.

## Dependencies for next phase
Phase 11 requires all internal analysis complete — Gate E cannot be evaluated while internal work is outstanding.
