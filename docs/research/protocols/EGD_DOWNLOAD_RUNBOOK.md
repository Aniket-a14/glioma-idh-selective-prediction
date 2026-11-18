# EGD download runbook (Research Lead performs the download)

Written 2026-11-17. **Deferred 2026-11-18** (D-057: EGD is a later, separately frozen evaluation; the first external run is UCSF-PDGM alone). Use this when the download starts. EGD is governed by the DUA/licence you signed (`DATA_ACCESS_LOG.md`, EGD section). An agent does not
download it: access is tied to your account and the terms name you as custodian. This file lists what to do before, during
and after the download so nothing breaks the terms or the pre-registration. Read `DATA_GOVERNANCE_PROTOCOL.md` first.

## Before you download

1. **Record the grant.** In `DATA_ACCESS_LOG.md` (EGD row, T02.1) write the date Health-RI confirmed access and that the
   XNAT account works. The row says "granted" only on that confirmation. (The last entry is 2026-10-05, "not yet granted".)
2. **Answer the two open licence questions** if not done: must each teammate who touches the imaging sign; may
   per-patient model outputs be published or only aggregates. Our terms say aggregates only. Write the answer in the log.
3. **Read the retention clause.** The request states retention of three months, then all copies deleted. Decide what the
   three months run from (download date or grant date) with Health-RI in writing. This sets a hard deadline for Gate E and
   Phase 12 once the data is on disk. D-057 covers the timing choice.
4. **Disk.** External cohorts live on `Research_1` (`data/external` links to it; UCSF-PDGM is there), which had about
   95 GB free on 2026-11-17 (`Research_2`, the artifact SSD, has about 60 GB). The EGD size is not in our docs; check the
   XNAT project size before starting.

## During the download

- Destination: `paths.external_data_dir() / "egd"`, which resolves to `/Volumes/Research_1/egd` (next to `ucsf_pdgm`).
  Never to the home server, a cloud drive, or the Mac's internal disk (`T02.7`: DUA data must not touch a second machine
  casually).
- Keep the download session's tool log (file counts, errors). Do not open images or metadata for labels beyond what the
  XNAT export requires.
- Make the folder read-only after the integrity step.

## After the download (in this order)

| Step | What | Who | Notes |
|---|---|---|---|
| 1 | Integrity: `scripts/verify_download_integrity.py` (checksums, counts, per-patient sequence inventory) | Codex adds the EGD root (the script only knows `utsw` and `ucsf_pdgm` today), then run on the Mac | CPU, reads files only |
| 2 | Fill the EGD adapter: `src/glioma_selective/data/adapters/egd.py` currently refuses to identify sequences until the real filename convention is known | Codex, after you share the file listing (names only) | Do not guess the T1/T1ce/T2/FLAIR mapping (R-C05) |
| 3 | Naturally-missing check: `scripts/inventory_missing_sequences.py` for EGD (T08.7, D-012 policy (a)) | Codex adds EGD if the script lacks it (no `egd` reference in it today), Claude reads the result | The T08.7 note says to rerun when EGD arrives; needs step 2 first |
| 4 | Phase 03 audit for EGD: ID normalization, duplicates, `UTSW ∩ EGD = ∅`, overlap with BraTS-2021 and TCGA | Codex, Claude reviews | Phase 02 says a cohort that arrives after Phase 05 gets its own audit and freeze |
| 5 | Label counts for the cohort table only (IDH n, 1p/19q n) | Claude | `EXTERNAL_VALIDATION_PROTOCOL.md` allows counting; never join labels to predictions |
| 6 | Preprocess through the identical frozen pipeline (Phase 04) with the UTSW-train normalization statistics, unchanged | Codex | Heavy CPU; check where it runs: the data stays on the SSD machine |
| 7 | Un-skip the EGD leakage test (`tests/regression/test_leakage.py:256`) and re-run the whole file | Claude | Currently skipped: "EGD not downloaded" |
| 8 | Update `freeze_spec.json` (EGD paths, cohort roster hash) and the T11.1 checklist (criteria 8 and 9) | Claude | Criterion 9 becomes "arrived" |

## What nobody does until Gate E

Compute any metric against EGD labels, run any model on EGD, or look at EGD predictions. Steps 1 to 8 touch files,
identifiers and counts only. `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` stays 0; the firewall (`evaluation/firewall.py`) enforces it.

## Open decision

D-057: whether Gate E waits for EGD (family of 44) or goes with UCSF-PDGM alone (family of 29) and treats EGD as a second,
separately frozen evaluation. Steps 1 to 8 are worth doing either way, since the retention clause starts a clock.
