# Phase 04 preprocessing and QC runbook

This runbook is for a run from the repository root on a machine where the
external data drive is mounted. The scripts resolve storage through
`glioma_selective.utils.paths`; set `GLIOMA_STORAGE_ROOT` (or the documented
`GLIOMA_DATA_ROOT`/`GLIOMA_ARTIFACT_ROOT` overrides) before starting. Do not
replace an accessor with a repository-local path.

Use the project virtual environment's Python. The commands below are written
as `python ...` and assume the environment is already active. Every command in
the canonical sequence is marked **[DATA DRIVE]** because it reads or writes
the mounted data, private metadata, manifests, caches, or generated figures.

Phase 04 is complete and its committed manifests are frozen. A rerun must use
explicit output paths outside `docs/research/manifests/` (`--manifest-output`
for step 6 and `--output` for steps 7 and 8), or be performed only at the
Research Lead's request. Step 3 merges verification into the existing
`preprocessing_status.json`; it does not recreate that status history.

## Canonical order

Run these commands from the repository root, in order. The first three scripts
have no argument parser. In particular, do not append `--help` to them: it
would execute the script rather than display help.

### 1. Discover retained inputs

Purpose: discover retained UTSW and UCSF-PDGM cases and build the aggregate
geometry report.

**[DATA DRIVE] Exact command:**

```text
python scripts/discover_preprocessing_inputs.py
```

Arguments: none; the script has no CLI parser.

Reads/writes: reads the real retained rosters and discovered case files. It
writes `paths.manifests_dir() / "preprocessing_discovery_report.json"`.

Prints: the aggregate report as formatted JSON on success. On a caught
discovery error it prints `discover_preprocessing_inputs.py: discovery failed`
to stderr.

Exit codes: `0` on success; `1` for a caught `OSError`, `RuntimeError`, or
`ValueError`.

### 2. Verify preprocessing inputs

Purpose: verify every retained case against the Phase 04 input checks and
produce both the aggregate report and the private per-case report.

**[DATA DRIVE] Exact command:**

```text
python scripts/verify_preprocessing_inputs.py
```

Arguments: none; the script has no CLI parser.

Reads/writes: reads the real retained rosters and discovered case files. It
writes `paths.manifests_dir() / "preprocessing_verification_report.json"` and
`paths.private_data_dir() / "preprocessing_verification_cases.json"`.

Prints: progress as `verified N/M cases` during the run, then the aggregate
report as formatted JSON. On a caught verification error it prints
`verify_preprocessing_inputs.py: verification failed` to stderr.

Exit codes: `0` on success; `1` for a caught `OSError`, `RuntimeError`,
`ValueError`, or `TypeError`.

### 3. Build the resumable status manifest

Purpose: load the private verification cases and create or merge the resumable
per-case Phase 04 status manifest.

**[DATA DRIVE] Exact command:**

```text
python scripts/build_preprocessing_status.py
```

Arguments: none; the script has no CLI parser.

Reads/writes: reads
`paths.private_data_dir() / "preprocessing_verification_cases.json"`. It
creates or updates `paths.manifests_dir() / "preprocessing_status.json"`.

Prints: the manifest's aggregate summary as formatted JSON. On a caught error
it prints `build_preprocessing_status.py: status manifest build failed` to
stderr.

Exit codes: `0` on success; `1` for a caught `OSError`, `RuntimeError`,
`TypeError`, or `ValueError`.

### 4. Generate visual-QC overlays

Purpose: create the Phase 04 visual-QC sample and review sheet. With no option,
the script creates the base sample; the mutually exclusive selection options
append one supported continuation sample.

**[DATA DRIVE] Base command:**

```text
python scripts/make_qc_overlays.py
```

**[DATA DRIVE] Supported selection commands:**

```text
python scripts/make_qc_overlays.py --tail N
python scripts/make_qc_overlays.py --shape-tail N --shape-tail-cohort utsw
python scripts/make_qc_overlays.py --new-borderline
python scripts/make_qc_overlays.py --residual-sample N
```

Arguments defined by the script:

- `--tail N`: append `N` lowest brain-fraction cases per cohort.
- `--shape-tail N`: append `N` cases for each shape-tail metric; it is
  mutually exclusive with `--tail`, `--new-borderline`, and
  `--residual-sample`.
- `--new-borderline`: append currently borderline cases not already indexed;
  it is in the same mutually exclusive group.
- `--residual-sample N`: append the seeded UTSW residual-risk sample; it is in
  the same mutually exclusive group.
- `--shape-tail-cohort {utsw,ucsf_pdgm}`: cohort used by `--shape-tail`,
  default `utsw`.

`N` is parsed as a non-negative integer. The defaults for the four selection
options are unset, so the plain command selects the base sample. A value of
zero is accepted and produces an aggregate zero-selection report for the
corresponding mode.

Reads/writes: reads
`paths.private_data_dir() / "preprocessing_verification_cases.json"`, the
retained rosters, discovered raw cases, and (for the base sample) the UTSW
metadata below `paths.raw_data_dir()`. It writes PNG overlays below
`paths.figures_dir() / "qc"`, the private index at
`paths.private_data_dir() / "qc_overlay_index.json"`, and the review sheet at
`paths.figures_dir() / "qc" / "qc_review_sheet.csv"`.

Prints: one aggregate JSON report containing selection counts, cohorts,
selection reasons, files written, requested mode, total size, and elapsed
time. On a caught error it prints
`make_qc_overlays.py: QC overlay generation failed` to stderr.

Exit codes: `0` on success, including an already-complete or zero-selection
run; `1` for a caught `OSError`, `RuntimeError`, `TypeError`, `ValueError`, or
`QCOverlayError`; argparse errors use argparse's non-zero exit.

### 5. Run the resumable preprocessing pipeline

Purpose: run or resume the Phase 04 per-case preprocessing pipeline and print
aggregate counts only.

**[DATA DRIVE] Exact command:**

```text
python scripts/run_preprocessing.py
```

Arguments defined by the script:

- `--cohort {utsw,ucsf_pdgm,all}`; default `all`.
- `--limit INTEGER`; default unset (`None`).
- `--cache-root PATH`; default unset, which lets the pipeline use
  `paths.processed_data_dir()`.
- `--status-path PATH`; default unset, which uses
  `paths.manifests_dir() / "preprocessing_status.json"`.
- `--outputs-path PATH`; default unset, which uses
  `paths.manifests_dir() / "preprocessing_outputs.json"`.
- `--n-threads INTEGER`; default `2`.
- `--dry-run`; a flag, default false.

Reads/writes: the pipeline reads its status and output indexes through
`paths.manifests_dir()`, uses `paths.processed_data_dir()` for the default
stage cache, and writes failure records to
`paths.private_data_dir() / "preprocessing_failures.json"` when not in dry-run
mode. It also reads the retained raw cases through the preprocessing discovery
layer. Explicit path arguments replace the corresponding defaults.

Prints: the pipeline result as formatted JSON. On a caught pipeline error it
prints `run_preprocessing.py: preprocessing run failed` to stderr.

Exit codes: `0` when the returned pipeline result has exit code `0`; otherwise
the script returns the pipeline result's `exit_code`. A caught `OSError`,
`RuntimeError`, `TypeError`, or `ValueError` returns `1`; argparse errors use
argparse's non-zero exit.

### 6. Build post-QC manifests

Purpose: convert the verified visual-QC status into post-QC exclusions and the
post-QC cohort manifest.

**[DATA DRIVE] Exact command:**

```text
python scripts/build_post_qc_manifests.py
```

Arguments defined by the script:

- `--status-path PATH`; default uses
  `paths.manifests_dir() / "preprocessing_status.json"`.
- `--exclusion-output PATH`; default uses
  `paths.manifests_dir() / "exclusion_manifest_post_qc.json"`.
- `--manifest-output PATH`; default is the repository's post-QC cohort-manifest
  destination defined in the script. The script refuses the frozen Phase 03
  manifest destinations.

Reads/writes: reads the status manifest through `paths.manifests_dir()`, the
pre-QC exclusion/cohort manifest inputs, and the retained rosters. With
defaults it writes the post-QC exclusion artifact through
`paths.manifests_dir()` and the post-QC cohort manifest at the script's
repository-owned manifest destination. Explicit output arguments replace the
corresponding defaults.

Prints: aggregate cohort counts and QC-reason counts as formatted JSON. On a
caught error it prints `build_post_qc_manifests.py: error: ...` to stderr.

Exit codes: `0` on success; `1` for a caught `OSError`, `RuntimeError`,
`TypeError`, `ValueError`, or `KeyError`; argparse errors use argparse's
non-zero exit.

### 7. Audit preprocessing outputs

Purpose: audit the indexed cached volumes and masks against the post-QC cohort
manifest and write the aggregate audit report.

**[DATA DRIVE] Exact command:**

```text
python scripts/audit_preprocessing_outputs.py
```

Arguments defined by the script:

- `--outputs PATH`; default unset, using the preprocessing output index under
  `paths.manifests_dir()`.
- `--cohort-manifest PATH`; default is the script's repository-owned post-QC
  cohort-manifest destination.
- `--output PATH`; default is the script's repository-owned output-audit
  report destination.
- `--cache-root PATH`; default unset, using `paths.processed_data_dir()`.

Reads/writes: reads the output index through `paths.manifests_dir()` by
default, the supplied or default post-QC cohort manifest, and cached outputs
through `paths.processed_data_dir()` by default. It writes the aggregate JSON
report to the supplied or default output path and the private failure log
through `paths.private_data_dir()`.

Prints: the aggregate audit report as formatted JSON. On an audit error it
prints either `audit_preprocessing_outputs.py: audit failed: ...` or
`audit_preprocessing_outputs.py: audit failed` to stderr.

Exit codes: `0` when the report's `passed` value is true; `1` when the report
is not passed or when a caught `OutputAuditError`, `OSError`, `RuntimeError`,
`TypeError`, or `ValueError` occurs; argparse errors use argparse's non-zero
exit.

### 8. Build the QC report

Purpose: combine automated verification, per-case status, and visual-QC
review artifacts into the roster-free QC report.

**[DATA DRIVE] Exact command:**

```text
python scripts/build_qc_report.py
```

Arguments defined by the script:

- `--status PATH`; default uses
  `paths.manifests_dir() / "preprocessing_status.json"`.
- `--verification PATH`; default uses
  `paths.private_data_dir() / "preprocessing_verification_cases.json"`.
- `--review-sheet PATH`; default uses
  `paths.figures_dir() / "qc" / "qc_review_sheet.csv"`.
- `--overlay-index PATH`; default uses
  `paths.private_data_dir() / "qc_overlay_index.json"`.
- `--output PATH`; default is the script's repository-owned QC-report
  destination.

Reads/writes: reads the status, verification, review-sheet, and overlay-index
inputs through the accessors above. It writes the aggregate report to the
supplied or script-default output path.

Prints: the aggregate QC report as formatted JSON. On a caught report error it
prints either `build_qc_report.py: report build failed: ...` or
`build_qc_report.py: report build failed` to stderr.

Exit codes: `0` on success; `1` for a caught `QCReportError`, `OSError`,
`RuntimeError`, `TypeError`, or `ValueError`; argparse errors use argparse's
non-zero exit.

## Existing no-argument inspection helpers

These helpers are not additional steps in the canonical order. If they are
used for diagnosis, invoke the plain command shown; none has an argument
parser, so `--help` would run the helper.

**[DATA DRIVE]** `python scripts/report_segmentation_targets.py` reads retained
cases, writes `paths.manifests_dir() / "segmentation_target_report.json"`,
prints formatted aggregate JSON, and returns `0` on success.

**[DATA DRIVE]** `python scripts/time_n4_smoke.py` reads a small retained sample,
uses a cache below `paths.interim_data_dir()`, prints a formatted aggregate
timing JSON report, and returns `0` on success or `1` for its caught failure
types.

**[DATA DRIVE]** `python scripts/reorient_smoke.py` reads a small retained
sample, uses a cache below `paths.interim_data_dir()`, prints aggregate counts,
and returns `0` when no checks fail or `1` when any check fails.

## Decision notes

- **D-023:** The Phase 05 split freeze precedes T04.6 normalization statistics
  and the related T04.8 z-score check; those commands are outside this Phase
  04 preprocessing and QC runbook.
- **D-026:** The retained UTSW and UCSF-PDGM inputs are verified passthrough
  inputs for the relevant preprocessing stages; the scripts still run their
  checks.
