# Phase 05 — Cohort Finalization, Frozen Splits, and Experiment Pre-Registration

**Duration:** ~4 days · **Gate:** D + **FREEZE** · **Compute:** CPU

> The scientific-integrity keystone. After this phase, the analysis plan is fixed and can no longer be adjusted to suit results. **D-003, D-004, and D-007 must all resolve here** — each is a place where an unfrozen choice would let external results retroactively shape the claim.

## Scientific purpose
Fix, in advance and in writing, exactly what will be measured, how abstention is defined, what tolerance C4 is judged against, and which comparisons are corrected for multiplicity. Pre-registration is the mechanism that makes C1–C6 falsifiable rather than decorative.

## Engineering purpose
Compute and freeze the patient-level stratified UTSW split; hash every input manifest; emit a pre-registration document whose hash predates all modelling.

## Specification requirements satisfied
SPEC §4.5 (splits and thresholds calibrated entirely on UTSW), §5.1 (patient-level, after de-duplication, frozen before training), §5.3 (honest power discussion), §5.4 (stratified splits, class imbalance), §5.5 (statistical plan), §9 step 3 (freeze cohorts).

## RQs / claims addressed
All. This phase makes C1–C6 testable by fixing their decision criteria.

## Entry criteria
Phase 03 complete; Phase 04 complete except T04.6 (D-023: normalization statistics are fitted after this phase freezes the split); cohort manifest and exclusion manifest (including QC exclusions) frozen and hashed; post-QC class counts available.

## Inputs
Post-QC cohort manifest (`docs/research/manifests/cohort_manifest_post_qc.json`, D-030) and post-QC exclusion manifest (SSD `exclusion_manifest_post_qc.json`); post-QC counts (`protocols/POST_EXCLUSION_CLASS_COUNTS.md`); `DECISION_LOG.md` D-003, D-004, D-007.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T05.1 | **Power check** — internal test size vs. risk–coverage resolution | A | — | Claude | CPU | no | T05.2 |
| T05.2 | Patient-level stratified split: train / calibration / internal test | A | — | Codex | CPU | no | T05.3 |
| T05.3 | **Freeze the split; SHA-256; commit** | A | — | Human | none | no | Phase 06 |
| T05.4 | **Resolve D-003** — abstention operationalization | A | — | Claude | none | no | Phase 07 |
| T05.5 | **Resolve D-004** — freeze the C4 tolerance band with a power justification | A | — | Claude | CPU | no | Phase 11 |
| T05.6 | **Resolve D-007** — 1p/19q approach and budget | A | — | Claude | none | no | Phase 10 |
| T05.7 | Write the pre-registration document | A | — | Claude | none | no | Phase 11 |
| T05.8 | Statistical analysis plan: tests, BH family, bootstrap iterations | C | A+Codex (+3d) | Claude | none | yes | Phase 13 |
| T05.9 | Enumerate the 18 evaluation conditions and 6 mechanisms as configs | A | — | Codex | none | yes | Phase 09 |
| T05.10 | Hash and commit the pre-registration | A | — | Human | none | no | Gate E |

**T05.1 — the power check** determines whether the design survives contact with the actual counts. Inputs: post-exclusion IDH counts; intended split proportions; the coverage grid granularity. Outputs: expected internal-test n; expected bootstrap CI half-width for AUROC and for selective risk at φ ∈ {0.9,…,0.5}; the finest coverage grid that remains statistically meaningful. SPEC §5.3 predicts *"visibly wide confidence bands at the extremes of coverage"* — the point is to know how wide **before** committing, not to discover it in Phase 09.

**T05.4 — D-003, abstention definition.** Two operationalizations are in the specification and they are not interchangeable. Recommended resolution: the nonconformity-score threshold generates risk–coverage and AURC (RQ1, C1–C3, C5, C6); the set-valued conformal predictor at nominal 1−α generates the empirical-vs-nominal coverage comparison (RQ2, C4) over a pre-registered α grid. **Both definitions and their mapping must be written down here**, because after Phase 12 the choice could be made to favour whichever looks better.

**T05.5 — D-004, the C4 tolerance band.** Recommended: **±5 percentage points**, with the recorded justification that at external n≈450–500 the bootstrap CI half-width on coverage near 0.90 is roughly ±2.7 pp, so ±5 pp is resolvable. Also pre-register C4's *own* refutation clause: if the CI half-width on coverage deviation exceeds the band, C4 is refuted — and that is a reportable finding.

## Human allocation
**A:** owns every freeze and every decision. **C:** statistical analysis plan (with A). **B:** independent verification that the split respects the exclusion manifest. **D–F:** none.

## Claude tasks
T05.1, T05.4, T05.5, T05.6, T05.7, T05.8 — all scientific judgement, all cross-cutting, all consequential.

## Codex tasks
T05.2 (split implementation — **Claude-reviewed**, per the leakage/splits joint-review rule), T05.9 (config enumeration).

## Parallelization map
```
T05.1 ─> T05.2 ─> T05.3 ──────────────┐
T05.4, T05.5, T05.6 (Claude) ─> T05.7 ─┼─> T05.10 ─> FREEZE
T05.8, T05.9 in parallel ──────────────┘
```

## Worktrees / branches
```
agent/codex/p05-splits        agent/claude/p05-preregistration
```
`agent/claude/p05-preregistration` also carries the D-003/D-004/D-007 resolutions into `DECISION_LOG.md`.

## Files / modules expected
`src/glioma_selective/splits/{stratified,freeze}.py`, `tests/unit/test_splits.py`, `data/manifests/splits.json` + `.sha256`, `docs/research/protocols/PREREGISTRATION.md` + `.sha256`, `docs/research/protocols/STATISTICAL_ANALYSIS_PLAN.md`, `configs/experiments/`.

## Data required
Manifests only. No image data is read.

## Compute required
CPU, minutes.

## Outputs / artifacts
Power-check report · **frozen split manifest, hashed** · **pre-registration document, hashed** · statistical analysis plan · 18-condition × 6-mechanism config enumeration · D-003, D-004, D-007 resolved in the decision log.

## Tests
`test_splits.py`: patient-level only (no ID in two splits); stratification holds within tolerance on the primary endpoint; determinism (same seed → same split); every ID exists in the cohort manifest; no excluded ID appears; split proportions match the config; **re-running produces a byte-identical manifest.**

## Quality gates
Gate D **plus a freeze event**. After this phase, changing the split, the abstention definition, the tolerance band, or the statistical plan requires a decision-log entry and invalidates downstream results.

## Scientific validation
1. B independently verifies the split honours the exclusion manifest and is patient-level.
2. C independently reviews the statistical analysis plan against SPEC §5.5.
3. The pre-registration is hashed and committed **before any model is trained**, so its timestamp provably predates every result.

## Acceptance criteria
1. Power check complete; expected CI widths recorded for the primary metrics at every reported coverage level.
2. Split computed, patient-level, stratified on IDH; all split tests passing.
3. Split manifest hashed and committed; hash recorded in `PREREGISTRATION.md`.
4. **D-003 resolved** — abstention defined for both the risk–coverage sweep and the coverage comparison, with the mapping stated.
5. **D-004 resolved** — tolerance band frozen to a number, with a power justification and C4's own refutation clause pre-registered.
6. **D-007 resolved** — 1p/19q approach fixed (recommended: frozen-encoder probe) and labelled exploratory.
7. Pre-registration document complete: endpoints, conditions, mechanisms, metrics, statistical tests, BH family, bootstrap iterations, refutation criteria for C1–C6 verbatim, α grid, coverage grid.
8. Statistical analysis plan committed, naming exactly which comparisons enter the BH family.
9. All 18 conditions × 6 mechanisms enumerated as configs.
10. Pre-registration hashed and committed; the commit predates any training commit.

## Failure conditions
Power check shows the internal test set cannot resolve selective risk at the intended coverage grid → coarsen the grid or re-proportion the split, **before freezing**, and record it · 1p/19q positives too few to support even exploratory analysis → drop RQ4 with a decision-log entry rather than reporting an uninterpretable result · stratification unachievable given the class balance.

## Rollback / recovery
**This is the last cheap moment.** Everything before is recomputable; everything after depends on the freeze. If an error is found post-freeze, the split is re-issued as v2 with a decision-log entry and **all downstream results are invalidated and re-run.**

## Risks
**R-C06 (wrong or unfrozen split)** · **R-C09 (post-hoc threshold manipulation — this phase is the defence against it)** · R-H03 (insufficient class counts, decided here).

## Decisions requiring Research Lead approval
Split proportions (recommendation: 60/20/20 train/calibration/internal-test, subject to the power check) · the coverage grid · the α grid for conformal · **D-003, D-004, D-007** · which comparisons form the BH family.

## Exit criteria
All acceptance criteria met; Gate D passed; **split and pre-registration hashed and committed**; the three blocking decisions resolved.

## Dependencies for next phase
Phase 06 needs the frozen split and the normalization statistics (Phase 04 T04.6, run after this phase's T05.3 per D-023). Phase 11's Gate E cannot pass without the hashed pre-registration.
