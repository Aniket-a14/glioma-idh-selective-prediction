# Phase 12 external run harness: contract for Codex

Written 2026-11-18 by Claude. Tasks T12.3 and the operational assertions of `PHASE_12_EXTERNAL_EVALUATION.md`, built and tested now on synthetic and internal stand-in data so the one real run does not use code that has never run. **Nothing in this task touches UCSF-PDGM or EGD data or labels. `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` stays 0 in every test run outside a test's own patched environment.** The Research Lead's later real run uses this code unchanged.

## What exists and what is missing

`scripts/freeze_predictions.py` (`freeze_run`) and `scripts/freeze_conditions.py` (via `evaluation/condition_sweep.py`, `evaluation/freeze.py`, `evaluation/freeze_mc_dropout.py`) freeze predictions for the two fixed UTSW splits only (`_SPLITS` in `freeze_predictions.py`). There is no path that scores another cohort, no firewall check at the point labels are read, and no check of the signed freeze manifest's hashes against the files actually used. This task adds that path, nothing else.

## Deliverable

`scripts/run_external_evaluation.py` and the smallest change to the modules above that lets one cohort be scored with the same code. The cohort is selected by name (`ucsf_pdgm` for the real run; the harness also accepts a test-only stand-in name that tests inject, see below). New code beyond a thin driver and the cohort-selection seam is a red flag per the phase file; if the seam needs more than that, stop and report.

Behaviour, in this order:
1. **Firewall first.** Before any label is loaded, call `evaluation/firewall.py::assert_external_eval_authorized(cohort)`. Do not copy its logic. Labels must not be read by any code that runs before this call (find where `IDHDataset` or the roster loader reads labels; if labels are read at construction, the seam must defer that until after the check, or stop and report).
2. **Verify against the signed manifest** (`firewall.freeze_manifest_path()`; fields per `PHASE11_MANIFEST_CONTRACT.md` and `evaluation/freeze_manifest.py`): for every checkpoint in the manifest, the sha256 of the file on disk equals the manifest entry; normalization statistics hash; the conditions config hash (`configs/evaluation/conditions.yaml`); the cohort roster hash for the external cohort; and `git rev-parse HEAD` equals the manifest's code commit with a clean tree. Any mismatch raises `FreezeMismatchError` before inference and writes nothing. Operational assertions only, no scientific tests.
3. **Score** all six conditions for all five ensemble members plus MC-dropout (30 passes) with the frozen conditions config, using the existing code paths. **The conformal quantile and temperature carry over from the internal calibration split; nothing is refit on external data.** The harness must not call any fitting function on external predictions (a test asserts `fit_temperature` and the conformal quantile function are never called with external rows, by patching them to raise).
4. **Write frozen artifacts write-once** (existing exclusive-create plus `.sha256` sidecar pattern) to `experiments/external_frozen/<cohort>/<run_id>/`, each with metadata: run id, git SHA, checkpoint hash, **freeze-manifest sha256**. Re-running into an existing directory raises `FileExistsError`.
5. **Report** at the end: counts per cohort and condition only. **Print no metric**: no AUROC, no accuracy, no loss, no per-patient value. The only labels-derived output allowed is the class counts already published in the post-QC manifest, so the harness can assert the roster size. The sanity print in `freeze_predictions.py` (`internal_test_auroc_sanity_check_only`) must not be carried over.
6. **After the run**: assert `git rev-parse HEAD` still equals the manifest commit (acceptance criterion 10 of Phase 12) and record that in the report file.

Internal behaviour must not change: re-running `freeze_run` and the condition sweep on the existing synthetic test fixtures gives byte-identical output to before the change (a regression test that compares against a stored digest of the old output from the unmodified code, generated first on the unmodified tree).

## Tests (all on synthetic data; each must fail on the unfixed behaviour)

1. With the flag unset or 0: the harness raises `ExternalEvaluationNotAuthorized` and **no label file is opened** (patch `open`/the label reader to record calls).
2. With a signed manifest in a temp directory and the flag patched to 1 inside the test only: the full path runs on a small synthetic cohort registered under a test-only cohort name and produces frozen artifacts with the manifest hash in their metadata.
3. Each of the five mismatches in step 2 (checkpoint, normalization, conditions config, roster, git SHA or dirty tree) raises `FreezeMismatchError` and leaves the output directory empty.
4. Existing output directory raises `FileExistsError`; the original is untouched.
5. No refit: see step 3.
6. No metric printed: capture stdout and stderr and assert no float that equals any metric computed from the synthetic labels, and no `auroc`/`ece`/`brier` substring.
7. Internal regression digest, as above.
8. `scripts/audit_external_leak.py` still reports 0 blocking findings (the new script may read labels only behind the firewall call; if the audit's allowlist needs the new file, add it with a comment saying why and say so in the report).

## Stop conditions (ask, do not invent)

The seam needs a scientific choice; labels cannot be deferred behind the firewall without restructuring the dataset; the conditions sweep for 5 members plus MC-dropout needs a code change beyond cohort selection; a manifest field you need is not in `PHASE11_MANIFEST_CONTRACT.md`. Report which and stop.

## Gates and done

`pytest tests/unit tests/regression -q` (note the count; the leakage regression needs `GLIOMA_STORAGE_ROOT` and the SSD, which may not be mounted: say if it skipped), mypy, ruff check and format, `scripts/check_invariants.py`, pre-commit. Branch `agent/codex/p12-external-inference` from main, small atomic commits, no merge. Do not edit `PROJECT_STATE.md`, `DECISION_LOG.md`, `paper/`, `pyproject.toml`, `evaluation/firewall.py` or `evaluation/freeze_manifest.py` (read-only for you). Use `PYTHONPATH=src` and `/Users/aniketsaha/4th_Year/Glioma/.venv/bin/python`; never `pip install`. Never run the harness against the real external data or with the real flag.
