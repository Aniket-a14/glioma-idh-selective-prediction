# Phase 07/09 internal results for R1 and R2 (UTSW calibration and internal test only)

Generated 2026-10-09 by `scripts/analyze_internal.py` from the frozen prediction artifacts; every number below is read from
`internal_analysis.json` (SHA-256 sidecar beside each file). Internal data only: 124 calibration patients (35 mutant) and
124 internal-test patients (35 mutant). No UCSF-PDGM or EGD label was read. Temperature, conformal quantile and CRC threshold are
fitted on the calibration split, which also chose the checkpoint (the D-039 selection effect, to be stated beside any coverage result).

- R1: run `01M45268QDQ2CFBSPNH117MF41`, checkpoint `d3c33660fc78a151...`, artifact `addc26482c870061...`, temperature T = 1.352
- R2: run `01M46999FB083AX4WW0067YM13`, checkpoint `1d0c53023fef5615...`, artifact `83f3d99c98557cf1...`, temperature T = 1.125

## Always-predict (M1 raw, M2 temperature-scaled), internal test

| | R1 M1 | R1 M2 | R2 M1 | R2 M2 |
|---|---|---|---|---|
| AUROC | 0.872 | 0.872 | 0.878 | 0.878 |
| AUPRC | 0.743 | 0.743 | 0.778 | 0.778 |
| Brier | 0.171 | 0.169 | 0.140 | 0.139 |
| ECE (10 bins) | 0.186 | 0.191 | 0.119 | 0.122 |
| ECE (5 / 15 bins) | 0.181 / 0.201 | 0.184 / 0.203 | 0.096 / 0.120 | 0.108 / 0.136 |
| Accuracy at 0.5 | 0.742 | 0.742 | 0.782 | 0.782 |
| Sensitivity / specificity | 0.857 / 0.697 | 0.857 / 0.697 | 0.743 / 0.798 | 0.743 / 0.798 |

Temperature scaling leaves the ranking unchanged, so M1, M2 and the M5 score-threshold view share one risk-coverage curve (D-047).

## Selective prediction on the shared confidence ranking (max(p, 1 - p)), internal test

| | R1 | R2 |
|---|---|---|
| AURC (mean over cutoffs) | 0.1343 | 0.0755 |
| AURC (trapezoid) | 0.1332 | 0.0747 |
| Oracle AURC | 0.0376 | 0.0265 |
| Monotonicity violations (pairs) | 706 | 253 |
| Always-predict error (1 - accuracy) | 0.2581 | 0.2177 |

Selective risk at the smallest attainable coverage at or above each target (attained coverage in brackets); rejected-but-correct rate in the last block.

| Target coverage | R1 risk | R2 risk | R1 rejected-but-correct | R2 rejected-but-correct |
|---|---|---|---|---|
| 0.9 | 0.232 (0.903) | 0.170 (0.903) | 0.500 of 12 | 0.333 of 12 |
| 0.8 | 0.200 (0.806) | 0.160 (0.806) | 0.500 of 24 | 0.542 of 24 |
| 0.7 | 0.172 (0.702) | 0.115 (0.702) | 0.541 of 37 | 0.541 of 37 |
| 0.6 | 0.133 (0.605) | 0.093 (0.605) | 0.551 of 49 | 0.592 of 49 |
| 0.5 | 0.129 (0.500) | 0.048 (0.500) | 0.613 of 62 | 0.613 of 62 |

## Split conformal on the temperature-scaled probability (M5 set view), internal test

Score 1 - p(true class), quantile k = ceil((n + 1)(1 - alpha)) of the calibration scores (n = 124); the set abstains unless it is a singleton (D-003).

| Run | alpha | Nominal | Empirical coverage | Abstention rate | Singleton | Empty | Both classes | Singletons holding the true label |
|---|---|---|---|---|---|---|---|---|
| R1 | 0.05 | 0.95 | 0.968 | 0.718 | 35 | 0 | 89 | 0.886 |
| R1 | 0.1 | 0.90 | 0.919 | 0.403 | 74 | 0 | 50 | 0.865 |
| R1 | 0.2 | 0.80 | 0.758 | 0.016 | 122 | 0 | 2 | 0.754 |
| R2 | 0.05 | 0.95 | 0.960 | 0.411 | 73 | 0 | 51 | 0.932 |
| R2 | 0.1 | 0.90 | 0.871 | 0.185 | 101 | 0 | 23 | 0.842 |
| R2 | 0.2 | 0.80 | 0.726 | 0.121 | 109 | 15 | 0 | 0.826 |

The test set has 124 patients, so empirical coverage carries about 3 to 6 points of sampling noise before any calibration-draw noise (`POWER_CHECK.md`); gaps of that size are not evidence for or against C4.

## Conformal risk control (secondary), internal test

Loss 1[confidence >= tau and wrong] (D-045); tau is the smallest threshold whose corrected calibration risk is at most alpha.

| Run | alpha | tau | Accepted (coverage) | P(accepted and wrong) | Risk among accepted |
|---|---|---|---|---|---|
| R1 | 0.05 | 0.846 | 0.282 | 0.032 | 0.114 |
| R1 | 0.1 | 0.701 | 0.589 | 0.081 | 0.137 |
| R1 | 0.2 | 0.513 | 0.984 | 0.242 | 0.246 |
| R2 | 0.05 | 0.778 | 0.589 | 0.040 | 0.068 |
| R2 | 0.1 | 0.666 | 0.806 | 0.129 | 0.160 |
| R2 | 0.2 | 0.504 | 1.000 | 0.218 | 0.218 |
