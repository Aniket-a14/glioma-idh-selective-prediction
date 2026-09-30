# Pre-registration: calibrated selective prediction for IDH classification

**FROZEN 2026-09-30** (Phase 05, T05.7 and T05.10). Its own SHA-256 is in `PREREGISTRATION.md.sha256` (a document cannot contain
its own hash). It predates every model training run and every look at external labels.

Companion documents: `STATISTICAL_ANALYSIS_PLAN.md` (procedures), `POWER_CHECK.md` (what the sample sizes can resolve),
`DECISION_LOG.md` (D-003, D-004, D-007, D-033, D-034, D-035 resolved for this document).

## 1. What this fixes

What is measured, how abstention is defined, the tolerance C4 is judged against, which comparisons are corrected for
multiplicity, and what result would count against each claim. After the freeze none of these move to suit a result. A
change needs a decision-log entry and invalidates every downstream result (they are re-run, not patched).

## 2. Endpoints

IDH mutation status is the primary endpoint. 1p/19q codeletion is exploratory only (section 11). MGMT is not an endpoint.

## 3. Cohorts and split

- Development: UTSW-Glioma, 616 patients after Phase 04 QC. Split 60/20/20 into train, calibration and internal test,
  patient-level, stratified on IDH, seeded (D-034). The split manifest hash is recorded in the freeze record.
- External: UCSF-PDGM (202 patients after de-duplication against BraTS-2021) and EGD (pending its data-use agreement,
  D-018). Both are evaluated whole, never split, never used for development.
- All thresholds, temperatures, conformal quantiles and normalization statistics come from UTSW training or calibration
  data only.

## 4. Conditions and mechanisms

Six modality conditions (`full`, `drop_t1`, `drop_t1ce`, `drop_t2`, `drop_flair`, `t1ce_flair_only`; dropped channels zeroed,
never imputed) by three cohorts (UTSW internal test, UCSF-PDGM, EGD) = 18 conditions. Six mechanisms: M1 always-predict
uncalibrated, M2 always-predict temperature-scaled, M3 selective MC-dropout entropy, M4 selective deep ensemble (N about 5),
M5 selective conformal (primary), M6 always-predict tumor-aware joint comparator (its definition rests on D-006).
18 x 6 = 108 result cells (72 without EGD). Enumerated in `configs/evaluation/conditions.yaml`.

## 5. Abstention (D-003)

Two views of one calibrated score, each used for the question it fits. The nonconformity-score threshold produces the
risk-coverage curve and AURC (RQ1, C1-C3, C5, C6). The set-valued conformal predictor at nominal 1-alpha produces the
empirical-versus-nominal coverage comparison (RQ2, C4). The set-valued predictor abstains when the set is not a singleton;
an empty set counts as abstention and its rate is reported separately.

## 6. Metrics and conventions (D-033)

Primary: selective risk at matched coverage, AURC, risk-coverage curve shape, empirical versus nominal conformal coverage.
Secondary: AUROC, AUPRC, sensitivity, specificity, F1, balanced accuracy, Brier, ECE, reliability diagrams. AUROC is never
reported without ECE, Brier, AURC and coverage. ECE: positive-class, equal-width, 10 bins, left-closed with 1.0 in the last
bin; 5 bins, 15 bins and equal-mass 10 bins as sensitivity; top-label ECE as secondary. Risk-coverage: block ties. AURC: mean
selective risk over all cutoffs. Selective risk at a target coverage: the smallest attainable coverage at or above the
target, reported with the attained coverage.

## 7. Grids

Coverage grid {0.9, 0.8, 0.7, 0.6, 0.5}. Conformal alpha grid {0.05, 0.10, 0.20}.

## 8. C4 tolerance band (D-004)

+/-7 percentage points, derived from the measured noise floor (`POWER_CHECK.md`): calibration-draw noise plus test-set
noise gives a 95% half-width of 6.6 pp at n = 202 and 5.9 pp at n = 450 with no shift at all. +/-5 pp is reported as a
secondary band. The interval on the coverage deviation resamples calibration and test together. If its half-width exceeds the
band, C4 is refuted (the deviation cannot be reliably characterized), and that is a reportable finding.

## 9. Claims and what would prove each wrong (verbatim from SPEC §1.4)

| # | Claim | Result that would prove it WRONG |
|---|---|---|
| C1 | Selective prediction (conformal) achieves lower selective risk at matched coverage than an always-predict baseline, internally. | Selective risk at any fixed coverage ≥ always-predict risk; risk–coverage curve is flat or increasing as coverage decreases. |
| C2 | Selective prediction preserves this advantage under missing modalities. | Selective-risk advantage over always-predict disappears or reverses when 1–2 sequences are dropped. |
| C3 | Selective prediction preserves this advantage under external (cross-institutional) shift. | No selective-risk advantage on UCSF-PDGM/EGD relative to always-predict, at matched coverage. |
| C4 | The magnitude and direction of any deviation between empirical and nominal coverage under domain shift and missingness can be measured and characterized (e.g., against a pre-registered tolerance band such as ±5 percentage points), without presupposing whether coverage holds or degrades. | The deviation cannot be reliably characterized — e.g., empirical coverage estimates are too noisy/unstable (given sample size) to distinguish "coverage preserved" from "coverage degraded" at the pre-registered tolerance. |
| C5 | Risk–coverage curves remain monotonic (rejecting less-confident cases never increases risk) across all four evaluation conditions. | Curves become non-monotonic under shift/missingness, mirroring documented failures in retinal/CXR imaging. |
| C6 | Abstention rate correlates with actual error rate (uncertain cases are disproportionately the wrong ones). | Abstained cases are no more likely to be erroneous than randomly selected cases of equal size. |

**How each is judged (D-035).** Three outcomes, fixed now: *supported* when the upper 95% limit of the selective-risk
difference from always-predict is below 0 at every grid coverage; *refuted* when the point estimate breaks the inequality
in the "would prove it wrong" column at any grid coverage; otherwise *inconclusive at this n*, reported as its own result.
C5 and C6 use the same three-way shape with the tests in `STATISTICAL_ANALYSIS_PLAN.md` section 5, and C4 is judged by section 8
above. The claim-level status is the worst per-condition status, with every per-condition status shown.

## 10. Tests, multiplicity, resampling

Patient-level bootstrap, 2000 iterations, percentile 95% intervals; paired resampling for comparisons on the same patients;
two-stage calibration-and-test resampling for coverage deviation; DeLong for paired AUROC; permutation tests, 10,000
permutations, for C6. One Benjamini-Hochberg family at q = 0.05 over 44 confirmatory comparisons (29 without EGD), listed by
block in `STATISTICAL_ANALYSIS_PLAN.md` section 6.

## 11. 1p/19q (D-007)

A frozen-encoder probe fitted after the IDH model is trained; exploratory, reported with wide intervals and no inferential
claim. About 12 co-deleted patients sit in the internal test set, so a null result is expected and is not evidence of absence.

## 12. Amendments

Anything in sections 2-11 changed after the freeze is logged in `DECISION_LOG.md` with the reason, the date and what is
invalidated. Deviations are listed in the paper's methods section.

## 13. Freeze record (T05.3 and T05.10)

| Item | Value |
|---|---|
| Split manifest SHA-256 (`data/manifests/splits.json`, T05.3, 2026-09-30) | `b8696d4474ce0328eb3ffd53bfb3727f85b1977ed22d0a78212111e800ec9a87` (copy in `docs/research/manifests/splits.sha256`) |
| Post-QC UTSW roster SHA-256 | `ee550584d4276d701204b864dd8b7817f65b24f9ba1f63110e5343b32023561d` |
| Conditions config SHA-256 (`configs/evaluation/conditions.yaml`) | `e74e253e31f9827c14cdf2db488afd59a6e3b1fec83d08991f8884a4d2d18283` |
| Statistical analysis plan SHA-256 (`STATISTICAL_ANALYSIS_PLAN.md`) | `27294ac1527f86c8ba5038edacf8cb8f2a81ef74c4ef3a3936cc3c6b2628f94f` |
| Git commit of this document | the commit that adds `PREREGISTRATION.md.sha256`; its id is recorded in `PROJECT_STATE.md` |
| Date and Research Lead authorization | 2026-09-30; the Research Lead instructed the freeze and approved the freeze command in session |
