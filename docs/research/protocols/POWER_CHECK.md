# Phase 05 power check (T05.1)

Written 2026-09-30. Simulation only: no image data and no UCSF-PDGM or EGD labels were read. Reproduce with
`python scripts/power_check_phase05.py --n-mutant 173 --n-wildtype 443 --out docs/research/protocols/power_check_results.json`
(seed 20260930, 300 simulated test sets, 1000 bootstrap resamples each; two runs give byte-identical output).
Results file: `docs/research/protocols/power_check_results.json`. Tests: `tests/unit/test_power_check_phase05.py`.

## Inputs

Post-QC UTSW: 616 patients, IDH-mutant 173, IDH-wildtype 443 (mutant share 28.1%). Recomputed from
`data/raw/UTSW_Glioma_Metadata-2-1.tsv` minus `exclusion_manifest_post_qc.json`, and equal to
`POST_EXCLUSION_CLASS_COUNTS.md`. Test and calibration sets are stratified on IDH, so the mutant share carries over.

## Model behind the numbers

Equal-variance binormal scores at a stated true AUROC, with the exact posterior as the predicted probability (perfectly
calibrated, so the numbers show sampling noise only; a real, miscalibrated model does worse). Prediction is
`p > 0.5`, confidence is `max(p, 1 - p)`, selective risk is the 0-1 error rate of the top `round(phi * n)` cases by
confidence. Intervals are 95% percentile bootstrap over test patients, averaged over the 300 simulated test sets.

## Split options (616 patients)

| Split | Train | Calibration | Test | Test mutants |
|---|---|---|---|---|
| 60/20/20 (SPEC default) | 370 | 123 | 123 | 35 |
| 50/25/25 | 308 | 154 | 154 | 43 |
| 60/15/25 | 370 | 92 | 154 | 43 |
| 70/15/15 | 432 | 92 | 92 | 26 |

## Internal AUROC, 95% CI half-width (60/20/20, n_test = 123)

| True AUROC | Bootstrap | Hanley-McNeil |
|---|---|---|
| 0.75 | 0.094 | 0.103 |
| 0.80 | 0.086 | 0.095 |
| 0.85 | 0.073 | 0.085 |
| 0.90 | 0.059 | 0.071 |

The percentile bootstrap is 8-17% narrower than the Hanley-McNeil formula at this n. Quote the larger figure when
planning. Other splits, bootstrap: 50/25/25 gives 0.083 / 0.076 / 0.066 / 0.053; 70/15/15 gives 0.110 / 0.099 / 0.085 / 0.067.

## Selective risk at fixed coverage (60/20/20, bootstrap 95% CI half-width; expected risk in brackets)

| True AUROC | phi 0.9 (111 kept) | 0.8 (98) | 0.7 (86) | 0.6 (74) | 0.5 (62) |
|---|---|---|---|---|---|
| 0.75 | 0.079 (0.225) | 0.081 (0.200) | 0.083 (0.178) | 0.085 (0.157) | 0.088 (0.137) |
| 0.80 | 0.075 (0.198) | 0.077 (0.171) | 0.077 (0.149) | 0.079 (0.129) | 0.079 (0.106) |
| 0.85 | 0.070 (0.164) | 0.070 (0.135) | 0.069 (0.111) | 0.068 (0.089) | 0.065 (0.071) |
| 0.90 | 0.063 (0.124) | 0.061 (0.094) | 0.057 (0.071) | 0.052 (0.054) | 0.047 (0.039) |

The half-width does not fall as coverage falls. At true AUROC 0.85 the risk drops from 0.164 to 0.071 between phi 0.9
and 0.5, a change about the size of one half-width, so individual grid points are not separately resolvable.
Adjacent points are strongly correlated, so a paired bootstrap of the difference would be narrower; that was not
simulated here.

## Split-conformal coverage given the calibration draw (exact Beta law, no simulation)

For a calibration set of n points, coverage on fresh exchangeable data is Beta(n + 1 - l, l) with l = floor((n + 1) alpha),
before any test-set noise or dataset shift.

| Calibration n | alpha | Mean | SD | 95% interval |
|---|---|---|---|---|
| 123 | 0.05 | 0.952 | 0.019 | 0.908 - 0.982 |
| 123 | 0.10 | 0.903 | 0.026 | 0.846 - 0.949 |
| 123 | 0.20 | 0.807 | 0.035 | 0.733 - 0.871 |
| 154 | 0.10 | 0.903 | 0.024 | 0.852 - 0.944 |
| 92 | 0.10 | 0.903 | 0.031 | 0.836 - 0.954 |

## What this means for D-004

D-004 justifies a +/-5 pp band by the external test-set half-width alone (about 2.7 pp at n = 450-500, 4.1 pp at
n = 202). That term is real, but the calibration draw adds another 2.4-3.1 pp of SD. Combined, under exchangeability
(no shift at all), for alpha = 0.10:

| Calibration n | External n | SD of deviation | 95% half-width | P(deviation beyond 5 pp) |
|---|---|---|---|---|
| 123 | 450 | 3.0 pp | 5.9 pp | 9.5% |
| 123 | 202 (UCSF-PDGM only) | 3.4 pp | 6.6 pp | 13.9% |
| 154 | 450 | 2.8 pp | 5.4 pp | 7.0% |
| 92 | 202 | 3.7 pp | 7.3 pp | 17.8% |

No feasible calibration size on 616 patients brings the 95% half-width under 5 pp. See the D-004 update.

## Coverage grid

Every kept-case count at phi 0.5 to 0.9 stays at or above 62 (60/20/20), so the five-point grid phi in {0.9, 0.8, 0.7,
0.6, 0.5} is usable for display. The half-widths above are about 0.05-0.09 at every grid point, so no finer grid adds
independent information for hypothesis tests. Recommendation: keep the five points for pre-registered inference, draw
the continuous curve, and put the headline claim on AURC rather than on any single phi. The 0.05 width criterion is
mine, not the phase file's; the Research Lead can set a different one.

## 1p/19q (input to D-007)

UTSW post-QC has 62 co-deleted and 270 non-co-deleted labelled patients (284 unlabelled). A 20% test share holds about
12 co-deleted and 54 non-co-deleted. Hanley-McNeil 95% half-width for AUROC there is 0.18 at true AUROC 0.7, 0.16 at
0.8, 0.12 at 0.9. UCSF-PDGM adds 13 co-deleted. That supports the exploratory label already in the SPEC and nothing
stronger.

## Limits of this check

- Perfectly calibrated posterior; a real model adds calibration error on top of these widths.
- Binormal equal-variance scores; real score distributions differ.
- The test and calibration draws are treated as independent of each other and of training.
- Only the UTSW internal test set and the exchangeable case are covered. Shifted coverage on UCSF-PDGM or EGD is
  not simulated and must not be estimated from labels before Gate E.
- Paired differences between coverage levels, and the effect of training-set size on model AUROC, were not measured.
