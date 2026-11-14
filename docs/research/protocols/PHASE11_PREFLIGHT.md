# Phase 11 pre-flight, run 1 (2026-11-14)

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
