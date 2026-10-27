# Phase 08, T08.7: naturally missing sequences

Status: written 2026-10-27. Covers acceptance criterion 8 of `phases/PHASE_08_MISSING_MODALITY.md` for UTSW-Glioma and
UCSF-PDGM. EGD is not covered (access not granted). Decision D-012 stays OPEN for that reason.

## Result

No naturally missing sequence exists in either downloaded cohort, so there is no separate natural-missingness analysis
to run and no case to flag. All missing-modality results in this study come from simulated removal (zeroing), as D-008
already states.

| Cohort | Patients checked | Missing one or more of T1, T1ce, T2, FLAIR | Source |
|---|---|---|---|
| UTSW-Glioma, as downloaded | 625 | 0 | `DECISION_LOG.md` D-012, partial finding of T03.9 (2026-09-18) |
| UCSF-PDGM, as downloaded | 501 | 0 | same |
| UTSW-Glioma, retained after QC | 616 | 0 (each of the four volumes loads for 616 of 616) | `manifests/preprocessing_output_audit.json`, `cohorts.utsw.checks` keys `volume.T1.load`, `volume.T1ce.load`, `volume.T2.load`, `volume.FLAIR.load` |
| UCSF-PDGM, retained after QC | 202 | 0 (each of the four volumes loads for 202 of 202) | same keys under `cohorts.ucsf_pdgm.checks` |
| EGD | none yet | not assessed | DUA sent, access not granted (last checked 2026-10-11) |

## What this does and does not show

- The T03.9 count is a sequence-presence check on patients that have an image directory. It did not look at the 6
  UCSF-PDGM patients with metadata and no imaging (D-021; they are excluded in Phase 03), so 501/501 means every
  patient with a directory has all four sequences.
- The post-QC counts come from the Phase 04 output audit, which loads every volume. They show that none of the retained
  patients has a missing or unreadable sequence.
- Policy (a) of D-012 (exclude naturally incomplete cases from the primary analysis and report them as a separate check)
  has nothing to exclude in UTSW or UCSF-PDGM. The tension that D-012 describes does not arise in these two cohorts.
- This is a statement about the inclusion criteria of the cohorts as downloaded. It says nothing about how a model behaves
  when a sequence is genuinely unavailable at a hospital, which the study cannot test (D-008, and the Limitations
  paragraph that D-008 requires).

## Open

- EGD: rerun `scripts/inventory_missing_sequences.py` when the data arrive, before Phase 12 planning. If EGD has
  naturally incomplete cases, D-012 policy (a) applies and this document needs a second table.
- The T03.9 report itself is on the external SSD (`manifests_dir()`), not in the repository. The figures above are the
  ones recorded in D-012 and in the committed audit file.
