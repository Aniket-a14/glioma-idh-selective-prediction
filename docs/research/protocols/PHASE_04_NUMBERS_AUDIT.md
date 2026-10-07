# PHASE 04 NUMBERS AUDIT

Independent audit of every numerical claim in sections 2–4 of
`PHASE_04_QC_REPORT.md` and in the **Post-QC counts** section of
`POST_EXCLUSION_CLASS_COUNTS.md`.

Sources were limited to the committed manifests and JSON artifacts named by C-013, plus
read-only entries in `PROJECT_STATE.md`. Arithmetic is shown where a claim is derived. The
criterion numbers, task IDs, decision IDs, and hexadecimal digests are identifiers rather than
numeric claims and are not audited as measurements.

## Audit table

| Report location | Number(s) or claim | Source and derivation | Result |
|---|---|---|---|
| QC report §2, cohort flow | UTSW pre-QC 622; excluded 6; post-QC 616; IDH 173/443 | `cohort_manifest.json`: UTSW retained 622; `cohort_manifest_post_qc.json`: UTSW excluded 9 total, of which 3 are pre-QC label exclusions and 6 are QC exclusions, retained 616; `PROJECT_STATE.md:82`: post-QC IDH 173/443 | **MATCH** — 622 − 6 = 616 |
| QC report §2, cohort flow | UCSF-PDGM pre-QC 202; excluded 0; post-QC 202 | `cohort_manifest.json` and `cohort_manifest_post_qc.json`: UCSF retained 202; `preprocessing_qc_report.json` `cohorts.ucsf_pdgm.exclusions_by_qc_reason`: `{}` | **MATCH** |
| QC report §2, exclusion rates | UTSW 6/622 = 0.96%; UCSF 0/202 = 0%; stop threshold 10% | `preprocessing_qc_report.json`: UTSW `post_decision_exclusion_rate` 0.00964630225080386 and UCSF 0.0; `PROJECT_STATE.md:80` records the 10% stop threshold | **MATCH** — 0.0096463 rounds to 0.96% |
| QC report §2, verification failure count | Automated verification failed for no case in either cohort | `preprocessing_qc_report.json`: `cohorts.utsw.verification_status_counts.failed` = 0 and `cohorts.ucsf_pdgm.verification_status_counts.failed` = 0; `cohorts.utsw.automated_failure_rate` = 0.0 and `cohorts.ucsf_pdgm.automated_failure_rate` = 0.0 | **MATCH** |
| QC report §3 criterion 1 | 6 QC exclusions, each categorized `qc:*` | `cohort_manifest_post_qc.json` UTSW `exclusion_reason_counts`: `qc:skullstrip-over: 6`; `preprocessing_qc_report.json` UTSW `exclusions_by_qc_reason` | **MATCH** |
| QC report §3 criterion 3 | At least 30 stratified cases | `preprocessing_qc_report.json` `reviewed_sample.utsw.by_selection_reason_and_verdict.stratified`: 24 pass; UCSF has 11 `random`, not stratified; `PROJECT_STATE.md:80` records 24 UTSW IDH-stratified and 11 UCSF random | **MISMATCH** — committed evidence identifies 24 stratified UTSW cases, not at least 30 stratified cases |
| QC report §3 criterion 3 | 24 UTSW IDH-stratified cases split 12/12 | `PHASE_04_QC_REPORT.md:36` states 24 UTSW IDH-stratified cases (12/12); `PROJECT_STATE.md:80` records the 24-case stratified sample | **MATCH** |
| QC report §3 criterion 3 | 155 overlays: 134 UTSW and 21 UCSF | `preprocessing_qc_report.json` `automated_vs_human_agreement.joinable_reviewed_case_count`: 155; `reviewed_sample.utsw.total`: 134; `reviewed_sample.ucsf_pdgm.total`: 21 | **MATCH** — 134 + 21 = 155 |
| QC report §3 criterion 3 | 24 UTSW stratified; 11 UCSF random; 68 borderline; 16 brain-fraction tail; 22 shape-tail; 40 residual random | `preprocessing_qc_report.json`: UTSW selection counts 24 stratified, 8 tail, 22 shape-tail, 40 residual-sample; UCSF 11 random; borderline counts 63 UTSW + 5 UCSF = 68; tail counts 8 UTSW + 8 UCSF = 16 | **MATCH** for the listed sample counts |
| QC report §3 criterion 3 | All 68 borderline cases reviewed | Assuming `not-required` applies only to passthrough cases: UTSW reviewed 134 = 128 passed + 6 failed; 559 passthrough − 488 not-required = 71 passthrough reviewed; 134 − 71 = 63 borderline. UCSF: 21 reviewed, 197 passthrough − 181 not-required = 16 passthrough reviewed; 21 − 16 = 5 borderline. `preprocessing_qc_report.json` `cohorts.utsw` and `cohorts.ucsf_pdgm` contain these values and `borderline_count` is 63 and 5. | **MATCH** (derived) — 63 + 5 = 68 |
| QC report §3 criterion 4 | All 6 human failures are individual brain-missing cases | `preprocessing_qc_report.json` UTSW `automated_vs_human_agreement.by_cohort.utsw.human_failures`: 6 entries, all `failure_category: skullstrip-over`; `PROJECT_STATE.md:80` describes all 6 as brain-missing source cases | **MATCH** |
| QC report §3 criterion 5 | 3,272 volumes audited | `preprocessing_output_audit.json`: UTSW `volumes_checked` 2,464 + UCSF `volumes_checked` 808 = 3,272 | **MATCH** |
| QC report §3 criterion 5 | Shape 240×240×155; spacing 1.0 mm; Dice threshold 0.90 | `preprocessing_output_audit.json` `thresholds.expected_shape`: `[240,240,155]`; `expected_spacing_mm`: `[1.0,1.0,1.0]`; `cross_sequence_dice_min`: 0.9 | **MATCH** |
| QC report §3 criterion 5 | 7 volumes, 152 negative voxels, maximum negative fraction 4.4e-5 | `preprocessing_output_audit.json` UTSW `negative_voxel_summary`: `volumes_with_any_negative` 7, `total_negative_voxels` 152, `largest_negative_fraction_nonzero` 0.000043825248112130763 | **MATCH** — rounds to 4.4e-5 |
| QC report §3 criterion 6 | 818 cases; footprint check passes 817/818 | `preprocessing_output_audit.json`: UTSW case count 616 + UCSF case count 202 = 818; `checks.mask_alignment.passed`: 615 + 202 = 817; failed: 1; UTSW minimum footprint fraction 0.9889132985836313 against threshold 0.99 | **MATCH** |
| QC report §3 criterion 7 | 7 volumes recomputed after the N4 fix; 0 after that | `PROJECT_STATE.md:80` records 7 recomputed after the fix and 0 failures on rerun | **MATCH** |
| QC report §3 criterion 8 | 3,281 of 3,288 volumes reused | `PROJECT_STATE.md:80` records 3,281 reused of 3,288 during the real rerun | **MATCH** |
| QC report §4, human failures | 6 failures at brain fractions 0.053, 0.100, 0.108, 0.109, 0.115, 0.129 | `preprocessing_qc_report.json` UTSW `human_failures`: six fractions 0.0525913, 0.1002404, 0.1080006, 0.1088010, 0.1150693, 0.1289130 | **MATCH** — report values are rounded to three decimals |
| QC report §4, original screen | Original lower bound 0.08; 1 of 6 failures flagged | `preprocessing_qc_report.json` `screen_bounds.original_lower_bound`: 0.08; UTSW `human_failures_flagged_at_original_bound`: 1 | **MATCH** |
| QC report §4, recalibration | Bounds 0.11, 0.12, 0.13; three updates; asymmetry ranks 1, 11, 23, 44, 75 of 90 | `preprocessing_qc_report.json` `screen_bounds.current_lower_bound`: 0.13; `PROJECT_STATE.md:82` records the sequence 0.11 → 0.12 → 0.13 and the five listed ranks among 90 | **MATCH** for the recorded values; the prose says “the failures” while listing five ranks for six failures, so that wording should be clarified by the Research Lead |
| QC report §4, final bound | All 6 failures flagged at 0.13; bound is provisional | `preprocessing_qc_report.json`: all six `human_failures.automated_flagged` are true; `screen_bounds.current_lower_bound`: 0.13; `screen_bounds.provisional`: true | **MATCH** |
| QC report §4, residual sample | 40 cases, 0 failures, one-sided 95% upper bound 7.2% | `preprocessing_qc_report.json` `residual_failure_rate.residual_sample`: `n` 40, `failures` 0, `upper_95` 0.0721575245055146 | **MATCH** — rounds to 7.2% |
| QC report §4, combined random sample | 22 earlier draws; 0 of 62; upper bound 4.7% | `preprocessing_qc_report.json` `residual_failure_rate.all_random_above_bound`: `n` 62, `failures` 0, `upper_95` 0.047169511375356854; `PROJECT_STATE.md:82` records the 22 earlier draws | **MATCH** — 4.7% is the rounded upper bound |
| QC report §4, residual coverage | 559 retained cases above 0.13; 71 reviewed; 488 not reviewed | `preprocessing_qc_report.json` UTSW `verification_status_counts.verified-passthrough`: 559 and `visual_qc_counts.not-required`: 488; 71 is derived as 559 − 488, while `PROJECT_STATE.md:82` records 488 not reviewed | **MATCH** — 71 + 488 = 559 |
| Post-QC section, UTSW flow | 622 pre-QC; 6 QC-excluded; 616 post-QC | `cohort_manifest.json`: UTSW retained 622; `cohort_manifest_post_qc.json`: UTSW `qc:skullstrip-over` 6 and retained 616 | **MATCH** — 622 − 6 = 616 |
| Post-QC section, UTSW labels | IDH 173/443; 1p/19q 62/270/284 | `PROJECT_STATE.md:82` records post-QC UTSW IDH 173/443 and 1p/19q 62/270/284 | **MATCH** |
| Post-QC section, UCSF-PDGM flow | 202 pre-QC; 0 QC-excluded; 202 post-QC | `cohort_manifest.json` and `cohort_manifest_post_qc.json`: UCSF retained 202; QC exclusion counts are empty; `preprocessing_output_audit.json` case count is 202 | **MATCH** |
| Post-QC section, UCSF-PDGM labels | IDH 80/122; 1p/19q 13/167/22 | `POST_EXCLUSION_CLASS_COUNTS.md:38` gives the pre-QC IDH and 1p/19q counts; `cohort_manifest_post_qc.json` and `preprocessing_qc_report.json` show no UCSF QC exclusions, so both label splits are unchanged | **MATCH** |
| Post-QC section, exclusion labels | 6 excluded UTSW patients: 3 IDH-mutant, 3 IDH-wildtype; 1 co-deleted, 2 non-co-deleted, 3 unlabeled | IDH: `PROJECT_STATE.md:71` pre-QC 176/446 minus `PROJECT_STATE.md:82` post-QC 173/443 = 3/3 excluded. 1p/19q: `POST_EXCLUSION_CLASS_COUNTS.md` pre-QC 63/272/287 minus post-QC 62/270/284 = 1/2/3 excluded. | **MATCH** (derived) |
| Post-QC section, UTSW percentage | Mutant share 28.3% → 28.1% | Arithmetic from committed counts: 176/622 = 28.2958% → 28.3%, and 173/616 = 28.0844% → 28.1%; the counts are at `PROJECT_STATE.md:71` and `PROJECT_STATE.md:82` | **MATCH** |
| Post-QC section, roster digests | UTSW digest and unchanged UCSF digest | `cohort_manifest_post_qc.json` `cohorts.utsw.roster_sha256` and `cohorts.ucsf_pdgm.roster_sha256`; UCSF value equals `cohort_manifest.json` | **MATCH** |

## Findings to flag in the PR

1. The Phase 04 acceptance table says “at least 30 stratified cases,” but the committed review
   breakdown records 24 UTSW stratified cases and 11 UCSF random cases. This audit does not edit
   the acceptance report; the Research Lead should decide whether the criterion wording or the
   underlying record needs correction.
2. The report says all 68 borderline cases were reviewed. The committed counts support this as a
   derived result if `not-required` applies only to passthrough cases: 63 UTSW borderline cases
   plus 5 UCSF borderline cases equals 68.
3. The report lists five asymmetry ranks for six human failures. The source progress log repeats
   those five ranks, but the relationship between the six failures and five ranks is unclear.
4. The six excluded patients’ label breakdown and the UCSF post-QC 1p/19q split are derived from
   the permitted pre-QC and post-QC class counts; both are marked **MATCH** above.
