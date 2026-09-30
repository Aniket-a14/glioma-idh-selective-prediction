# Phase 04 normalization and z-score range check (T04.6, T04.8)

Run 2026-09-30. Report only: no patient is excluded, no value is clipped (D-036). Aggregates only, no patient identifiers.
The per-patient rows are on the SSD in `data/manifests/normalization_zscore_check.json`. No UCSF-PDGM or EGD label was read;
the check uses images and the preprocessing index only.

## Frozen statistics (T04.6)

Fitted on the 368 UTSW patients of the frozen training split (`splits.json` SHA-256 `b8696d44…9a87`, roster digest
`9b140f4dc882adf8…`). Each volume is first divided by its own brain-voxel median, because raw intensity units differ by up to
several hundred times between patients (D-036 amendment). Then pooled brain-voxel mean and population SD of the rescaled
voxels, applied unchanged to every cohort and split, brain voxels only, background stays 0.

| Modality | Mean | SD | Brain voxels |
|---|---|---|---|
| T1 | 0.9569157 | 0.2028983 | 517,331,708 |
| T1ce | 0.9761187 | 0.2098552 | 517,306,554 |
| T2 | 1.1183774 | 0.4431464 | 517,323,643 |
| FLAIR | 0.9711155 | 0.2564007 | 517,324,362 |

File: `data/manifests/normalization_stats.json`, SHA-256
`f6b7cc70d6ca2b23fc9e706d1ee78b30cbb1d0e845fc63ee894e3894dc36bbb9` (copy in `docs/research/manifests/normalization_stats.sha256`;
checked with `shasum -a 256`; a second fit reproduced the same numbers). Written once; the fitting script refuses to overwrite it.

## Z-score range check (T04.8)

Median over patients of each patient's brain-voxel z-scores.

| Group (patients) | Modality | Median mean | Median SD | Median p99.9 | Flagged mean / SD / p99.9 |
|---|---|---|---|---|---|
| UTSW train (368) | FLAIR | 0.002 | 0.953 | 3.06 | 0 / 0 / 0 |
| | T1 | 0.004 | 0.874 | 1.78 | 0 / 0 / 0 |
| | T1ce | 0.001 | 0.871 | 4.96 | 0 / 0 / 0 |
| | T2 | -0.025 | 0.896 | 4.00 | 0 / 0 / 0 |
| UTSW calibration (124) | FLAIR | -0.015 | 0.964 | 3.02 | 1 / 0 / 1 |
| | T1 | -0.011 | 0.911 | 1.63 | 1 / 0 / 2 |
| | T1ce | -0.002 | 0.856 | 5.03 | 2 / 0 / 0 |
| | T2 | 0.023 | 0.932 | 4.29 | 2 / 0 / 3 |
| UTSW internal test (124) | FLAIR | -0.024 | 0.955 | 3.14 | 1 / 0 / 1 |
| | T1 | -0.009 | 0.930 | 1.88 | 0 / 0 / 2 |
| | T1ce | -0.019 | 0.911 | 4.73 | 2 / 0 / 1 |
| | T2 | -0.027 | 0.882 | 3.75 | 1 / 1 / 0 |
| UCSF-PDGM (202) | FLAIR | 0.011 | 1.311 | 4.04 | 0 / 1 / 0 |
| | T1 | 0.059 | 1.314 | 2.61 | 1 / 0 / 0 |
| | T1ce | 0.139 | 1.455 | 11.19 | 4 / 2 / 3 |
| | T2 | 0.122 | 1.334 | 6.73 | 1 / 1 / 3 |

A flag means a patient's per-modality z mean, SD or 99.9th percentile lies outside the min-max range of the 368 UTSW-train
patients. Patients with at least one flag: train 0, calibration 8, internal test 7, UCSF-PDGM 9. No non-finite values.
EGD is not downloaded (D-018) and is skipped.

## Reading it

- UTSW held-out splits behave like the training split: median z mean near 0, median SD 0.86 to 0.96. Seven to eight of 124
  patients flagged is about what a min-max range built from 368 patients gives for new data from the same population (about 2 in
  369 per quantity, 12 quantities per patient), so no sign of shift inside UTSW.
- UCSF-PDGM does differ after identical normalization: median SD 1.31 to 1.46 against 0.87 to 0.96, and T1ce and T2 means
  shifted by about +0.13. This is a label-free sign of cohort-level intensity shift, consistent with the project's premise. It
  is not a reason to exclude or re-normalize anything, and no UCSF-PDGM statistic was used to fit anything.
- Flags are for review only. They do not change any downstream step.
