# Phase 09 internal results: selective prediction on R2 with a five-member ensemble (UTSW internal test only)

Generated 2026-11-14 by `scripts/analyze_phase09.py` (analysis code at `989d049`) from the frozen artifacts; every number below is read from `phase09_analysis.json` by a script, none is typed by hand. Artifact SHA-256 `99f48c7dd3069fc657f15f1009c0d6628fbe5369b9f79e96259de420f99dc3e9`. Internal data only: 124 internal-test patients. No UCSF-PDGM or EGD label was read; C3 is not evaluated and stays locked until Gate E.

- Primary run R2 `01M46999FB083AX4WW0067YM13`, checkpoint `1d0c53023fef5615...`, full-input temperature T = 1.125.
- M4 deep ensemble, N = 5: R2 to R6 (seeds 0 to 4). Checkpoint hashes are in `provenance.ensemble_checkpoint_hashes`.
- Bootstrap 2000 draws, permutation test 10000 permutations, MC-dropout 30 passes, seed 0.
- M1, M2 and M5 rank patients identically (D-047), so they share one risk-coverage curve; every claim below is read on that curve (M5, the primary mechanism).
- M6 is absent in every cell. Correction 2026-11-17: this line first said M6 needs its own training run (D-006). That was wrong: D-005 and D-006 say M6 needs no extra training run. Which trained model serves as M6 is open (D-056).
- Calibration used the same 124-patient split that chose the checkpoint (D-039), so coverage results carry that selection effect.

## Claim adjudication (frozen rules, `PHASE09_STATS_CONTRACTS.md` D1 to D4)

| Claim | Status | What decides it |
|---|---|---|
| C1 | **supported** | `full`: all five coverage levels have an upper 95% limit below 0 |
| C2 | **refuted** | worst of five conditions: drop_t1 inconclusive, drop_t1ce refuted, drop_t2 supported, drop_flair supported, t1ce_flair_only inconclusive |
| C3 | not evaluated | external cohorts locked until Gate E |
| C4 | **refuted** | band 0.07 (primary): full refuted, drop_t1 refuted, drop_t1ce refuted, drop_t2 refuted, drop_flair refuted, t1ce_flair_only refuted; band 0.05 (secondary): refuted |
| C5 | **inconclusive** | full supported, drop_t1 supported, drop_t1ce inconclusive, drop_t2 inconclusive, drop_flair supported, t1ce_flair_only inconclusive |
| C6 | **refuted** | full supported, drop_t1 inconclusive, drop_t1ce refuted, drop_t2 supported, drop_flair supported, t1ce_flair_only inconclusive |

Rules: C1 to C3 refuted if any point estimate of D(phi) is at or above 0, supported if every upper 95% limit is below 0, otherwise inconclusive. C5 refuted if any adjacent-pair lower 95% limit is above 0, supported if every point estimate is at or below 0 (D-050 reading a). C6 refuted if any observed enrichment is at or below 0, supported if every BH-adjusted p is below 0.05. C4 refuted if any condition has a coverage-deviation interval whose half-width exceeds the 0.07 band. Worst status over conditions decides the claim.

### C1 and C2: D(phi) = selective risk minus always-predict risk (negative favours selective prediction)

Point estimate with 95% paired-bootstrap interval, M5, per target coverage.

| Condition | phi 0.9 | phi 0.8 | phi 0.7 | phi 0.6 | phi 0.5 | Status |
|---|---|---|---|---|---|---|
| full | -0.048 (-0.066, -0.009) | -0.058 (-0.102, -0.020) | -0.103 (-0.149, -0.044) | -0.124 (-0.191, -0.070) | -0.169 (-0.235, -0.097) | supported |
| drop_t1 | -0.017 (-0.036, 0.016) | -0.027 (-0.065, 0.012) | -0.051 (-0.104, -0.004) | -0.084 (-0.144, -0.020) | -0.129 (-0.187, -0.058) | inconclusive |
| drop_t1ce | 0.012 (-0.014, 0.043) | 0.048 (0.008, 0.095) | 0.065 (0.002, 0.136) | 0.054 (-0.026, 0.126) | 0.016 (-0.073, 0.118) | refuted |
| drop_t2 | -0.052 (-0.069, -0.010) | -0.055 (-0.096, -0.013) | -0.094 (-0.137, -0.038) | -0.105 (-0.164, -0.048) | -0.105 (-0.178, -0.048) | supported |
| drop_flair | -0.038 (-0.059, -0.001) | -0.046 (-0.098, -0.012) | -0.076 (-0.126, -0.018) | -0.092 (-0.157, -0.023) | -0.145 (-0.210, -0.065) | supported |
| t1ce_flair_only | -0.021 (-0.046, 0.013) | -0.038 (-0.078, 0.008) | -0.045 (-0.106, -0.002) | -0.058 (-0.119, 0.006) | -0.056 (-0.139, 0.014) | inconclusive |

### Always-predict risk, AURC and monotonicity by mechanism (95% bootstrap interval on AURC)

| Condition | Always-predict risk | Oracle AURC | M2/M5 AURC | M3 AURC | M4 AURC | Random-confidence AURC | Max grid gap, random vs always-predict |
|---|---|---|---|---|---|---|---|
| full | 0.218 | 0.0265 | 0.0755 (0.041, 0.123) | 0.0804 (0.044, 0.130) | 0.0796 (0.041, 0.129) | 0.2303 | 0.049 |
| drop_t1 | 0.177 | 0.0175 | 0.0759 (0.039, 0.128) | 0.0798 (0.041, 0.132) | 0.0707 (0.033, 0.123) | 0.2140 | 0.049 |
| drop_t1ce | 0.532 | 0.1790 | 0.4927 (0.379, 0.616) | 0.4733 (0.365, 0.599) | 0.3702 (0.272, 0.492) | 0.5804 | 0.048 |
| drop_t2 | 0.185 | 0.0191 | 0.0730 (0.036, 0.122) | 0.0746 (0.036, 0.126) | 0.0785 (0.034, 0.138) | 0.2282 | 0.041 |
| drop_flair | 0.226 | 0.0286 | 0.1082 (0.058, 0.177) | 0.1064 (0.057, 0.173) | 0.1118 (0.059, 0.178) | 0.2554 | 0.068 |
| t1ce_flair_only | 0.218 | 0.0265 | 0.1135 (0.064, 0.176) | 0.1170 (0.066, 0.183) | 0.1239 (0.051, 0.215) | 0.2045 | 0.049 |

Random-confidence control (Phase 09 sanity check): a flat curve means the random AURC sits near the always-predict risk and the grid gap is small. The grid gap is not zero because 124 patients is a small sample; it is the largest absolute difference over the five grid coverages.

Monotonicity violations (pairs, magnitude with 95% interval), M2/M5 and M4:

| Condition | M2/M5 violations | M2/M5 magnitude (95%) | M4 violations | M4 magnitude (95%) |
|---|---|---|---|---|
| full | 253 | 1.082 (0.148, 2.770) | 553 | 3.110 (0.495, 6.157) |
| drop_t1 | 422 | 1.898 (0.237, 6.559) | 712 | 5.366 (0.521, 17.110) |
| drop_t1ce | 1467 | 49.225 (7.522, 100.953) | 1691 | 40.332 (4.794, 88.227) |
| drop_t2 | 361 | 1.440 (0.403, 9.996) | 1119 | 8.245 (0.562, 40.077) |
| drop_flair | 604 | 4.003 (0.590, 23.058) | 413 | 2.003 (0.793, 23.827) |
| t1ce_flair_only | 416 | 2.331 (0.580, 14.302) | 4121 | 113.079 (3.857, 234.639) |

### Selective risk at target coverage (M5), attained coverage and rejected-but-correct rate

| Condition | phi 0.9 | phi 0.8 | phi 0.7 | phi 0.6 | phi 0.5 |
|---|---|---|---|---|---|
| full | risk 0.170 @ 0.903; RBC 0.333 of 12 | risk 0.160 @ 0.806; RBC 0.542 of 24 | risk 0.115 @ 0.702; RBC 0.541 of 37 | risk 0.093 @ 0.605; RBC 0.592 of 49 | risk 0.048 @ 0.500; RBC 0.613 of 62 |
| drop_t1 | risk 0.161 @ 0.903; RBC 0.667 of 12 | risk 0.150 @ 0.806; RBC 0.708 of 24 | risk 0.126 @ 0.702; RBC 0.703 of 37 | risk 0.093 @ 0.605; RBC 0.694 of 49 | risk 0.048 @ 0.500; RBC 0.694 of 62 |
| drop_t1ce | risk 0.545 @ 0.903; RBC 0.583 of 12 | risk 0.580 @ 0.806; RBC 0.667 of 24 | risk 0.598 @ 0.702; RBC 0.622 of 37 | risk 0.587 @ 0.605; RBC 0.551 of 49 | risk 0.548 @ 0.500; RBC 0.484 of 62 |
| drop_t2 | risk 0.134 @ 0.903; RBC 0.333 of 12 | risk 0.130 @ 0.806; RBC 0.583 of 24 | risk 0.092 @ 0.702; RBC 0.595 of 37 | risk 0.080 @ 0.605; RBC 0.653 of 49 | risk 0.081 @ 0.500; RBC 0.710 of 62 |
| drop_flair | risk 0.188 @ 0.903; RBC 0.417 of 12 | risk 0.180 @ 0.806; RBC 0.583 of 24 | risk 0.149 @ 0.702; RBC 0.595 of 37 | risk 0.133 @ 0.605; RBC 0.633 of 49 | risk 0.081 @ 0.500; RBC 0.629 of 62 |
| t1ce_flair_only | risk 0.196 @ 0.903; RBC 0.583 of 12 | risk 0.180 @ 0.806; RBC 0.625 of 24 | risk 0.172 @ 0.702; RBC 0.676 of 37 | risk 0.160 @ 0.605; RBC 0.694 of 49 | risk 0.161 @ 0.500; RBC 0.726 of 62 |

RBC = rejected-but-correct rate (share of rejected patients whose prediction was right).

### C5: adjacent-coverage risk change (lower coverage minus higher coverage; positive = risk rose when rejecting more)

| Condition | 0.9->0.8 | 0.8->0.7 | 0.7->0.6 | 0.6->0.5 | Status |
|---|---|---|---|---|---|
| full | -0.010 | -0.045 | -0.022 | -0.045 | supported |
| drop_t1 | -0.011 | -0.024 | -0.033 | -0.045 | supported |
| drop_t1ce | 0.035 | 0.018 | -0.011 | -0.038 | inconclusive |
| drop_t2 | -0.004 | -0.038 | -0.012 | 0.001 | inconclusive |
| drop_flair | -0.008 | -0.031 | -0.016 | -0.053 | supported |
| t1ce_flair_only | -0.016 | -0.008 | -0.012 | 0.001 | inconclusive |

### C6: abstention enrichment (error rate among rejected minus overall error rate), M5

Observed difference per target coverage with BH-adjusted one-sided permutation p over the five coverages.

| Condition | phi 0.9 | phi 0.8 | phi 0.7 | phi 0.6 | phi 0.5 | Status |
|---|---|---|---|---|---|---|
| full | 0.449 (p 0.001) | 0.241 (p 0.003) | 0.242 (p <0.001) | 0.190 (p <0.001) | 0.169 (p <0.001) | supported |
| drop_t1 | 0.156 (p 0.135) | 0.114 (p 0.114) | 0.120 (p 0.038) | 0.129 (p 0.006) | 0.129 (p 0.002) | inconclusive |
| drop_t1ce | -0.116 (p 0.993) | -0.199 (p 0.993) | -0.154 (p 0.993) | -0.083 (p 0.993) | -0.016 (p 0.993) | refuted |
| drop_t2 | 0.481 (p <0.001) | 0.231 (p 0.002) | 0.220 (p <0.001) | 0.161 (p <0.001) | 0.105 (p 0.003) | supported |
| drop_flair | 0.358 (p 0.008) | 0.191 (p 0.017) | 0.180 (p 0.005) | 0.142 (p 0.005) | 0.145 (p <0.001) | supported |
| t1ce_flair_only | 0.199 (p 0.097) | 0.157 (p 0.094) | 0.107 (p 0.094) | 0.088 (p 0.094) | 0.056 (p 0.097) | inconclusive |

### C4 and conformal coverage (M5, split conformal on the temperature-scaled probability)

Test coverage minus nominal is characterized by a two-stage bootstrap (calibration and test resampled together). Carried-over = full-input calibration reused; refit = calibration re-run under the same dropped modalities.

| Condition | alpha | Empirical coverage (carried / refit) | Abstention (carried / refit) | Deviation interval (carried) | Half-width | Label, band 0.07 |
|---|---|---|---|---|---|---|
| full | 0.05 | 0.960 / 0.960 | 0.411 / 0.411 | -0.103 to 0.050 | 0.077 | indeterminate |
| full | 0.1 | 0.871 / 0.871 | 0.185 / 0.185 | -0.150 to 0.044 | 0.097 | indeterminate |
| full | 0.2 | 0.726 / 0.726 | 0.121 / 0.121 | -0.219 to 0.039 | 0.129 | indeterminate |
| drop_t1 | 0.05 | 0.952 / 0.935 | 0.411 / 0.387 | -0.103 to 0.050 | 0.077 | indeterminate |
| drop_t1 | 0.1 | 0.871 / 0.887 | 0.177 / 0.226 | -0.126 to 0.044 | 0.085 | indeterminate |
| drop_t1 | 0.2 | 0.758 / 0.758 | 0.097 / 0.089 | -0.195 to 0.055 | 0.125 | indeterminate |
| drop_t1ce | 0.05 | 0.758 / 0.960 | 0.556 / 0.855 | -0.402 to 0.042 | 0.222 | indeterminate |
| drop_t1ce | 0.1 | 0.589 / 0.927 | 0.306 / 0.815 | -0.481 to -0.150 | 0.165 | degraded |
| drop_t1ce | 0.2 | 0.347 / 0.823 | 0.177 / 0.653 | -0.590 to -0.292 | 0.149 | degraded |
| drop_t2 | 0.05 | 0.960 / 0.919 | 0.468 / 0.242 | -0.079 to 0.050 | 0.065 | indeterminate |
| drop_t2 | 0.1 | 0.887 / 0.863 | 0.177 / 0.081 | -0.110 to 0.076 | 0.093 | indeterminate |
| drop_t2 | 0.2 | 0.750 / 0.782 | 0.129 / 0.081 | -0.227 to 0.063 | 0.145 | indeterminate |
| drop_flair | 0.05 | 0.903 / 0.935 | 0.379 / 0.419 | -0.111 to 0.042 | 0.077 | indeterminate |
| drop_flair | 0.1 | 0.887 / 0.887 | 0.242 / 0.266 | -0.158 to 0.035 | 0.097 | indeterminate |
| drop_flair | 0.2 | 0.677 / 0.806 | 0.177 / 0.065 | -0.236 to 0.023 | 0.129 | indeterminate |
| t1ce_flair_only | 0.05 | 0.919 / 0.903 | 0.460 / 0.403 | -0.111 to 0.050 | 0.081 | indeterminate |
| t1ce_flair_only | 0.1 | 0.863 / 0.895 | 0.218 / 0.339 | -0.158 to 0.035 | 0.097 | indeterminate |
| t1ce_flair_only | 0.2 | 0.710 / 0.782 | 0.121 / 0.000 | -0.260 to 0.023 | 0.141 | indeterminate |

Half-widths run from 0.065 to 0.222 against a band of 0.07; 1 of 18 condition-alpha cells meet it (drop_t2 alpha 0.05 (0.065)). Labels at band 0.07: 0 preserved, 2 degraded (drop_t1ce alpha 0.1; drop_t1ce alpha 0.2), 16 indeterminate. The claim rule uses the half-width only, so a cell labelled `degraded` still counts against C4 when its half-width is above the band.

## What this does and does not show

- Single split, 124 test patients (35 mutant in the test split), one primary model. Intervals are wide and most claim cells that are not supported are inconclusive for that reason.
- C2 is refuted by the T1ce-dropped condition alone: D(phi) is positive at every coverage level there (selective prediction does worse than always-predict), and its 95% interval excludes 0 only at phi 0.8 and 0.7. The rule refutes on any point estimate at or above 0. The always-predict risk in that condition is above 0.5 and `drop_t1ce` has the lowest AUROC in every run (Phase 08 file), the clinically expected direction.
- C4 is refuted under the frozen half-width rule: only one of 18 cells meets the 0.07 band, and `full` does not (half-width 0.077 at alpha 0.05). That is mostly interval width at n = 124, not a coverage failure. The one real coverage failure is `drop_t1ce` with full-input calibration carried over: empirical coverage 0.589 at nominal 0.90 and 0.347 at nominal 0.80, labelled degraded; refitting calibration under the dropped modality restores it (0.927, 0.823). Whether the half-width rule or the criterion text (cannot distinguish preserved from degraded) should govern a cell labelled degraded is a Research Lead question; no number is changed here.
- C6 is refuted by the T1ce-dropped condition: abstained patients are not more error-prone than the rest (observed enrichment negative at every coverage level).
- M4 (ensemble of 5) has a lower AURC than the single-model ranking in drop_t1, drop_t1ce and a higher one in full, drop_t2, drop_flair, t1ce_flair_only; every pair of intervals overlaps heavily. Descriptive only, not a pre-registered claim.
- M6 is a separate always-predict comparator (PREREGISTRATION.md section 4) and is not computed here; which already-trained model it is, is open (D-056). The claim rules measure D(phi) against the always-predict risk of the same predictions, so its absence does not change any C1 to C6 status here.
- Not yet done for Phase 09 acceptance: independent recomputation by Person C (scientific validation 2), Gate D.

## Draft entries for `paper/NEGATIVE_RESULTS.md` (Research Lead to place; `paper/` is human-owned)

Refutation criteria are the verbatim PREREGISTRATION.md section 9 text. Date found: 2026-11-14. Evidence artifact: `phase09_analysis.json` for run `01M46999FB083AX4WW0067YM13`, SHA-256 `99f48c7dd3069fc657f15f1009c0d6628fbe5369b9f79e96259de420f99dc3e9`.

| Date | Claim | Criterion met (verbatim) | Cohort / condition | Evidence | Phase |
|---|---|---|---|---|---|
| 2026-11-14 | C2 | Selective-risk advantage over always-predict disappears or reverses when 1-2 sequences are dropped. | UTSW internal test, `drop_t1ce`: D(phi) = 0.012, 0.048, 0.065, 0.054, 0.016 at phi 0.9 to 0.5 (positive means worse than always-predict) | `phase09_analysis.json` `claims.C2.drop_t1ce` | 09 |
| 2026-11-14 | C4 | The deviation cannot be reliably characterized, e.g. empirical coverage estimates are too noisy/unstable (given sample size) to distinguish "coverage preserved" from "coverage degraded" at the pre-registered tolerance. | UTSW internal test, all six conditions, alpha 0.05, 0.1, 0.2; deviation-interval half-widths 0.065 to 0.222 against a 0.07 band; 1 of 18 cells meet it; labels 0 preserved, 2 degraded, 16 indeterminate | `phase09_analysis.json` `claims.C4` | 09 |
| 2026-11-14 | C6 | Abstained cases are no more likely to be erroneous than randomly selected cases of equal size. | UTSW internal test, `drop_t1ce`: observed enrichment -0.116, -0.199, -0.154, -0.083, -0.016 at phi 0.9 to 0.5 (all at or below 0) | `phase09_analysis.json` `claims.C6.drop_t1ce` | 09 |
