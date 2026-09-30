# Statistical analysis plan (Phase 05 T05.8)

**DRAFT, not frozen.** Written 2026-09-30. Frozen with `PREREGISTRATION.md` at T05.10 by the Research Lead. Reviewed
against SPEC §5.5 by contributor role C before the freeze. After the freeze, any change needs a `DECISION_LOG.md` entry and
invalidates downstream results (Phase 05 file, Rollback section).

Sources: SPEC §4.6, §4.7, §5.2, §5.4, §5.5; decisions D-003, D-004, D-007, D-033, D-034, D-035; `POWER_CHECK.md`.
Numbers marked *proposed* below are this plan's choices where the SPEC gives none, for the Research Lead to confirm at the
freeze.

## 1. Data and units

- Development cohort: UTSW-Glioma, 616 patients after Phase 04 QC, split 60/20/20 (D-034) into train, calibration and
  internal test, patient-level, stratified on IDH. The unit of resampling is always the patient.
- External cohorts: UCSF-PDGM (202 patients after de-duplication against BraTS-2021), evaluated whole, never split.
  EGD, evaluated whole, once its data-use agreement is signed (D-018); until then every EGD cell is absent, and the
  absence is stated in the report, not filled.
- No UCSF-PDGM or EGD label is read before Gate E. All thresholds, temperatures and conformal quantiles are fitted on the
  UTSW calibration split only.

## 2. Conditions and mechanisms

Six modality conditions (`full`, `drop_t1`, `drop_t1ce`, `drop_t2`, `drop_flair`, `t1ce_flair_only`; dropped channels are
zeroed, never imputed) by three cohorts by six mechanisms (M1-M6), enumerated in `configs/evaluation/conditions.yaml`:
18 conditions, 108 cells (12 conditions, 72 cells without EGD). All cells are computed from frozen prediction artifacts.

## 3. Definitions

- **Coverage grid** {0.9, 0.8, 0.7, 0.6, 0.5}. **Conformal alpha grid** {0.05, 0.10, 0.20}.
- **Risk** is the 0-1 error rate of `p > 0.5` on accepted patients. **Always-predict risk** is the 0-1 error rate on all
  patients (coverage 1) of the same model.
- **Risk-coverage curve, AURC, ECE, selective risk at a target coverage:** as adopted in D-033. Positive-class ECE, equal-width,
  10 bins, left-closed with 1.0 in the last bin, primary; 5 bins, 15 bins, equal-mass 10 bins as sensitivity; top-label ECE
  secondary. Tied scores enter and leave together (block ties). AURC is the mean selective risk over all cutoffs. At a
  target coverage between attainable points, take the smallest attainable coverage at or above the target and report the
  attained value.
- **Abstention** (D-003): for the risk-coverage curve, a threshold on the nonconformity score (baselines: softmax
  confidence, MC-dropout entropy, ensemble variance). For the coverage comparison, the conformal set at nominal 1-alpha,
  abstaining when the set is not a singleton; an empty set counts as abstention and its rate is reported separately.
- **Nonconformity score and conformal quantile:** the score definition is written in the Phase 07 contract; the quantile is
  the `ceil((n + 1)(1 - alpha))`-th smallest calibration score, computed in exact arithmetic (a float `ceil` is wrong
  for some inputs: n = 9, alpha = 0.7 gives 4 instead of 3).

## 4. Resampling

- Patient-level bootstrap, **2000 iterations** (proposed; SPEC minimum 1000), percentile 95% intervals, for AUROC,
  AUPRC, AURC, selective risk at each grid coverage, ECE and Brier. The percentile bootstrap runs 8-17% narrower than
  the Hanley-McNeil formula at n = 123 (`POWER_CHECK.md`); AUROC intervals are reported from both, and the wider one is
  quoted when they differ.
- **Paired** comparisons on the same patients reuse the same resample indices for every mechanism and every modality
  condition of that cohort, so differences are paired by construction. Unpaired comparisons (UTSW vs an external cohort) use
  independent resamples.
- **Coverage deviation (C4):** two-stage resampling. Draw a calibration set by resampling UTSW calibration patients, refit
  the conformal quantile, then draw a test set by resampling the evaluation cohort and measure coverage. 2000 pairs. The
  deviation is empirical minus nominal coverage, per condition and per alpha.
- **Permutation tests** (C6): 10,000 permutations. **DeLong** for paired AUROC comparisons between models on the same
  patients (SPEC §5.5).
- Every resampling script takes a seed from config; the seed for each analysis is listed in the run record.

## 5. Claim decision rules (D-035, three-way)

Let `D(phi)` be selective risk of the mechanism minus always-predict risk at grid coverage `phi`, paired bootstrap.

| Claim | Unit | Supported | Refuted (the SPEC's refuting event) | Otherwise |
|---|---|---|---|---|
| C1 | M5 on UTSW internal test, `full` | upper 95% limit of `D(phi)` < 0 at every `phi` | point estimate of `D(phi)` >= 0 at any `phi` | inconclusive at this n |
| C2 | M5 on UTSW internal test, each of the five missing-modality conditions | as C1, per condition | as C1, per condition | inconclusive at this n |
| C3 | M5 on UCSF-PDGM and on EGD, `full` (and each missing-modality condition, reported as secondary) | as C1, per cohort | as C1, per cohort | inconclusive at this n |
| C4 | M5 set-valued at each alpha, every condition | 95% half-width of the coverage-deviation interval <= 7 pp (the deviation can be characterized) | half-width > 7 pp in any condition (D-004) | not applicable; each condition is also labelled preserved (interval inside the band), degraded (interval wholly outside) or indeterminate |
| C5 | M5 curves in every condition | no increase in risk between adjacent grid coverages | a statistically significant increase (lower 95% limit > 0) between any adjacent grid pair | inconclusive at this n |
| C6 | M5, every condition | one-sided permutation p < 0.05 after BH across the grid, at every `phi` | point estimate of (error rate among abstained) minus (overall error rate) <= 0 at any `phi` | inconclusive at this n |

The claim-level status is the worst status across the conditions the claim covers, and every per-condition status is
reported next to it. C4 also reports the +/-5 pp band as secondary.

## 6. Multiplicity (Benjamini-Hochberg)

One BH family at q = 0.05 over the confirmatory comparisons of SPEC §4.9 (*proposed* composition, to confirm at the freeze).
P-values come from the paired bootstrap (two-sided) unless the row says DeLong.

| Block | Comparison | Tests with EGD | Tests without EGD |
|---|---|---|---|
| A | Uncertainty-method choice: AURC of M5 vs M3, M5 vs M4, M3 vs M4, `full`, per cohort | 9 | 6 |
| B | Missing modalities: AURC of M5 in each of the five missing-modality conditions vs `full`, per cohort | 15 | 10 |
| C | Internal vs external: AURC of M5, `full`, UCSF-PDGM vs UTSW and EGD vs UTSW (unpaired) | 2 | 1 |
| D | Calibration alone: M1 vs M2 on ECE and on Brier, `full`, per cohort | 6 | 4 |
| E | Confirmatory ablations: R7 (whole-brain pooling) and R8 (two-stage) each vs R2, AUROC (DeLong) and AURC, `full`, per cohort | 12 | 8 |
| | **Total** | **44** | **29** |

Outside the family: C1-C6 decision rules (own rules above), the 1p/19q probe (exploratory, D-007, confidence intervals
only, no tests), reliability diagrams, and every descriptive table. The always-predict vs selective comparison
(§4.9 row 4) is C1-C3.

## 7. Reporting rules

- AUROC is never reported without ECE, Brier, AURC and coverage next to it. PR-AUC is reported next to ROC-AUC (class
  imbalance, SPEC §5.4).
- Every table reports the number of patients behind it. Cells that cannot be computed are shown as absent with the reason.
- The rate at which abstained patients would have been classified correctly is reported for every condition (SPEC §5.4,
  claim C6).
- Negative and inconclusive results are reported in full; no experiment is re-run, re-tuned or re-scoped because of its outcome.

## 8. Limits stated in advance

Internal test n is about 124 (35 mutant): AUROC half-width about +/-0.09 and selective-risk half-width +/-0.06 to +/-0.09 at
every grid coverage even with a perfectly calibrated model (`POWER_CHECK.md`). Differences smaller than that will come out
inconclusive. 1p/19q has about 12 co-deleted patients in the internal test set. These are properties of the data, not
of the analysis.
