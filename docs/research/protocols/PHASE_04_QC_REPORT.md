# PHASE 04 — QC REPORT AND ACCEPTANCE STATUS

Written 2026-09-19 for the Research Lead's T04.9 sign-off and the Gate D review. Every number below comes
from a committed aggregate file (`docs/research/manifests/preprocessing_qc_report.json`,
`preprocessing_output_audit.json`, `cohort_manifest_post_qc.json`) or from a run recorded in `PROJECT_STATE.md`.
No patient identifiers appear here; per-case files stay on the SSD.

## 1. What is done and what is not

Everything in Phase 04 that does not depend on the Phase 05 split is done. Two items are **deliberately open** (D-023):

- **T04.6** normalization statistics from UTSW-train only, and the **T04.8 z-score range check** that follows it. Both
  need the frozen Phase 05 split (Research-Lead-gated).
- **EGD preprocessing.** EGD is not downloaded (DUA pending, D-018); the stages are built and tested but have not run on it.

So Gate D cannot close yet, and the phase exit criteria ("normalization statistics frozen and hashed") are not met.
Phase 05's input from this phase (post-QC counts and manifests) is ready.

## 2. Cohort flow

| Cohort | Pre-QC retained (Phase 03) | Excluded in Phase 04 | Post-QC, preprocessed | Roster digest (post-QC) |
|---|---|---|---|---|
| UTSW-Glioma | 622 | 6, all `qc:skullstrip-over` | **616** (173 IDH-mutant / 443 wildtype) | `ee550584d4276d701204b864dd8b7817f65b24f9ba1f63110e5343b32023561d` |
| UCSF-PDGM | 202 | 0 | **202** | `19d5a89e15d2bd62b75c69cdbac08c975d0405d28cc090e7aafe763f9d46bfe5` (unchanged) |

QC exclusion rate: UTSW 6/622 = 0.96%, UCSF-PDGM 0/202 = 0%; the phase stop threshold is 10% per cohort. Automated
verification failed no case in either cohort. The Phase 03 manifests are untouched (D-030); the pre-QC to post-QC
drop stays auditable.

## 3. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | All included patients preprocessed or excluded with a categorized `qc:*` reason | Met (UTSW, UCSF-PDGM) | outputs-index roster digest equals the post-QC roster digest for both cohorts (audit `roster_digest_match: true`); 6 exclusions carry `qc:skullstrip-over`. EGD pending (D-018). |
| 2 | Normalization statistics from UTSW-train alone, hashed, provenance test | **Open (D-023)** | Follows the Phase 05 split freeze (T04.6). |
| 3 | Visual QC on at least 30 stratified cases plus every borderline case; overlays archived | Met, pending your sign-off | 155 overlays reviewed (134 UTSW, 21 UCSF): 24 UTSW IDH-stratified (12/12), 11 UCSF random, all 68 borderline cases, 16 brain-fraction tail, 22 shape-tail, 40 residual random. No case is left pending. Overlays and the review sheet are on the SSD (`artifacts/figures/qc/`). |
| 4 | QC failure rate recorded per cohort; systematic failures corrected, not excluded | Met | Section 2. All 6 failures are individual cases with brain missing in the already-stripped source, which no parameter can repair (HD-BET is a no-op on stripped data), so they are excluded, not re-run. No systematic failure was found. |
| 5 | All volumes RAS at target spacing and consistent shape, asserted automatically | Met | Asserted per volume when written (`pipeline.py`) and re-audited on all 3,272 volumes: RAS, float32, 240x240x155, 1.0 mm, finite, identical affine across a case's four volumes, non-zero footprints agree (Dice at least 0.90). 7 volumes carry 152 isolated negative voxels in total (at most 4.4e-5 of non-zero voxels), kept as they are (D-029). |
| 6 | Masks aligned with volumes | Met, one documented exception | Mask and T1ce grids are identical (shape and affine) for all 818 cases. The supplementary footprint check passes 817 of 818 cases; the exception is a boundary effect (D-032). |
| 7 | Pipeline resumable | Met | Interrupt/restart test; real reruns recomputed only what changed (7 volumes after the N4 fix, 0 after that). |
| 8 | Content-addressed cache verified | Met | Cache tests (identical parameters reuse, changed parameters recompute, corrupt or missing entries recompute); real reruns reused 3,281 of 3,288 volumes, then all of them. |
| 9 | Post-QC counts recorded and fed to Phase 05 | Met | Section 2; `protocols/POST_EXCLUSION_CLASS_COUNTS.md`. |

Failure conditions checked: no cohort above 10%; no modality mislabelling found; the Phase 05 power threshold is a
Phase 05 T05.1 question, not decided here.

## 4. Automated QC against human judgement, and the recalibration

The phase file requires the automated thresholds to be recalibrated if the human catches failures the screen misses.
It did. Measured on the reviewed sample (counts, not sensitivity estimates, because the sample was drawn on the tails):

- Human failures: 6, all UTSW, at brain fractions 0.053, 0.100, 0.108, 0.109, 0.115, 0.129.
- The original screen (borderline lower bound 0.08) flagged 1 of the 6.
- The lower bound was raised to 0.11, then 0.12, then 0.13 (D-031 and its three updates), each time after new failures
  appeared just above the previous bound, and a left-right asymmetry screen was tried and rejected (the failures rank
  1, 11, 23, 44 and 75 of 90 reviewed cases by asymmetry). All 6 failures are flagged at 0.13, but that is in-sample by
  construction.
- The bound is provisional. It was fitted to these failures and is not a validated operating point.

**Residual risk above the final bound (0.13).** 40 UTSW cases were drawn at random (seeded) from unflagged cases above
0.13 and reviewed: 0 failures, exact one-sided 95% upper bound 7.2% for the failure rate above the bound. Adding the
22 earlier IDH-stratified random draws that lie above 0.13 (also 0 failures) gives 0 of 62, upper bound 4.7%.
Of the 559 retained UTSW cases above 0.13, 71 were reviewed and 488 were not.

## 5. Text for the manuscript Limitations

> Visual quality control of the skull-stripped UTSW-Glioma volumes found 6 of 622 patients (0.96%) with part of the brain
> missing; these were excluded. The automated brain-volume screen missed 5 of these 6 at its original threshold and was
> recalibrated on them, so its agreement with the reviewer is in-sample. A random sample of 40 unflagged cases above the
> final threshold contained no failure (95% upper bound 7.2% for the residual rate); unreviewed cases above the
> threshold may still contain a few affected volumes. No such failure was found in UCSF-PDGM (0 of 202; 21 reviewed).

## 6. Sign-off

T04.9 requires the Research Lead's explicit sign-off; the reviewer was the Research Lead alone, so visual QC is the
solo fallback and R-M02 applies (no second reader). The Research Lead signed off in chat on 2026-09-19 when asked
whether they sign off on this report; Claude transcribed it here.

| Item | Research Lead |
|---|---|
| Visual QC completed as described in section 3, row 3 | Signed off |
| Recalibration and residual-risk handling (section 4) accepted | Signed off |
| D-029 to D-032 confirmed | Signed off |
| Date | 2026-09-19 |

Sign-off covers T04.9 and the work in this report only. Gate D and the phase exit remain open until T04.6 (see section 1).
