# Phase 10 internal results (UTSW internal test only; final run with R7 and R8)

Generated 2026-11-17 from `phase10_analysis.json` (SHA-256 `3d2a220c49b558a543833057514ea65f733a80f5e49aa04411fd776ffd271f54`, analysis code at `5b6878c`) and, for the 1p/19q section written 2026-11-14, `probe_1p19q.json` (SHA-256 `0e5f2a18b6751a614b1dd00122576a95a5a63ea70a216bb1c694bbdf50a5c652`); every number is read from those files by a script. The R2 sections below are unchanged from the preliminary file `phase10_analysis_preliminary_20261114b.json` (SHA-256 `09dd37a07e023c61721495a43193f97c086ab12b624f6935afdde9e8b72ae33a`, kept beside the final file); probe code at `9e501d4`. Internal data only: 124 UTSW internal-test patients; no UCSF-PDGM or EGD label was read. One shared resample matrix (2000 draws, seed 0); the primary run is R2 `01M46999FB083AX4WW0067YM13`, the ensemble is R2 to R6, R7 is `01M7C0KRNY5M2SNH59PH97XZ8K` and R8 is stage 1 `01M7ETEEYVT8KXCVJSQS5R7KJC` plus stage 2 `01M7JZYEBFCJF8WY0W1WJ3RZX7`.

**Status.** Final for the UTSW members of the family: R7 and R8 now have frozen predictions and E1 to E4 are computed. Nothing in this file is a Gate D claim: independent recomputation by Person C and the independent review are still open.

## R2 on the internal test: metrics with 95% intervals (acceptance criterion 3)

| Metric | Point | 95% interval | Note |
|---|---|---|---|
| AUROC | 0.878 | bootstrap (0.808, 0.939); Hanley-McNeil (0.801, 0.956) | quoted: hanley_mcneil (the wider, SAP section 4) |
| AUPRC | 0.778 | (0.647, 0.884) | |
| AURC (mean over cutoffs), M5 ranking | 0.0755 | (0.041, 0.123) | M1, M2 and M5 share the ranking (D-047) |
| ECE, 10 bins, M1 (raw probability) | 0.119 | (0.087, 0.190) | |
| Brier, M1 (raw probability) | 0.140 | (0.104, 0.181) | |
| ECE, 10 bins, M2 (temperature-scaled, T = 1.125) | 0.122 | (0.090, 0.194) | |
| Brier, M2 (temperature-scaled, T = 1.125) | 0.139 | (0.104, 0.177) | |

Selective risk at each target coverage (M5):

| Coverage | Attained | Risk | 95% interval |
|---|---|---|---|
| 0.5 | 0.500 | 0.048 | (0.000, 0.127) |
| 0.6 | 0.605 | 0.093 | (0.026, 0.173) |
| 0.7 | 0.702 | 0.115 | (0.056, 0.205) |
| 0.8 | 0.806 | 0.160 | (0.080, 0.240) |
| 0.9 | 0.903 | 0.170 | (0.107, 0.259) |

Auxiliary segmentation Dice (internal test, 124 patients with a mask): mean 0.473; enhancing 0.431, necrotic core 0.390, oedema 0.597.

### Auxiliary segmentation HD95 (R2, internal test; T10.10, D-053)

HD95 in mm on the 2 mm preprocessing grid (values are quantized to the voxel size), larger of the two directed 95th percentiles of surface distances, mask `sigmoid > 0.5`. HD95 is undefined when either mask is empty, so two tables are given (D-053). **Primary**: only patients where both masks are non-empty, with the counts that are left out. **BraTS-style penalty**: both empty = 0 mm, exactly one empty = the grid-diagonal penalty (an arbitrary constant, shown).

| Channel | Patients | Evaluable | Missed (truth, no prediction) | False (prediction, no truth) | Both empty | Primary mean | Primary median (IQR) | Penalty-convention mean | Penalty-convention median |
|---|---|---|---|---|---|---|---|---|---|
| enhancing | 124 | 95 | 0 | 29 | 0 | 16.620 | 7.483 (5.657, 18.209) | 90.508 | 12.884 |
| necrotic_core | 124 | 117 | 4 | 3 | 0 | 12.926 | 9.165 (7.169, 14.560) | 30.970 | 9.165 |
| oedema | 124 | 124 | 0 | 0 | 0 | 19.453 | 8.485 (7.211, 13.598) | 19.453 | 8.485 |

Penalty used: 332.554 mm. The enhancing channel has many patients with no enhancing region in the ground truth but a predicted one (false), which is why the primary table matters: it leaves them out and says how many, instead of charging a constant. Dice scores those patients 0.

The `skipped_single_class_draws` count is 0 for AUROC and AUPRC (every draw has both classes at 35 mutant of 124).

## Confirmatory comparisons inside the pre-registered family (UTSW members; raw p-values)

Difference is first minus second; AURC and the calibration errors are lower-is-better, so a negative AURC difference favours the first. Raw two-sided paired-bootstrap p (D-052, `+1` convention); p `<0.001` means the smallest attainable value with 2000 draws (2/2001). No adjusted value appears in this table by design (D-052).

| Id | Comparison | Difference | 95% interval | Raw p |
|---|---|---|---|---|
| A1 | AURC(M5) - AURC(M3), full | -0.0048 | (-0.0120, 0.0006) | 0.084 |
| A2 | AURC(M5) - AURC(M4), full | -0.0040 | (-0.0367, 0.0292) | 0.826 |
| A3 | AURC(M3) - AURC(M4), full | 0.0008 | (-0.0321, 0.0368) | 0.931 |
| B1 | AURC(M5, drop_t1) - AURC(M5, full) | 0.0003 | (-0.0194, 0.0182) | 0.985 |
| B2 | AURC(M5, drop_t1ce) - AURC(M5, full) | 0.4172 | (0.2954, 0.5434) | <0.001 |
| B3 | AURC(M5, drop_t2) - AURC(M5, full) | -0.0026 | (-0.0255, 0.0204) | 0.779 |
| B4 | AURC(M5, drop_flair) - AURC(M5, full) | 0.0327 | (-0.0089, 0.0805) | 0.129 |
| B5 | AURC(M5, t1ce_flair_only) - AURC(M5, full) | 0.0379 | (-0.0091, 0.0886) | 0.118 |
| D1 | ECE(M1) - ECE(M2), full | -0.0033 | (-0.0276, 0.0223) | 0.668 |
| D2 | Brier(M1) - Brier(M2), full | 0.0012 | (-0.0014, 0.0041) | 0.380 |
| E1 | AUROC(R7) - AUROC(R2), full | 0.0096 | (-0.0261, 0.0468) | 0.597 (DeLong) |
| E2 | AURC(R7) - AURC(R2), full | 0.0173 | (-0.0237, 0.0703) | 0.516 (344/667) |
| E3 | AUROC(R8) - AUROC(R2), full | 0.0104 | (-0.0286, 0.0507) | 0.615 (DeLong) |
| E4 | AURC(R8) - AURC(R2), full | 0.0219 | (-0.0038, 0.0523) | 0.106 (212/2001) |

Family listing: 29 members, 14 computed, 15 pending external (UCSF-PDGM, Phase 12). The Benjamini-Hochberg pass over the full family runs once, at the Phase 13 freeze (D-052, accepted 2026-11-14).

### Supplementary: BH over the 14 computed UTSW members only (supplementary; not the pre-registered family (D-052)), q = 0.05

| Id | Adjusted p | Reject |
|---|---|---|
| A1 | 0.361 | no |
| A2 | 0.963 | no |
| A3 | 0.985 | no |
| B1 | 0.985 | no |
| B2 | 0.014 | yes |
| B3 | 0.963 | no |
| B4 | 0.361 | no |
| B5 | 0.361 | no |
| D1 | 0.935 | no |
| D2 | 0.886 | no |
| E1 | 0.935 | no |
| E2 | 0.935 | no |
| E3 | 0.935 | no |
| E4 | 0.361 | no |

Reading: dropping T1ce raises the AURC by about 0.42 (B2) and is the only comparison with a raw p below 0.05; it is also the only member that survives the supplementary adjustment. The uncertainty-method comparisons (A1 to A3) and raw against temperature-scaled calibration (D1, D2) show no detectable difference at n = 124, with all point differences under 0.005 in absolute value.

**R7 and R8 against R2 (E1 to E4).** All four intervals include 0. AUROC differences are +0.010 (R7) and +0.010 (R8) with raw p 0.60 and 0.61. AURC differences are positive, +0.017 (R7) and +0.022 (R8), which is the worse direction (lower AURC is better), with raw p 0.52 and 0.11. At n = 124 (35 mutant) the data show no detectable AUROC or AURC difference between R2 and either ablation; the AURC point estimates lean against R7 and R8 but the intervals are wide (R8: -0.004 to 0.052). These are not claims of equivalence. The two ablations were fixed in D-051 before any result and are reported whichever way they came out.

## R7 and R8 per-run metrics (internal test, 124 patients, 35 mutant)

| Metric | R2 | R7 (whole-brain pooling) | R8 (two-stage) |
|---|---|---|---|
| AUROC (bootstrap 95%) | 0.878 (0.808, 0.939) | 0.888 (0.820, 0.941) | 0.889 (0.816, 0.948) |
| AUPRC (bootstrap 95%) | 0.778 (0.647, 0.884) | 0.741 (0.585, 0.873) | 0.823 (0.708, 0.912) |
| AURC, M5 ranking (bootstrap 95%) | 0.0755 (0.041, 0.123) | 0.0929 (0.039, 0.166) | 0.0974 (0.057, 0.153) |
| ECE, M1 (raw) | 0.119 | 0.108 | 0.177 |
| Brier, M1 (raw) | 0.140 | 0.129 | 0.162 |
| Temperature T | 1.125 | 0.827 | 1.654 |
| ECE, M2 (temperature-scaled) | 0.122 | 0.109 | 0.173 |
| Brier, M2 (temperature-scaled) | 0.139 | 0.129 | 0.153 |
| Segmentation Dice, mean (enhancing / necrotic core / oedema) | 0.473 (0.431 / 0.390 / 0.597) | 0.485 (0.481 / 0.409 / 0.566) | 0.741 (0.799 / 0.605 / 0.819) |

R8 is the least calibrated of the three (raw ECE 0.177 against 0.119 and 0.108); temperature scaling moves it little. No interval or test is computed for the ECE and Brier columns across runs, so this is a point-estimate observation. R8 has much higher Dice because its stage 1 is trained on segmentation alone with a Dice loss (D-051); the comparison of segmentation quality is between a dedicated segmenter and a multitask head, not between equal designs. Calibration-set AUROC at the stopping epoch was near 0.92 for R7 and for R8 stage 2; the test-set values above are the numbers that count.

### Auxiliary segmentation HD95 (R7 and R8, internal test; T10.10, D-053)

Same definitions and caveats as the R2 table. Primary table (both masks non-empty):

| Run | Channel | Evaluable | Missed | False | Both empty | Primary mean | Primary median (IQR) | Penalty-convention mean |
|---|---|---|---|---|---|---|---|---|
| R7 | enhancing | 95 | 0 | 29 | 0 | 16.778 | 6.000 (4.472, 15.678) | 90.629 |
| R7 | necrotic_core | 121 | 0 | 3 | 0 | 15.869 | 10.954 (7.211, 15.620) | 23.531 |
| R7 | oedema | 124 | 0 | 0 | 0 | 21.920 | 9.798 (7.483, 15.185) | 21.920 |
| R8 | enhancing | 91 | 4 | 2 | 27 | 9.000 | 2.000 (2.000, 3.464) | 22.696 |
| R8 | necrotic_core | 113 | 8 | 3 | 0 | 7.273 | 6.227 (4.472, 9.165) | 36.129 |
| R8 | oedema | 124 | 0 | 0 | 0 | 7.800 | 3.464 (2.000, 6.081) | 7.800 |

Penalty 332.554 mm for all runs. R7's HD95 is close to R2's. R8's median surface distances are small (2 mm is one voxel on this grid) and it predicts "no enhancing region" in 27 patients where the truth also has none, which R2 and R7 never do (they predict an enhancing region in all 29 patients with none in the truth). The enhancing primary mean is not comparable across runs: the sets of evaluable patients differ (95, 95, 91).

## RQ4: 1p/19q frozen-encoder probe (exploratory, D-007; no inferential claim)

Probe: L2 logistic regression, C = 1, class-balanced, train-split standardization, 256 features, converged: True. Fitted on the 193 UTSW train patients with a 1p/19q label (37 co-deleted); scored on the 66 internal-test patients with a label (14 co-deleted). Frozen encoder: R2. Everything was fixed before the run; nothing was tuned. A null result would not be evidence of absence.

| Scores | n | Co-deleted | AUROC (95% bootstrap) | Hanley-McNeil half-width | AUPRC (95% bootstrap) |
|---|---|---|---|---|---|
| Probe, all labelled test patients | 66 | 14 | 0.787 (0.627, 0.919) | 0.151 | 0.587 (0.348, 0.822) |
| Comparator: R2 IDH probability, all labelled test patients | 66 | 14 | 0.714 (0.577, 0.846) | 0.165 | 0.334 (0.207, 0.570) |
| Probe, IDH-mutant test patients only | 28 | 14 | 0.673 (0.441, 0.870) | 0.202 | 0.763 (0.543, 0.915) |
| Comparator: R2 IDH probability, IDH-mutant only | 28 | 14 | 0.337 (no interval computed) | 0.203 | 0.410 |

Co-deletion occurs only in IDH-mutant patients in this test set (all 14 co-deleted patients are among the 28 IDH-mutant ones), so the all-patient AUROC partly re-reads IDH status; the IDH-mutant-only rows are the informative ones. Inside IDH-mutant patients the probe ranks co-deleted patients above the others (AUROC 0.673) where the IDH probability itself does not (0.337), but the probe interval (0.441, 0.870) includes 0.5. Descriptive only. The test set holds 66 labelled patients, not the 124 of the IDH analysis, because only patients with a 1p/19q result count.

## Open for Phase 10

- Record of the runs: R7 trained to epoch 99 (best epoch 69) and had one unexplained stop after epoch 71 and resumed from epoch 72; whether that resume matches an uninterrupted run is not verified. R8 stage 1 trained about 39 h, stage 2 stopped after epoch 46. R7 HD95 was frozen with `--allow-sha-mismatch` (run git SHA `0ad683e`, current `5b6878c`), as R2's was; the model config is read from the run record.
- T10.8: DeLong cross-check passed (1000 random cases against an independent midrank implementation); bootstrap and BH cross-checks agree on the Phase 09 fixtures; the paired-bootstrap p-value (S2, S3) was checked against an independent loop on 50 random cases.
- Independent recomputation of every headline number by Person C (pack ready: `scripts/person_c_recompute.py` and `PERSON_C_RECOMPUTATION_GUIDE.md`; the Research Lead's run of it reproduces 188 of 188 numbers, Person C has not run it yet), Gate D review, and the single Benjamini-Hochberg pass at Phase 13.
