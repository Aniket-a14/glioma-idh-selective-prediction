# Phase 10 internal results (PRELIMINARY: R7 and R8 not yet trained; UTSW internal test only)

Generated 2026-11-14 from `phase10_analysis_preliminary_20261114b.json` (SHA-256 `09dd37a07e023c61721495a43193f97c086ab12b624f6935afdde9e8b72ae33a`) and `probe_1p19q.json` (SHA-256 `0e5f2a18b6751a614b1dd00122576a95a5a63ea70a216bb1c694bbdf50a5c652`); every number is read from those files by a script. Analysis code at `88fbff0` (`scripts/analyze_phase10.py`), probe code at `9e501d4`. Internal data only: 124 UTSW internal-test patients; no UCSF-PDGM or EGD label was read. One shared resample matrix (2000 draws, seed 0); the primary run is R2 `01M46999FB083AX4WW0067YM13`, the ensemble is R2 to R6.

**Status.** Preliminary. The final run of `analyze_phase10.py` writes `phase10_analysis.json` once R7 and R8 have frozen predictions; the confirmatory entries E1 to E4 (R7 and R8 against R2) and the R7 and R8 per-run metrics are absent here. Nothing in this file is a Gate D claim: independent recomputation by Person C and the independent review are still open,

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
| E1 | AUROC(R7) - AUROC(R2), full | absent | | R7 has no frozen predictions |
| E2 | AURC(R7) - AURC(R2), full | absent | | R7 has no frozen predictions |
| E3 | AUROC(R8) - AUROC(R2), full | absent | | R8 has no frozen predictions |
| E4 | AURC(R8) - AURC(R2), full | absent | | R8 has no frozen predictions |

Family listing: 29 members, 10 computed, 4 absent (R7 and R8 predictions), 15 pending external (UCSF-PDGM, Phase 12). The Benjamini-Hochberg pass over the full family runs once, at the Phase 13 freeze (D-052, accepted 2026-11-14).

### Supplementary: BH over the 10 computed UTSW members only (supplementary; not the pre-registered family (D-052)), q = 0.05

| Id | Adjusted p | Reject |
|---|---|---|
| A1 | 0.322 | no |
| A2 | 0.985 | no |
| A3 | 0.985 | no |
| B1 | 0.985 | no |
| B2 | 0.010 | yes |
| B3 | 0.985 | no |
| B4 | 0.322 | no |
| B5 | 0.322 | no |
| D1 | 0.985 | no |
| D2 | 0.760 | no |

Reading: dropping T1ce raises the AURC by about 0.42 (B2) and is the only comparison with a raw p below 0.05; it is also the only member that survives the supplementary adjustment. The uncertainty-method comparisons (A1 to A3) and raw against temperature-scaled calibration (D1, D2) show no detectable difference at n = 124, with all point differences under 0.005 in absolute value.

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

- R7 (whole-brain pooling) and R8 (two-stage) are training or queued on the home GPU (D-051); E1 to E4 and their per-run metrics follow in the final `phase10_analysis.json`. The preliminary file is kept beside it as a record.
- T10.10: HD95 for R2 is done above; R7 and R8 follow when trained (`scripts/freeze_segmentation_hd95.py`).
- T10.8: DeLong cross-check passed (1000 random cases against an independent midrank implementation); bootstrap and BH cross-checks agree on the Phase 09 fixtures; the paired-bootstrap p-value (S2, S3) was checked against an independent loop on 50 random cases.
- Independent recomputation of every headline number by Person C, Gate D review, and the single Benjamini-Hochberg pass at Phase 13.
