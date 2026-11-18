# Phase 11 pre-flight (run 1: 2026-11-14; run 2: 2026-11-17, at the end of this file)

Preliminary. It tells the Research Lead what blocks Gate E today and gives T11.7 a repeatable tool. It does not
replace T11.1 or T11.7 at the real freeze: both are re-run on the final tree, and T11.7 by Person C (phase file).

## T11.1 entry-criterion checklist (state of 2026-11-14)

| # | Criterion | State | Evidence or what settles it |
|---|---|---|---|
| 1 | Phases 00 to 10 complete, prior gates passed | **No** | Gate D (Phase 06 independent review) not passed; Phase 10 incomplete (R7 training, R8 queued, final `analyze_phase10.py` run, Person C recomputation) |
| 2 | All internal results final | **No** | R7 and R8 results, HD95 for R7 and R8, single BH pass at Phase 13 (D-052) |
| 3 | Tree clean, everything merged to `main` | Yes today | `main` at the merge of this branch; must be re-checked at the freeze |
| 4 | Leakage regression test passes on final manifests | **Not run today** | `tests/regression/test_leakage.py` needs the external SSD (not mounted on this Mac); run it where `data/` resolves |
| 5 | UCSF-PDGM and BraTS-2021 disjoint, hashed | Met by exclusion | `cohort_manifest_post_qc.json`: 293 of 501 UCSF-PDGM patients excluded as `overlap:brats2021`, 202 retained, roster hash `19d5a89e...` |
| 6 | D-002, D-003, D-004 resolved and pre-registered | Yes | Resolved 2026-10-05, 2026-09-30, 2026-09-30; frozen in `PREREGISTRATION.md` |
| 7 | Statistical plan complete with exact BH family | **Partly** | SAP lists the family as 44 members, 29 confirmatory, "proposed composition, to confirm at the freeze"; D-052 stages the BH pass |
| 8 | External cohorts preprocessed through the frozen pipeline | UCSF-PDGM yes; EGD **no** | Phase 04 report (202 UCSF-PDGM cases); EGD not downloaded |
| 9 | EGD resolved (arrived, or single-cohort contingency recorded) | **No** | DUA sent; download, governance log row and overlap audit open |
| 10 | Research Lead has read and signed the manifest | **No** | `GATE_E_LOG.md` has no entries |

Also required before T11.4: `evaluation/firewall.py` (built 2026-11-14, was missing) and `scripts/generate_freeze_manifest.py`
(T11.2, not written).

## T11.7 hostile audit, run 1

Tool: `scripts/audit_external_leak.py` (read-only, exits 1 on a blocking finding; 18 unit tests with planted leaks).
Questions covered: the flag, external cohort names in model/training/selective/calibration/uncertainty/statistics code,
external-metadata readers outside the operational allowlist, external names in test fixtures, external numbers in
experiment artifacts, external metric lines in the docs, commit messages naming an external cohort with a metric, and
`GATE_E_LOG.md`.

| Check | Where run | Result |
|---|---|---|
| flag | this Mac, `.env` | 0, not set to 1 |
| model code | `src/glioma_selective/{models,training,selective,calibration,uncertainty,statistics}` | no external cohort name |
| label readers | all of `src` and `scripts` | only the allowlist (`data/metadata.py`, adapters, `leakage/`, `preprocessing/`, `firewall.py`, `paths.py`); one non-blocking hit, `scripts/verify_download_integrity.py:76` (path for checksums, no labels) |
| fixtures | `tests/fixtures` | none |
| artifacts | home GPU `/data/glioma-idh/storage/artifacts` (52 JSON/log files, R1 to R7, internal only) | no number under an external-cohort key |
| artifacts | external SSD on this Mac | **not scanned**, not mounted |
| docs | `docs`, `paper` | 10 lines reviewed by hand, none is an external result: the power check (half-widths, no labels), literature rows, the preprocessing QC mask-alignment Dice for UCSF-PDGM (image against image, no label), and log lines naming the cohorts |
| history | all branches | no commit message names an external cohort with a metric |
| gate log | `GATE_E_LOG.md` | no entries |

One thing the audit cannot see: a label count was computed for UCSF-PDGM (`data/metadata.py`,
`label_verification.json`, D-009). The external-validation protocol permits counting labels for the cohort table and
blocks joining labels to predictions; no code path does that, and `phase10_analysis.py` only lists UCSF-PDGM
comparisons as `pending_external`.

Not covered, for Person C to do at the freeze: the external SSD, notebooks and shell history on every machine used,
MLflow runs if any, and chat or email transcripts. Re-run the script on the final tree with `--artifact-root` set to
every artifact directory.

---

# Run 2 (2026-11-17), `main` at `e331095` plus this change

Same status as run 1: preliminary, re-run on the final tree at the freeze. Evidence below was collected today.

## T11.1 entry-criterion checklist (state of 2026-11-17)

| # | Criterion | Run 1 | Now | Evidence or what settles it |
|---|---|---|---|---|
| 1 | Phases 00 to 10 complete, prior gates passed | No | **No** | Gate D for Phase 06 still needs its independent review (`PHASE06_CLOSEOUT.md` line 61: "It has not happened"); Phase 10 acceptance still needs Person C's recomputation (pack ready, not run by them). Phase 10 computation is done: R7 and R8 frozen, E1 to E4 computed, HD95 frozen |
| 2 | All internal results final | No | **Yes for computation; formally open** | `phase10_analysis.json` is final for the 14 UTSW members (SHA-256 `3d2a220c...`), HD95 for R2, R7, R8, M6 cells (`phase09_m6_analysis.json`). Still open by design: the single BH pass over the 29-member family (Phase 13, D-052). Person C's recomputation (criterion 1) |
| 3 | Tree clean, everything merged to `main` | Yes | **Yes today, one item** | `main` equals `origin/main`, working tree clean. One agent branch not on `main`: `agent/claude/p08-naturally-missing` (a one-file T08.7 doc, from 2026-10-27); merged as part of this change. Re-check at the freeze |
| 4 | Leakage regression test passes on the final manifests | Not run | **Met today (re-run at the freeze)** | With the SSD mounted and `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`: `tests/regression/test_leakage.py` 7 passed, 1 skipped (the EGD test, EGD not downloaded, D-018). Earlier the same day it skipped on the home server and on the Mac without the SSD |
| 5 | UCSF-PDGM and BraTS-2021 disjoint, hashed | Met | **Met** | Unchanged from run 1: 293 of 501 excluded as `overlap:brats2021`, 202 retained, roster hash `19d5a89e...` |
| 6 | D-002, D-003, D-004 resolved and pre-registered | Yes | **Yes** | `PREREGISTRATION.md` sha256 sidecar matches (`e350d9fa...`); D-055 (2026-11-17) confirmed the pre-registered carried-over conformal quantile for drop_t1ce, so nothing in the frozen rules moved |
| 7 | Statistical plan complete with exact BH family | Partly | **Partly** | SAP still says the 29-member composition is "proposed, to confirm at the freeze". The 14 UTSW members are computed; the 15 external ones are listed as `pending_external` in `bh_family`. Research Lead confirms the family before the manifest is signed |
| 8 | External cohorts preprocessed through the frozen pipeline | UCSF-PDGM yes, EGD no | **UCSF-PDGM yes, EGD no** | Phase 04 report (202 UCSF-PDGM cases); no EGD data |
| 9 | EGD resolved | No | **No** | `DATA_ACCESS_LOG.md` has no EGD entry after the DUA submission on 2026-10-05 and the "last checked 2026-10-11" in the T08.7 note. Research Lead: has access been granted, or is the single-cohort contingency to be invoked (a decision for you, `PHASE_11` lists it as such)? |
| 10 | Research Lead has read and signed the manifest | No | **No** | `GATE_E_LOG.md` has no entries; flag is 0 |

New since run 1 for criteria 7 and 10: the manifest generator (`scripts/generate_freeze_manifest.py`, T11.2, merged) and a
draft `protocols/freeze_spec.json` whose every value is sourced in `PHASE11_FREEZE_SPEC_SOURCES.md`. A dry run against the
real run records agreed on every hash (checkpoint, split, exclusion, normalization). The manifest has not been generated
for real, and nothing has been signed.

## T11.7 hostile audit, run 2

`scripts/audit_external_leak.py` on the Mac tree and, with `--artifact-root /data/glioma-idh/storage/artifacts`, on the
home server's checkout. Both runs gave the same result.

- **One new blocking finding, fixed:** `evaluation/freeze_manifest.py:193` calls `external_data_dir()`. That is the
  generator's own guard (G3): it resolves the path only to refuse a spec file under it, and reads no label or metric. The
  file is now on the audit's allowlist, with a comment saying why. After the change the audit exits 0 on both machines.
- **Non-blocking, as in run 1:** `scripts/verify_download_integrity.py:76` (checksum path, no labels) and 10 doc lines
  that mention the external cohorts; the count and the files are the same as run 1 (the power check, literature rows,
  the Phase 04 mask-alignment Dice for UCSF-PDGM, log lines). Not re-read line by line today; Person C re-reads them at the freeze.
- **Server artifacts:** no number under an external-cohort key in the home server's artifact tree (now R1 to R8, internal only).
- **SSD artifacts scanned (SSD mounted later the same day):** `--artifact-root /Volumes/Research_2/artifacts` gave 0 blocking findings, 11 review items (the same 10 doc lines and the checksum-path hit). The SSD now also holds every run directory R1 to R8 (3.1 GB, copied from the home server; checkpoint hashes equal their records).
- Still not covered, as in run 1: notebooks and shell history on every machine, MLflow if any, chat and email transcripts. (The external SSD itself was scanned for experiment artifacts only, not for stray files.) Person C does these at the freeze.

## What blocks Gate E today

1. Gate D (Phase 06 independent review) and Person C's recomputation (criterion 1).
2. Confirming the BH family (criterion 7).
3. EGD: arrived, or the single-cohort contingency recorded (criterion 9).
4. The signature (criterion 10), which only the Research Lead can give.

Nothing in 1 to 3 needs the GPU. Criterion 4 is met today and is re-run on the final tree.

## Update 2026-11-18: EGD deferred (D-057 resolved)

The Research Lead deferred the EGD download. Effect on the checklist: criterion 9 (EGD resolved) is **met by the recorded single-cohort contingency** (D-057 alternative (b)); criterion 8 is met for the cohort that will be evaluated (UCSF-PDGM); the BH family for the first external run is 29 (criterion 7 still needs the Research Lead's confirmation, `BH_FAMILY_CONFIRMATION.md`); the EGD leakage test stays skipped. EGD is a later, separately frozen evaluation reported as an addendum. Remaining blockers: Gate D reviews (Phases 06 to 10), D-058, Person C recomputation, BH family confirmation, T11.4 signature.
