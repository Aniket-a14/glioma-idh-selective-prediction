# Phase 13 figure and table builder: contract for Codex

Written 2026-11-18 by Claude (owner of the claims, metrics and what each figure may say). Codex implements. Tasks T13.4, T13.5, T13.7, T13.8 of `PHASE_13_RESULTS_FREEZE.md`, built early on internal data so Gate F is not the first time the pipeline runs.

## Scope

One entry point: `python -m glioma_selective.cli.build_paper_artifacts --run-id <R2 id> [--m6-run-id <R1 id>] [--out-dir DIR]`.
Modules: `src/glioma_selective/visualization/{risk_coverage,reliability,coverage,abstention}.py`, `src/glioma_selective/visualization/tables.py`, `src/glioma_selective/cli/build_paper_artifacts.py`. Tests in `tests/unit/` (and `tests/regression/` for the regeneration test). No change to any file under `evaluation/`, `selective/`, `calibration/`, `models/`, `training/`.

**Output directory.** Default `build/paper_artifacts/` (git-ignored), never `paper/`. `paper/` is human-owned and the Research Lead moves the files there. Do not write to `paper/` and do not edit `paper/REGISTRY.md`; write the registry rows to `<out-dir>/REGISTRY_ROWS.md` in the same column layout as `paper/REGISTRY.md`.

## Inputs (frozen files only)

All under `paths.artifacts_dir()/experiments/<run_id>/` (resolve through `utils/paths.py`; never hard-code a root):
- `phase09_analysis.json` (schema `phase09_analysis.v1`; written by `evaluation/phase09_analysis.py::analyze_phase09`): per condition and mechanism: `rc_points`, `aurc_mean_over_cutoffs`, `oracle_aurc`, selective risk at coverage with `rejected_but_correct_rate`, `monotonicity`, conformal blocks (carried-over and refit variants: `empirical_coverage`, `coverage_deviation_bootstrap`, set summaries), claims C1 to C6.
- `phase09_m6_analysis.json` (schema `phase09_m6_analysis.v1`, optional): M6 cells.
- `phase10_analysis.json`: headline AUROC, AUPRC, AURC, ECE, Brier with intervals, the 14-member family with raw p, `bh_family`.
- `predictions.parquet` and `conditions/*.parquet` for reliability diagrams (bins from the existing `evaluation/calibration_metrics.py`, not re-implemented).
- `data/manifests/cohort_manifest_post_qc.json` and the exclusion manifests for Table 1 and 2 and Figure 1 (counts only).

Each file has a `.sha256` sidecar: the builder verifies it before use and refuses on mismatch. Read the code that writes these files for exact keys; do not guess keys from this note. To get a real-shaped input in tests, build synthetic runs the way `tests/unit/test_phase09_analysis.py` does and run `analyze_phase09` on them. The real internal files are on the external SSD and the home server and are not available in every session; the builder must work on the synthetic ones and on the real ones with no code change.

## Outputs

| Element | Content | Source |
|---|---|---|
| Fig 1 | Cohort flow (counts only) | manifests |
| Fig 2 | Risk-coverage curves, M1 to M6, one panel per condition; internal now, external panels drawn only when an external analysis file is passed | `phase09_analysis.json` |
| Fig 3 | Nominal vs empirical coverage per condition and alpha, with the 0.07 half-width band from the frozen rule | conformal blocks |
| Fig 4 | Reliability diagram, raw and temperature-scaled | predictions |
| Fig 5 | Abstention vs error: rejected-but-correct rate at each coverage | selective-risk blocks |
| Table 1, 2 | Cohort characteristics; exclusions with reasons | manifests |
| Table 3 | AURC and selective risk at coverage 0.5 to 0.9, all mechanisms by condition | phase09 |
| Table 4 | Coverage deviation with intervals vs the band | phase09 conformal |
| Table 5 | AUROC, AUPRC, ECE, Brier with intervals | phase10 |
| Table 6 | Abstention analysis incl. rejected-but-correct rate | phase09 |

Tables are written as `.csv` (full precision as stored) and `.tex` (booktabs, numbers rounded by one named function with the digits per column fixed in one place). Figures as `.pdf` and `.png`.

## Hard rules (each needs a test that fails on the old behaviour)

1. **No hand-typed number.** Every number in a table or figure label comes from a loaded file. A test greps the module sources for numeric literals used as results (allowed: digits, axis limits, tolerances named as constants).
2. **SI-14.** A table builder that emits AUROC refuses (raises `MetricHierarchyError`) unless ECE, Brier, AURC and coverage are in the same table or the same call. Test: calling the AUROC table builder without the other four raises.
3. **Simulated missingness (D-008).** Every figure caption string and table header that covers a missing-modality condition (`drop_*`, `t1ce_flair_only`) contains the word "simulated". Test over all generated captions and headers.
4. **No checkpoint reads.** Figure and table code imports nothing from `models/` or `training/` and opens no `.pt` file. Test by import-graph check and by running the builder with `torch` import blocked.
5. **External firewall.** The builder never opens an external-cohort file unless `GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1` and the analysis path is given explicitly; the check goes through `evaluation/firewall.py`, not a copy of its logic. With the flag at 0 and an external path given, it raises. Test both.
6. **Determinism.** Same inputs give byte-identical `.csv` and `.tex`, and identical `.png`/`.pdf` bytes: matplotlib `Agg` backend, fixed `savefig` metadata (`CreationDate` and `Producer` removed or set constant, `svg.hashsalt` set), fixed font, fixed figure size, no use of wall-clock time, no `set` iteration order in output. Regeneration test (T13.7): run twice into two directories and compare file bytes (`tests/regression/test_paper_artifacts_regeneration.py`); if PDF bytes cannot be made identical, compare the rendered PNG and say so in the report rather than loosening silently.
7. **Absent cells stay absent.** A `{"absent": true, ...}` cell is drawn as an empty, labelled slot with its `reason`, and written to the table as the word `absent`, never as 0 or NaN.
8. **Wide intervals stay visible.** Intervals are drawn at every plotted coverage with no smoothing and no grid thinning (acceptance criterion 11).
9. **Claim statuses are copied, not recomputed.** Anything about C1 to C6 is read from the `claims` block; the builder does not re-evaluate a criterion.
10. **Registry rows** list for each element: path, `Generated from` (the file names and their sha256 prefixes), the exact regenerate command, status `GENERATED`.

## Stop conditions (ask, do not invent)

A key you need is not in the frozen file; a figure needs a design choice that changes interpretation (axis range, which interval to show); a number needs recomputing. Report which and stop. Axis ranges default to data-driven limits with a fixed 0 to 1 for risk, coverage and probability axes.

## Gates and done

`pytest tests/unit tests/regression -q` (note the count), `python -m mypy` on the new modules, `python -m ruff check` and `ruff format`, `scripts/check_invariants.py`, pre-commit. Commit small and atomic on `agent/codex/p13-figures-tables`, no merge, leave the branch ready. Do not edit `PROJECT_STATE.md`, `DECISION_LOG.md`, `paper/`, or `pyproject.toml` (request a dependency in the report; matplotlib is already declared). Use `PYTHONPATH=src` with the repo venv at `/Users/aniketsaha/4th_Year/Glioma/.venv/bin/python`; never `pip install` (an earlier session re-pointed the shared editable install).
