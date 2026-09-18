# DATA ACCESS LOG

Per-cohort acquisition record, `DATA_GOVERNANCE_PROTOCOL.md` §2. One section per cohort. Fields
left `TBD` need Research Lead confirmation before Gate D — this file is a living record, not
written once and frozen (except the frozen split manifests it eventually feeds).

**Label counts per marker are deliberately not filled in below.** `DATA_GOVERNANCE_PROTOCOL.md` §2
lists them as an acquisition-record field, but `PHASE_02_DATASET_ACQUISITION.md`'s own scope is
explicit: "No label counting or label-file parsing happens here — that is Phase 03, deliberately
separated so that acquisition and verification are distinct auditable steps." This field is
populated once Phase 03 does that work, not invented here to fill the row.

---

## UTSW-Glioma

| Field | Value |
|---|---|
| Source dataset version | TCIA collection, DOI [10.7937/DFAE-1B86](https://doi.org/10.7937/dfae-1b86) |
| Download date | 2026-09-11 (from file modification timestamps on disk — **not independently confirmed by the operator**; TBD if a different date should be recorded) |
| Download method | TBD — not recorded at acquisition time. Needs Research Lead confirmation (NBIA Data Retriever vs. manual TCIA browser download) |
| Source checksum | None published by TCIA for a manual download (no NBIA manifest checksum captured at download time). Baseline SHA-256 per file computed post-hoc by T02.6's integrity verification (`scripts/verify_download_integrity.py`), not a comparison against a known-good external hash |
| Raw-file inventory | 625 patient directories (`BTxxxx`), **6,349 files, all 6,349 valid gzip + valid NIfTI header** (T02.6 real run, 2026-09-18). Per-patient: `brain_t1`, `brain_t1ce`, `brain_t2`, `brain_flair` (core four) + ANTs-registered variants + segmentations (`tumorseg_FeTS`, `tumorseg_manual_correction`, `rtumorseg_manual_correction`) |
| Patient count | 625 directories on disk, matching TCIA's published "625 subjects, 6,349 studies" and the SPEC's claimed 625 — **provisional per D-009 until Phase 03's hashed manifest**, recorded here only as "matches," not as verified |
| Label counts per marker | Not populated here — Phase 03 (see note above) |
| Modality counts | Core four sequences present per patient per T02.6/T02.8's findings — exact per-patient completeness in the T02.6 report (`data/manifests/download_integrity_report.json`, external SSD, not committed) |
| Ambiguous labels | N/A this phase (Phase 03) |
| Naturally missing sequences | None detected at the file-presence level by T02.6 (per-patient breakdown in its report); a definitive per-sequence completeness check is Phase 03/04's job, not this file-existence pass |
| Corrupt volumes | **Zero** — T02.6's full real-data run found zero gzip/NIfTI-header validation failures across all 6,349 files |
| Duplicate scans | Not assessed this phase |
| Licence / DUA terms | **CC BY 4.0** (Creative Commons Attribution 4.0 International), confirmed via [TCIA's UTSW-Glioma collection page](https://www.cancerimagingarchive.net/collection/utsw-glioma/). No DUA. Redistribution and derivative works permitted with attribution. **Transfer to the GPU server is permitted** — no restriction in the licence terms. Citation/DOI attribution required per TCIA's Data Usage Policy. |
| Who downloaded it | TBD — not recorded. Needs Research Lead confirmation of who ran the download in the earlier session |

## UCSF-PDGM

| Field | Value |
|---|---|
| Source dataset version | TCIA collection, [UCSF-PDGM v5](https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=119705830) |
| Download date | 2026-09-11 (file modification timestamps — same caveat as UTSW-Glioma above) |
| Download method | TBD — same caveat as UTSW-Glioma |
| Source checksum | None published for a manual download; baseline SHA-256 computed post-hoc, see T02.6's report |
| Raw-file inventory | 501 patient directories (`UCSF-PDGM-NNNN_nifti`), **12,030 files** (T02.6 real run, 2026-09-18): **11,529 valid NIfTI files + 501 non-NIfTI sidecars** (the `_DTI_eddy.eddy_rotated_bvecs` text file, one per patient — correctly not NIfTI, not a failure). Per-patient: core four (`_T1`, `_T1c`, `_T2`, `_FLAIR`, + `_bias` variants) plus `_ADC`, `_ASL`, `_DTI_eddy*`, `_DWI`, `_SWI`, and three segmentation volumes |
| Patient count | 501 directories on disk, matching TCIA's stated cohort size and the SPEC's claimed 501 — same D-009 provisional caveat as above |
| Label counts per marker | Not populated here — Phase 03 |
| Modality counts | Core four present per patient, plus additional modalities beyond the SPEC's scope (recorded, not used) — see T02.6/T02.8 |
| Ambiguous labels | N/A this phase |
| Naturally missing sequences | None detected at the file-presence level; definitive check is Phase 03/04 |
| Corrupt volumes | **Zero** — all 11,529 NIfTI files passed gzip/header validation; the 501 sidecars are non-NIfTI by design, not failures |
| Duplicate scans | Not assessed this phase |
| Licence / DUA terms | **CC BY 4.0**, confirmed via the TCIA wiki page above. No DUA. **Transfer to the GPU server is permitted.** Attribution required — see the wiki page's specified citations |
| Who downloaded it | TBD |

### T02.5 — UCSF-PDGM ⇄ BraTS-2021 ID-mapping file

**Obtained.** `UCSF-PDGM-metadata_v2.csv`, downloaded 2026-09-18 from the official TCIA wiki
attachment (`https://wiki.cancerimagingarchive.net/download/attachments/119705830/UCSF-PDGM-metadata_v2.csv`),
per the wiki page's own description: "a mapping to the 2021 BraTS data to prevent any data leak
when both datasets are used... confirmed by BraTS Challenge organizers." Placed at
`paths.external_data_dir() / "UCSF-PDGM-metadata_v2.csv"` (external-validation firewall, same as
the imaging data — see `EXTERNAL_VALIDATION_PROTOCOL.md`).

SHA-256: `c83b2783ce78d513ba96efa1d90a7e27fe045553ca8e1e57361406c1f1ba1df6`
502 lines (501 patients + header), matching the on-disk patient count.

**This file also contains UCSF-PDGM's clinical labels** (IDH, MGMT, 1p/19q, survival) — the
external test cohort's ground truth, not just the BraTS mapping column. It has **not been parsed
or read for label content** as part of this phase; only downloaded, placed, and hashed. It sits
behind the same `data/external/` firewall as the imaging data — `GLIOMA_EXTERNAL_EVAL_AUTHORIZED`
still gates any code path that would read it before Gate E, same as everything else in
`data/external/`.

## EGD

| Field | Value |
|---|---|
| T02.1 — DUA submission | **NOT YET SUBMITTED.** This is Phase 02's "DAY-1 ACTION" and the single most time-critical item in the phase — it has a 4–8 week external latency (R-H01) that nothing else in the project can compress. Requires institutional details and Research Lead signature; not something an agent can submit on the Research Lead's behalf. Contact: `servicedesk@health-ri.nl` |
| T02.2 — weekly status check | N/A until T02.1 is submitted |
| Download / inventory / licence | N/A until the DUA is granted |

---

## Storage cross-reference (D-014)

Both cohorts are reachable via `utils/paths.py`'s canonical accessors as of 2026-09-18:
`paths.raw_data_dir() / "utsw"` and `paths.external_data_dir() / "ucsf_pdgm"` — both are symlinks
into the pre-existing downloads (no data copied or moved), added specifically so Phase 02's
tooling (T02.6, T02.8) doesn't need to know about the two-drive layout at all.
