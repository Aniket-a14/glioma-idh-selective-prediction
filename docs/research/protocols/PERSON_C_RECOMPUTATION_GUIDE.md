# Person C: recomputing the Phase 10 headline numbers

Written 2026-11-17. Phase 10 acceptance needs an independent recomputation of every headline statistic from the frozen
artifacts (`PHASE_10_ABLATIONS_INTERNAL_STATS.md`, scientific validation 1; `PUBLICATION_PLAN.md` step 8). This is the
pack for it. CPU only, about 2 seconds of compute, internal UTSW data only.

## What you get

- `scripts/person_c_recompute.py`: one file, needs numpy and pandas (with pyarrow). It imports nothing from
  `glioma_selective`. Every metric is written out from the definitions in `PHASE09_METRIC_CONTRACTS.md` and
  `PHASE10_STATS_CONTRACTS.md`.
- A folder `experiments/` with, for each run you need, the frozen files and their `.sha256` sidecars (ask the Research
  Lead for the copy; it holds patient-level internal predictions, so it stays inside the team):
  - R2 `01M46999FB083AX4WW0067YM13`: `predictions.parquet`, `conditions/*.parquet`, `phase10_analysis.json`
  - R3 to R6 (`01M4FPECM9DKAR7F6B7VFRQNC5`, `01M60CYFD2AYA8DCPBTDSJS4DM`, `01M66E2KR6ZV2YPBTNPF5FD53T`,
    `01M776GTZC70FTB1ABD2DDMYHH`): `conditions/full.parquet`
  - R7 `01M7C0KRNY5M2SNH59PH97XZ8K` and R8 `01M7JZYEBFCJF8WY0W1WJ3RZX7`: `predictions.parquet`

The script refuses any parquet file whose SHA-256 differs from its sidecar, and refuses `phase10_analysis.json` if it
does not match its own sidecar.

## Run it

```
python scripts/person_c_recompute.py --results-root PATH/TO/experiments \
    --reference PATH/TO/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

It prints one line per number (`ok` or `FAIL`, your value, the reference value, the difference) and exits 0 only if all
188 agree. On the Research Lead's Mac the result is 188 of 188.

## What it checks (188 numbers)

For R2, R7 and R8 on the 124-patient internal test (35 IDH-mutant): temperature, AUROC with bootstrap and Hanley-McNeil
intervals, AUPRC, AURC (M5 ranking), selective risk and attained coverage at 0.5 to 0.9, ECE and Brier for M1 (raw) and
M2 (temperature-scaled), each with the 95% bootstrap interval. Then the 14 computed members of the pre-registered
family: A1 to A3, B1 to B5, D1, D2, E1 to E4, each with point, interval and raw p (exact fractions for bootstrap p,
DeLong for E1 and E3).

## What agreement means

- Bootstrap draws come from `numpy.random.default_rng(0).integers(0, 124, size=(2000, 124))`, one matrix shared by every
  comparison (SAP section 4). With the same NumPy stream, points, interval limits and p-values match exactly; p-values
  are compared as exact fractions. Tolerance is 1e-9 for points and limits.
- Calibration numbers (temperature, M1 and M2 ECE and Brier, D1, D2) are compared at 1e-6. Two reasons, both known: the
  predictions are stored as float32, and the main analysis stops its temperature bisection at 1e-8 in 1/T, which leaves
  R2's T about 7e-7 from the exact minimum (1.1247554 against 1.1247561).
- If you use a different random generator, intervals and bootstrap p-values agree only up to Monte Carlo error
  at 2000 draws. That is not a failure, but say which generator you used (this was not measured).

## What it does not check

- Segmentation Dice and HD95 (needs the masks and the segmentation freeze files).
- The 1p/19q probe (`probe_1p19q.json`), exploratory, D-007.
- Phase 09: conformal sets and coverage (C4), the claim rules C1 to C6, monotonicity counts, M6 cells.
- The Benjamini-Hochberg listing (the supplementary 14-member pass) and the 29-member family bookkeeping.
- That the frozen predictions themselves are right (they come from the model, not from this check).

## How independent this is

The script was written by the same agent that wrote the contracts and the main analysis, so a shared misreading of a
formula would pass. The stronger check is to write your own implementation from `PHASE09_METRIC_CONTRACTS.md` and
`PHASE10_STATS_CONTRACTS.md` without reading the script, then compare numbers; use the script as a second opinion when
your numbers differ. Two choices are not in the contracts and you will have to match them: the Hanley-McNeil
interval uses z = 1.959964 (not 1.96), and the temperature objective is mean binary cross-entropy of
`sigmoid(logit / T)` on the 124 calibration patients, T in [0.05, 20].

## Report back

Send the Research Lead the full output, your Python and NumPy versions, and any number that differs by more than the
tolerance with your reading of why. The Research Lead records it in `PROJECT_STATE.md` and in
`PHASE10_INTERNAL_RESULTS.md` ("Open for Phase 10"). A mismatch is a finding, not something to adjust the reference to.

## Choices the contracts left open (found by the independent Codex recomputation, 2026-11-18)

Both implementations need these; the first reference script fixed them silently:
- R2 metrics come from `conditions/full.parquet`, not `predictions.parquet` (max logit difference between them 4.4e-5). R7 and R8 use `predictions.parquet`.
- Sort every cohort by `patient_id` before applying the bootstrap matrix; parquet row order is not sorted and the exact resample depends on it.
- AUPRC is non-interpolated average precision.
- Hanley-McNeil: `Q1 = A/(2-A)`, `Q2 = 2A^2/(1+A)`, variance `[A(1-A) + (m-1)(Q1-A^2) + (n-1)(Q2-A^2)]/(mn)`, z = 1.959964, limits clipped to [0, 1].
- M3 loss is the raw classifier's error and M4 loss is the ensemble-mean classifier's error (D-059). Reading M3 as the MC-mean classifier gives 180 of 188, with A1 and A3 differing as in `PERSON_C_REPORT_CODEX.md`.

Result of the independent check: `PERSON_C_REPORT_CODEX.md` (DEGRADED solo fallback, D-001: a second agent, not a second human).
