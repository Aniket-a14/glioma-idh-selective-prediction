# Phase 08 internal results: missing-modality sweep for R2 to R6 (UTSW internal test only)

Generated 2026-11-14 from the frozen `conditions_analysis.json` of each run (SHA-256 sidecar beside each file). Every number below is read from those files by a script, none is typed by hand. Internal data only: 124 internal-test patients. No UCSF-PDGM or EGD label was read. Dropped channels are zeroed, never imputed. Condition prediction freezes ran on the CPU with 30 MC-dropout passes.

| Run | Seed | Run id | `conditions_analysis.json` SHA-256 |
|---|---|---|---|
| R2 | 0 | `01M46999FB083AX4WW0067YM13` | `706336e766b6d3cb...` |
| R3 | 1 | `01M4FPECM9DKAR7F6B7VFRQNC5` | `ba41bf4e13554641...` |
| R4 | 2 | `01M60CYFD2AYA8DCPBTDSJS4DM` | `9e8a49938bfbbe11...` |
| R5 | 3 | `01M66E2KR6ZV2YPBTNPF5FD53T` | `f7f560328434473a...` |
| R6 | 4 | `01M776GTZC70FTB1ABD2DDMYHH` | `7a1bea4552deec69...` |

## AUROC by condition

| Condition | R2 | R3 | R4 | R5 | R6 | Mean | SD (n=5 seeds) |
|---|---|---|---|---|---|---|---|
| full | 0.878 | 0.912 | 0.822 | 0.878 | 0.878 | 0.874 | 0.032 |
| drop_t1 | 0.879 | 0.899 | 0.832 | 0.883 | 0.887 | 0.876 | 0.026 |
| drop_t1ce | 0.631 | 0.717 | 0.596 | 0.686 | 0.734 | 0.673 | 0.058 |
| drop_t2 | 0.873 | 0.898 | 0.791 | 0.862 | 0.835 | 0.852 | 0.041 |
| drop_flair | 0.793 | 0.843 | 0.823 | 0.839 | 0.816 | 0.823 | 0.020 |
| t1ce_flair_only | 0.780 | 0.801 | 0.765 | 0.835 | 0.853 | 0.807 | 0.037 |

## Brier (raw probability) by condition

| Condition | R2 | R3 | R4 | R5 | R6 | Mean | SD (n=5 seeds) |
|---|---|---|---|---|---|---|---|
| full | 0.140 | 0.118 | 0.147 | 0.127 | 0.134 | 0.133 | 0.011 |
| drop_t1 | 0.135 | 0.136 | 0.144 | 0.132 | 0.126 | 0.135 | 0.007 |
| drop_t1ce | 0.360 | 0.247 | 0.222 | 0.260 | 0.259 | 0.270 | 0.053 |
| drop_t2 | 0.129 | 0.143 | 0.165 | 0.140 | 0.136 | 0.143 | 0.013 |
| drop_flair | 0.157 | 0.135 | 0.165 | 0.148 | 0.191 | 0.159 | 0.021 |
| t1ce_flair_only | 0.160 | 0.194 | 0.170 | 0.153 | 0.131 | 0.161 | 0.023 |

## ECE (10 bins, raw probability) by condition

| Condition | R2 | R3 | R4 | R5 | R6 | Mean | SD (n=5 seeds) |
|---|---|---|---|---|---|---|---|
| full | 0.119 | 0.106 | 0.040 | 0.106 | 0.119 | 0.098 | 0.033 |
| drop_t1 | 0.115 | 0.129 | 0.051 | 0.098 | 0.083 | 0.095 | 0.030 |
| drop_t1ce | 0.401 | 0.233 | 0.170 | 0.251 | 0.258 | 0.263 | 0.085 |
| drop_t2 | 0.072 | 0.170 | 0.068 | 0.117 | 0.066 | 0.098 | 0.045 |
| drop_flair | 0.104 | 0.092 | 0.146 | 0.059 | 0.185 | 0.117 | 0.049 |
| t1ce_flair_only | 0.076 | 0.218 | 0.064 | 0.115 | 0.049 | 0.105 | 0.068 |

The SD is the spread over five training seeds on the same 124 test patients. It is not a confidence interval for the population and it ignores test-set sampling error.

## Degradation ordering (Phase 08 sanity check)

Phase 08 expects that dropping T1ce hurts more than dropping T1 and that a mis-mapped channel (R-C05) would break that order.

| Run | Worst single drop by AUROC | AUROC full | AUROC drop_t1ce | AUROC drop_t1 | T1ce hurts more than T1 |
|---|---|---|---|---|---|
| R2 | drop_t1ce | 0.878 | 0.631 | 0.879 | yes |
| R3 | drop_t1ce | 0.912 | 0.717 | 0.899 | yes |
| R4 | drop_t1ce | 0.822 | 0.596 | 0.832 | yes |
| R5 | drop_t1ce | 0.878 | 0.686 | 0.883 | yes |
| R6 | drop_t1ce | 0.878 | 0.734 | 0.887 | yes |

## Selective AURC (mean over cutoffs) on the M2 confidence ranking and the M3 MC-dropout entropy ranking

Lower is better. Per-run, internal test, 124 patients.

| Condition | R2 M2 / M3 | R3 M2 / M3 | R4 M2 / M3 | R5 M2 / M3 | R6 M2 / M3 |
|---|---|---|---|---|---|
| full | 0.076 / 0.080 | 0.059 / 0.057 | 0.110 / 0.109 | 0.064 / 0.064 | 0.067 / 0.070 |
| drop_t1 | 0.076 / 0.080 | 0.078 / 0.074 | 0.102 / 0.101 | 0.069 / 0.069 | 0.065 / 0.064 |
| drop_t1ce | 0.493 / 0.473 | 0.349 / 0.346 | 0.419 / 0.420 | 0.346 / 0.352 | 0.333 / 0.339 |
| drop_t2 | 0.073 / 0.075 | 0.092 / 0.091 | 0.138 / 0.134 | 0.069 / 0.070 | 0.084 / 0.082 |
| drop_flair | 0.108 / 0.106 | 0.082 / 0.080 | 0.104 / 0.106 | 0.086 / 0.088 | 0.164 / 0.162 |
| t1ce_flair_only | 0.113 / 0.117 | 0.212 / 0.212 | 0.143 / 0.148 | 0.082 / 0.081 | 0.071 / 0.073 |

## Notes

- Tied confidence scores. The risk-coverage curve has one point per distinct score, so fewer than 124 points means many patients share the same score (possibly saturated probabilities; not checked). Cells below 100 points: R4 full: 77 distinct operating points of 124; R4 drop_t1: 79 distinct operating points of 124; R4 drop_t1ce: 34 distinct operating points of 124; R4 drop_t2: 70 distinct operating points of 124; R4 t1ce_flair_only: 78 distinct operating points of 124. With ties the selective risk at a target coverage is read at the next attainable coverage and the rejected-but-correct rate can be undefined (null in the JSON).

- R4's full-input temperature is 0.815 (below 1); the other runs: R2 1.125, R3 1.271, R5 1.076, R6 1.418.

- All numbers describe the checkpoint chosen by calibration loss on the UTSW calibration split (the D-039 selection effect).
