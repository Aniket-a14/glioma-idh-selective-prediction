# Gate D readiness, Phases 07 to 10 (evidence table for the independent reviewers)

Written 2026-11-17 by the author of the work, so this is the author's check, not the independent review. Gate D needs a
reviewer who did not write the phase. For Phase 06 see `GATE_D_REVIEW_BRIEF_PHASE06.md`. Columns: **Met** (evidence found
and, where marked "checked today", re-run today), **Not met** (as written in the phase file), **Open** (cannot be settled
without a person or later phase). "Doc" means I read it in the named file today; I did not re-run it.

## Phase 07: calibration and uncertainty (R1 to R6)

| # | Criterion | State | Evidence |
|---|---|---|---|
| 1 | D-002 resolved | Met | `DECISION_LOG.md` D-002, RESOLVED 2026-10-05 (split conformal primary, CRC secondary) |
| 2 | Mechanisms are independent modules | Met (doc) | `calibration/{temperature,conformal,crc}.py`, `uncertainty/mc_dropout.py`, `selective/*.py`. No shared state was re-audited today |
| 3 | Every parameter fitted on the calibration split only, asserted by test | Open | Not re-verified today: name the test that asserts it (candidates: `tests/unit/test_training_loop.py`, `test_condition_analysis.py`) |
| 4 | Conformal quantile has the n+1 correction, hand-calculated test | Met (doc) | `tests/unit/test_conformal.py` quantile fixtures; the Phase 09 results use k = ceil((n+1)(1-alpha)) |
| 5 | Coverage within +/-2 pp on exchangeable internal data | **Not met as written** | R2 0.960 / 0.871 / 0.726 and R1 0.968 / 0.919 / 0.758 at 0.95 / 0.90 / 0.80; three of six outside. Replication check (checked today): mean coverage 0.953 / 0.905 / 0.801, SD 2.5 to 5 pp. **D-058, open** |
| 6 | Temperature scaling lowers internal-test ECE | **Not met** | R2 0.119 to 0.122, R1 0.186 to 0.191; Brier improves slightly. **D-058, open** |
| 7 | ECE, Brier, reliability stored for M1 and M2 | Met | `PHASE07_INTERNAL_RESULTS.md`; per-run blocks in `phase10_analysis.json` |
| 8 | R3 to R6 trained, run budget | Met | R1 to R6 plus R7, R8 is 8 runs, the phase 10 limit is 9; run records on the SSD |
| 9 | Independent implementations agree on every fixture | Met (doc) | `PHASE07_METRIC_CONTRACTS.md`, `PHASE09_METRIC_CONTRACTS.md` cross-check rule; Person C pack (2026-11-17) recomputes the Phase 10 numbers (188 of 188) with new code |
| 10 | Frozen predictions for all mechanisms | Met (doc) | `predictions.parquet` R1 to R8, `mc_dropout.parquet` R2, ensemble members R2 to R6 |

## Phase 08: missing modality

| # | Criterion | State | Evidence |
|---|---|---|---|
| 1 | Modality dropout active in R2 to R6, schedule documented | Met for R2 (checked today) | R2 `record.json`: `modality_dropout: true`, `modality_dropout_keep_all_probability: 0.5`; schedule in `training/modality_dropout.py`. R3 to R6 records not opened individually today |
| 2 | Six conditions implemented, masks unit-tested | Met (doc) | `evaluation/conditions.py`; `tests/unit/test_conditions.py`, `test_condition_sweep.py`, `test_modality_dropout.py` |
| 3 | Zeroing verified, no imputation path | Met (checked today) | The only mentions of imputation in `src/` are two docstrings saying it never happens (`training/modality_dropout.py:3`, `models/segresnet.py:66`) |
| 4 | Full sweep, 6 conditions x 6 mechanisms | Met | `phase09_analysis.json`: 30 internal cells (6 conditions x M1 to M5; M4 from R2 to R6); M6 adds 6 internal cells in `phase09_m6_analysis.json` (36 internal cells; 108 is the whole 3-cohort grid, 72 without EGD, of which only the 36 internal ones exist). Corrected 2026-11-18 after the Gate D review (F10) |
| 5 | Artifacts frozen per condition with run id, git SHA, checkpoint hash | Met (checked today for R1) | `conditions_meta.json` carries `run_id`, `checkpoint_hash`, `git_sha`, `record_git_sha`; sha256 sidecars verify |
| 6 | Conformal quantiles refit and carried over | Met (doc) | `phase09_analysis.json` `conformal.<condition>.{carried_over,refit}` |
| 7 | Degradation ordering plausible | Met (doc) | T1ce dropped is worst in every run (`PHASE08_INTERNAL_RESULTS.md`); clinically expected |
| 8 | Naturally missing cases analysed (D-012, D-008) | **Open** | UTSW and UCSF-PDGM: none (T08.7). EGD pending. D-012 is still OPEN in the log and D-008 is a Phase 14 reporting duty |

## Phase 09: selective prediction, internal

| # | Criterion | State | Evidence |
|---|---|---|---|
| 1 to 5 | RC curves, AURC with 2000-draw CI, selective risk, coverage by alpha, monotonicity | Met | `phase09_analysis.json` (SHA-256 `99f48c7d...`), `PHASE09_INTERNAL_RESULTS.md` |
| 6 | Rejected-but-correct reported for every mechanism and condition | Met (doc) | per-cell `enrichment` and the rate in the results file; not re-opened today |
| 7 | Enrichment with a permutation test | Met | 10000 permutations, BH across the grid (C6 rule) |
| 8 | Calibration-vs-test coverage discrepancy reported | Open | Not re-verified today; check the `conformal` block for a calibration-versus-test column |
| 9 | Independent implementations agree | Met (doc) | `PHASE09_METRIC_CONTRACTS.md` (Claude S1, S4, S6; Codex S2, S3, S5) |
| 10 | JSON before any table or figure | Met | results docs are generated from the JSON; no figure exists yet |
| 11 | C1, C2, C5, C6 adjudicated | Met | `PHASE09_INTERNAL_RESULTS.md` claim table (it also adjudicates C4: C2, C4 and C6 are refuted there; read the table for the others) |
| 12 | Refutations in `paper/NEGATIVE_RESULTS.md` the day found | **Not met** | `paper/NEGATIVE_RESULTS.md` is the empty skeleton (26 lines, no entries). It is human-owned; draft entries sit at the end of `PHASE09_INTERNAL_RESULTS.md`. Research Lead to place them, plus the ECE finding (D-058) and the E1 to E4 nulls |

## Phase 10: ablations and internal statistics

| # | Criterion | State | Evidence |
|---|---|---|---|
| 1 | Six ablation axes complete (internal vs external deferred) | Met | missing modalities (Phase 08), M1 vs M2 (D1, D2), always-predict vs selective (Phase 09), uncertainty method (A1 to A3), R7 and R8 (E1 to E4) |
| 2 | R7 and R8 trained, runs at most 9 | Met | 8 runs in total |
| 3 | Bootstrap CIs, at least 1000 draws | Met | 2000 draws, `phase10_analysis.json` (SHA-256 `3d2a220c...`); recomputed independently, 188 of 188 |
| 4 | DeLong for paired AUROC | Met | E1, E3 (`statistics/delong.py`, `test_delong.py`) |
| 5 | Paired bootstrap for AURC and selective-risk deltas | Met | A, B, D, E2, E4 (`test_paired_bootstrap.py`) |
| 6 | BH across the pre-registered family, membership matches Phase 05 exactly | **Open** | The SAP calls the 29-member composition "proposed, to confirm"; the BH pass runs once at Phase 13 (D-052); a supplementary 14-member BH is reported and labelled. `BH_FAMILY_CONFIRMATION.md`, D-057 (29 or 44) |
| 7 | RQ4 exploratory, wide CIs, no inference | Met | `probe_1p19q.json`, labelled exploratory |
| 8 | Dice and HD95 | Met | `segmentation_dice.json`, `segmentation_hd95.json` for R2, R7, R8 |
| 9 | Independent implementations agree (bootstrap, DeLong, BH) | Met (doc) | `PHASE10_STATS_CONTRACTS.md`, Codex built from it |
| 10 | Statistics machine-readable and committed | Met with a note | JSON is on the SSD with SHA-256 sidecars; the repository holds hashes and results docs, not the JSON (data policy) |
| 11 | All internal analysis final | **Open** | Computation is final. Formally open until Person C's recomputation and the Gate D reviews |

Scientific validation items of Phase 10:
1. Person C recomputation: pack ready, not run by them (`PERSON_C_RECOMPUTATION_GUIDE.md`).
2. Bootstrap CI widths against the power check (done today, author's reading): R2 AUROC bootstrap half-width 0.066 against 0.073 predicted at true AUROC 0.85 and 0.059 at 0.90; Hanley-McNeil 0.078 against 0.085 and 0.071. Selective-risk half-widths 0.063 to 0.080 across coverage 0.5 to 0.9, against 0.065 to 0.070 (true AUROC 0.85) and 0.047 to 0.063 (0.90) predicted: about 10 to 20% wider at high coverage than the binormal model. The power model held at the AUROC level; the selective-risk intervals are somewhat wider than predicted.
3. R7 and R8 against the literature they reproduce: **drafted 2026-11-18 from search snippets only** (`PHASE10_LITERATURE_SANITY_CHECK.md`): no sign of an implementation error; the sources still need a full-text check under D-010 before any number is cited.

## What this means for Gate E criterion 1

Not ready. Open items: D-058 (Phase 07 criteria 5 and 6), the unfilled `NEGATIVE_RESULTS.md` (Phase 09 criterion 12),
D-012 and the EGD part of Phase 08 criterion 8, the BH family and D-057 (Phase 10 criterion 6), Person C (Phase 10
criterion 11), and the independent reviews themselves for Phases 06 to 10. Items marked "Open" or "(doc)" need the
reviewer to re-run them, not to trust this table.
