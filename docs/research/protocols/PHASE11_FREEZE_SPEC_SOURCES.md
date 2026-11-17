# Freeze spec: where each value comes from (T11.2 input; DRAFT for the Research Lead)

`freeze_spec.json` (same folder) is the input of `scripts/generate_freeze_manifest.py`. It contains no new decision: each
value below is copied from a frozen or resolved source. Checked 2026-11-17 by Claude; nothing here is signed or generated.
The generator checks that files exist and agree with their run records, not that these values are right, so this table is
what the Research Lead reads before T11.4.

| Manifest field | Source | Checked how |
|---|---|---|
| `model_checkpoints` (R2 primary, R3 to R6 seeds 1 to 4) | `phase09_analysis.json` provenance, `PHASE09_INTERNAL_RESULTS.md` (M4 = R2 to R6) | `sha256sum best.pt` on the server equals `checkpoint_hash` in each `record.json`, all five |
| `preprocessing` | R2 `record.json` (`phase06-frozen-zscore-and-2mm-whole-brain`) and `configs/preprocessing/base.yaml` | read by the generator |
| `normalization_statistics` | `data/manifests/normalization_stats.json`, `f6b7cc70...` (PROJECT_STATE 2026-09-30) | R2 record `normalization_stats_sha256` equal |
| `exclusion_manifest` | `data/manifests/exclusion_manifest_post_qc.json`, `ceba3f4e...` | equals R2 `exclusion_list_hash` |
| `utsw_split_manifest` | `data/manifests/splits.json`, `b8696d44...` (PREREGISTRATION section 13) | equals R2 `split_manifest_hash` |
| `calibration_parameters` | T = 1.1247554245437905, `phase09_analysis.json` provenance `full_temperature`; procedure PHASE07 K5, D-045 | value read from the file |
| `conformal` | D-002, D-045, PHASE07 K1, K2, K4; quantiles 0.7772720380564715, 0.6621428463530682, 0.39233376398264225 at alpha 0.05, 0.1, 0.2 from `phase09_analysis.json` `conformal.full.carried_over` | values read from the file |
| `abstention_definition` | D-003, PREREGISTRATION section 5 | text |
| `operating_points` | D-033, PREREGISTRATION sections 6 and 7 | text |
| `missing_modality_conditions` | PREREGISTRATION section 4, `configs/evaluation/conditions.yaml` | file hash `e74e253e...` equals the PREREGISTRATION section 13 value |
| `primary_metrics` | D-033, PREREGISTRATION section 6 | text |
| `c4_tolerance_band` | D-004, PREREGISTRATION section 8 (7 pp primary, 5 pp secondary) | text |
| `statistical_analysis_plan` | `STATISTICAL_ANALYSIS_PLAN.md` `27294ac1...`; `PREREGISTRATION.md.sha256` `e350d9fa...` | `shasum -a 256` equals both |
| `authorizing_signature` | not in the spec; the generator writes it unsigned | |

## Points the Research Lead needs to decide or confirm before T11.4

1. **M6 has no checkpoint.** The tumor-aware joint comparator (M6) needs its own training run (D-006) and has none; the
   Phase 09 results list its cells as absent. The 108-cell grid in `conditions.yaml` includes it. Either the run is made
   before Gate E, or the freeze names M6 as not evaluated (a change to the pre-registered cell count, which needs a
   decision-log entry). The spec as written lists M6 under mechanisms and has no M6 checkpoint.
2. **Carried-over conformal quantile.** The frozen method applies the full-input calibration quantile to every condition
   and cohort (PREREGISTRATION section 3: quantiles come from UTSW calibration data only). Phase 09 found this degrades
   coverage for `drop_t1ce` at alpha 0.1 and 0.2 (0.589 at nominal 0.90 for alpha 0.1). The spec freezes the carried-over version and
   keeps the refit as a diagnostic, as written in Phase 09. The open question from Phase 09 stands: whether the C4
   half-width rule or the criterion text governs those cells.
3. **R7 and R8 are not in the freeze.** They are internal ablations (D-051) and are not evaluated externally.
4. **Ensemble includes the primary run.** M4 is R2 to R6, so R2 appears once as `primary_seed0`.
5. **Operating points** are the two grids in PREREGISTRATION section 7. No threshold is frozen as a single number: the
   conformal quantiles above and the temperature are the only fitted values.
6. **Checkpoint file.** `best.pt` (the early-stopping checkpoint, matching the `record.json` hash), not `last.pt`.
