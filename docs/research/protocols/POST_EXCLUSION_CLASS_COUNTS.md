# POST-EXCLUSION CLASS COUNTS

Phase 03 acceptance criterion 10: *"Post-exclusion class counts recorded for IDH and 1p/19q —
input to the Phase 05 power check."* This is distinct from `SPEC_VS_VERIFIED_COUNTS.md` (T03.3,
D-009), which verifies the SPEC's *pre-exclusion* claims against the raw files. This document
answers a different question: after T03.10's exclusions actually apply, what does the retained
cohort's label distribution look like — the real input to Phase 05's power calculation, not the
full downloaded cohort's.

Computed directly from `src/glioma_selective/leakage/exclusions.py`'s already-merged, already-tested
`build_real_exclusion_manifest()` (T03.10) cross-referenced against the same real metadata files
`SPEC_VS_VERIFIED_COUNTS.md` used, filtering out every excluded patient before counting. The IDH
variant → binary bucketing uses `LABEL_DEFINITIONS.md` §4's already-settled harmonization mapping
(UCSF-PDGM's specific mutant variants and `mutated (NOS)` all fold into `IDH_MUTANT`; UCSF-PDGM's
`relative co-deletion` folds into `1P19Q_CODELETED` per D-019) — no new classification judgment is
made here.

---

## UTSW-Glioma — 622 retained (625 − 3 `label:idh_unavailable`)

| Marker | Retained count | Breakdown |
|---|---|---|
| IDH | 622 | `IDH_MUTANT` 176 / `IDH_WILDTYPE` 446 |
| 1p/19q | 622 | `1P19Q_CODELETED` 63 / `1P19Q_NONCODELETED` 272 / `1P19Q_UNLABELED` 287 |

IDH counts are unchanged from the pre-exclusion 625-patient total (176/446) because the only three
excluded UTSW patients are precisely the three with no IDH result — excluding them removes zero
labeled patients from either IDH class. The 1p/19q `UNLABELED` count drops from 290 (pre-exclusion)
to 287: exactly 3 fewer, confirming (not assumed) that all three excluded patients also happened to
lack 1p/19q testing.

## UCSF-PDGM — 202 retained (501 − 6 `no_imaging_available` − 293 `overlap:brats2021`)

| Marker | Retained count | Breakdown |
|---|---|---|
| IDH | 202 | `IDH_MUTANT` 80 / `IDH_WILDTYPE` 122 |
| 1p/19q | 202 | `1P19Q_CODELETED` 13 / `1P19Q_NONCODELETED` 167 / `1P19Q_UNLABELED` 22 |

`IDH_MUTANT` (80) = `mutated (NOS)` 24 + `IDH1 p.R132H` 43 + `IDH1 p.R132G` 4 + `IDH1 p.R132C` 5 +
`IDH1 p.R132S` 1 + `IDH2 p.R172K` 1 + `IDH2 p.Arg172Trp` 1 + `IDH1 p.Arg132His` 1. `1P19Q_CODELETED`
(13) = `co-deletion` 6 + `Co-deletion` 3 + `relative co-deletion` 4 (per D-019's settled fold-in).
Unlike UTSW, the BraTS-overlap exclusion is large (293 of 299 total UCSF-PDGM exclusions) and was
not selected on IDH status, so this retained distribution genuinely differs in *proportion* from
the pre-exclusion 501-patient cohort (pre-exclusion mutant rate ~21%; retained ~40%) — this is
expected and correct, not a red flag: BraTS-2021's training pool skews toward one participating
institution's referral mix, not a random subsample of UCSF-PDGM.

---

## Post-QC counts (Phase 04 T04.12, D-030, D-031)

The tables above are the **pre-QC** record and stay unchanged (they match the frozen
`docs/research/manifests/cohort_manifest.json`). Phase 04's visual QC excluded 6 UTSW patients
(all `qc:skullstrip-over`, part of the brain missing; D-024, D-028, D-031) and 0 UCSF-PDGM patients. The post-QC roster is
`docs/research/manifests/cohort_manifest_post_qc.json`, built by `scripts/build_post_qc_manifests.py` from the
Phase 03 exclusion manifest plus the QC decisions in `preprocessing_status.json`.

| Cohort | Retained pre-QC | QC-excluded | Retained post-QC | IDH (post-QC) | 1p/19q (post-QC, exploratory) |
|---|---|---|---|---|---|
| UTSW-Glioma | 622 | 6 | **616** | `IDH_MUTANT` 173 / `IDH_WILDTYPE` 443 | `1P19Q_CODELETED` 62 / `1P19Q_NONCODELETED` 270 / `1P19Q_UNLABELED` 284 |
| UCSF-PDGM | 202 | 0 | **202** | unchanged (80 / 122) | unchanged (13 / 167 / 22) |

The 6 excluded UTSW patients were 3 IDH-mutant and 3 IDH-wildtype (1 co-deleted, 2 non-co-deleted, 3 unlabeled for
1p/19q), so the mutant share moves from 28.3% to 28.1%. The UTSW post-QC roster digest is
`ee550584d4276d701204b864dd8b7817f65b24f9ba1f63110e5343b32023561d`; the UCSF-PDGM digest is identical to the
Phase 03 one. The counts were checked independently of the builder (own SHA-256 over the sorted canonical IDs, and
the QC-excluded set compared with the failed visual-QC verdicts). UCSF-PDGM labels were not read for this step.

---

## Note for Phase 05

These are the two external-facing counts (UCSF-PDGM) and the internal development-cohort counts
(UTSW) that exist *after* every Phase 03 exclusion. EGD is not included — its DUA is pending
(D-018) — so this document covers UTSW and UCSF-PDGM only; it will need a UTSW-unaffected, EGD-added
update once EGD's own leakage audit completes. No count here may be hard-coded into Phase 05's
config or code — Phase 05 should recompute from the post-QC exclusion manifest (`build_post_qc_manifests.py`) and the real
metadata files directly, the same way this document was produced, not copy these numbers as
constants.
