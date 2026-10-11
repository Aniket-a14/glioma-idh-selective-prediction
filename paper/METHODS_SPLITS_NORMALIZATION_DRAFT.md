# Data splitting and intensity normalization

The development cohort was the 616-patient post-QC UTSW-Glioma cohort. We split at the
patient level, so volumes from one patient could not appear in more than one split, and
stratified only on IDH status. Decision D-034 froze a 60/20/20 train/calibration/internal-test
design before the split was run. The seed is fixed in the split configuration before inspecting
the result; it is not changed to improve the class balance or any later result. Per-class
rounding places 35 IDH-mutant and 89 IDH-wildtype patients in both the calibration and internal
test splits. The remainder is 103 mutant and 265 wildtype patients in training, giving 368,
124, and 124 patients in train, calibration, and internal test, respectively. The 1p/19q
categories are reported for each split but are not used for stratification. UCSF-PDGM and EGD
are evaluated as whole cohorts and are never split.

D-034 records the Research Lead's choice of 60/20/20 after a power check compared four candidate
allocations. Its simulation table uses the rounded 60/20/20 sizes of 370 training, 123 calibration,
and 123 test patients, with 35 mutant patients in the test set. At this simulated test size, the
bootstrap 95% AUROC half-width ranges from 0.094 at true AUROC 0.75 to 0.059 at 0.90; the
corresponding Hanley--McNeil values are wider. For the coverage-deviation calculation under
exchangeability (alpha = 0.10, combining calibration-draw noise with an external test set of 202--450
patients), no feasible calibration size on 616 patients brings the 95% half-width below five
percentage points, while the five-point coverage grid from 0.5 to 0.9 remains usable.

Normalization is fitted on the UTSW training split only. Each volume is first divided by its own
positive brain-voxel median. This rescaling is necessary because raw scanner intensity scales
differ substantially between patients: in the training dry run, T1 per-patient mean brain
intensity ranged from 123 to 271,321, compared with a median of about 565, and 25 patients (7%)
had at least one modality above 5,000. D-036 therefore adopted the patient-specific median
rescale before calculating shared statistics. After rescaling, the pipeline pools non-zero brain
voxels from the 368 UTSW training patients and computes a per-modality mean and population
standard deviation (ddof = 0). The statistics are accumulated in float64, in sorted patient
order, and then applied unchanged to every split and cohort. Normalization is applied to brain
voxels only; background remains exactly zero, and no values are clipped. The per-patient step
uses no other patient's data, so external-cohort statistics are not needed.

The UTSW range check found no sign of an intensity shift between the held-out UTSW splits and
training: median z-score means were near zero and median standard deviations were approximately
0.86–0.96. Eight of 124 calibration patients and seven of 124 internal-test patients were flagged
by the training min--max review rule, a rate described as compatible with the expected multiple
comparisons from 12 quantities per patient; the flags do not alter downstream processing. No
non-finite values were found. The split manifest and normalization-statistics artifact are both
hash-pinned and written once, so changing either requires an explicit decision and invalidates
downstream results.

## Claims and provenance

| Claim | Value | Source file and line or section |
|---|---|---|
| Development cohort | 616 post-QC UTSW patients | `docs/research/DECISION_LOG.md:921`; `docs/research/protocols/POWER_CHECK.md:10-12` |
| Split proportions and unit | 60/20/20; patient-level; stratified on IDH | `docs/research/DECISION_LOG.md:914-921`; `docs/research/protocols/STATISTICAL_ANALYSIS_PLAN.md:8-16` |
| Split seed | Fixed before the split and not changed after inspection | `docs/research/DECISION_LOG.md:921` |
| Exact class counts | Train 103 mutant / 265 wildtype; calibration 35 / 89; internal test 35 / 89 | `docs/research/DECISION_LOG.md:921`; totals 173/443 in `docs/research/protocols/POWER_CHECK.md:10-12`; arithmetic shown in text |
| Split sizes | Train 368; calibration 124; internal test 124 | `docs/research/protocols/PHASE_04_ZSCORE_CHECK.md:9-12,35-42` |
| 1p/19q handling | Reported, not used for stratification | `docs/research/DECISION_LOG.md:921` |
| External cohorts | UCSF-PDGM and EGD are never split | `docs/research/DECISION_LOG.md:921`; `docs/research/protocols/STATISTICAL_ANALYSIS_PLAN.md:10-16` |
| Power-check allocation | Simulated 60/20/20 sizes 370/123/123; test mutants 35 | `docs/research/protocols/POWER_CHECK.md:21-29` |
| Power-check precision | Bootstrap AUROC half-width 0.094 to 0.059 for true AUROC 0.75 to 0.90; Hanley--McNeil is wider | `docs/research/protocols/POWER_CHECK.md:30-40` |
| Coverage-grid and calibration conclusion | Five points, 0.5–0.9, usable; no feasible calibration size gives a half-width below 5 percentage points | `docs/research/protocols/POWER_CHECK.md:82-90` |
| Rescale statistic | Each volume divided by its own positive brain-voxel median | `docs/research/DECISION_LOG.md:980-992` |
| Why rescaling was needed | T1 mean range 123–271,321; median about 565; 25 patients (7%) above 5,000; 11 extreme in all four modalities | `docs/research/DECISION_LOG.md:980-985` |
| Frozen pooled statistic | Per-modality pooled brain-voxel mean and population SD, ddof 0, from 368 UTSW-training patients | `docs/research/DECISION_LOG.md:973-978`; `docs/research/protocols/PHASE_04_ZSCORE_CHECK.md:9-19` |
| Application and clipping | Brain voxels only; background 0; no clipping; applied unchanged to every cohort and split | `docs/research/DECISION_LOG.md:973-978`; `docs/research/protocols/PHASE_04_ZSCORE_CHECK.md:9-12` |
| UTSW range check | Median z means near 0; median SD 0.86–0.96; 8 calibration and 7 internal-test flags; no non-finite values | `docs/research/protocols/PHASE_04_ZSCORE_CHECK.md:31-42,48-56` |
| Split artifact | SHA-256 `b8696d4474ce0328eb3ffd53bfb3727f85b1977ed22d0a78212111e800ec9a87` for `splits.json` | `docs/research/manifests/splits.sha256:1` |
| Normalization artifact | SHA-256 `f6b7cc70d6ca2b23fc9e706d1ee78b30cbb1d0e845fc63ee894e3894dc36bbb9` for `normalization_stats.json` | `docs/research/manifests/normalization_stats.sha256:1`; `docs/research/protocols/PHASE_04_ZSCORE_CHECK.md:21-23` |

## Open questions

None for this subsection. The exact split manifest and normalization-statistics file are the
frozen records of the realized allocation and fitted values.
