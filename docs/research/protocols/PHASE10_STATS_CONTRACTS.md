# Phase 10 statistics contracts (T10.3 to T10.6, T10.8; independent-implementation pattern)

Status: written 2026-11-14 under D-052. Fixtures: `tests/fixtures/phase10_stats.json`; every fraction string is exact
(`fractions.Fraction`). This file adds no statistical choice beyond the two recorded in D-052 (the paired-bootstrap p-value
formula and the staging of the Benjamini-Hochberg family). Resampling primitives `bootstrap_indices` and `percentile_interval`
(`PHASE09_STATS_CONTRACTS.md` R1, R2) and `benjamini_hochberg` (R4) already exist and are reused unchanged.

Conventions: NumPy randomness from `numpy.random.default_rng(seed)` only; errors are `ValueError` for empty input, unequal
lengths, NaN or infinite values, labels outside {0, 1}, `iterations` below `min_iterations`, `level` outside (0, 1).

## S1. `delong_paired_auroc(scores_a, scores_b, labels) -> DeLongResult` (`statistics/delong.py`)

Paired comparison of two AUROCs computed on the same patients (DeLong, DeLong and Clarke-Pearson 1988). `labels` is 1 for
IDH-mutant (positive) and 0 for wild type. Let `P` be the positives (`m` of them) and `N` the negatives (`n`), and
`psi(x, y) = 1` if `x > y`, `1/2` if `x = y`, `0` if `x < y`.

- `AUC_k = (1 / (m n)) sum_{i in P} sum_{j in N} psi(s_k[i], s_k[j])` for `k` in `{a, b}` (ties count one half).
- Placement values: `V10_k(i) = (1/n) sum_{j in N} psi(s_k[i], s_k[j])` for `i` in `P`; `V01_k(j) = (1/m) sum_{i in P}
  psi(s_k[i], s_k[j])` for `j` in `N`.
- Covariances with the unbiased denominators: `S10[k,l] = (1/(m-1)) sum_i (V10_k(i) - AUC_k)(V10_l(i) - AUC_l)` and
  `S01[k,l] = (1/(n-1)) sum_j (V01_k(j) - AUC_k)(V01_l(j) - AUC_l)`.
- `Var(AUC_a - AUC_b) = (S10[a,a] + S10[b,b] - 2 S10[a,b]) / m + (S01[a,a] + S01[b,b] - 2 S01[a,b]) / n`.
- `difference = AUC_a - AUC_b`; `z = difference / sqrt(Var)`; two-sided `p_value = erfc(|z| / sqrt(2))`.
- `Var = 0`: `difference = 0` gives `z = 0`, `p_value = 1`; `difference != 0` gives `z = +/-inf`, `p_value = 0`.
- `m < 2` or `n < 2` is a `ValueError` (the covariance needs `m - 1` and `n - 1`).

`DeLongResult` is a frozen dataclass: `auc_a, auc_b, difference, variance, z, p_value` (floats) and `n_positive, n_negative`
(ints). AUROC values and the variance are computed in exact rational arithmetic when the inputs are exact (`Fraction`) and
converted to float last; the fixture strings are the exact values. Swapping `a` and `b` negates `difference` and `z` and
leaves `p_value` unchanged. Identical score vectors give `p_value = 1`. Fixtures: four cases (no ties, with ties, identical
predictors, perfect against inverted with zero variance) in `delong` and the swap check in `delong_swap_check`. Tolerance:
exact for AUC, difference and variance (compare `Fraction(string)` to the float within 1e-15), `1e-12` for `z` and `p_value`.

## S2. `paired_bootstrap_p(differences) -> Fraction` (`statistics/paired.py`)

Two-sided bootstrap p-value from `B = len(differences)` paired bootstrap differences `d_b`. With integer counts
`le = #{b : d_b <= 0}` and `ge = #{b : d_b >= 0}`: `p = min(1, 2 (1 + min(le, ge)) / (B + 1))`, returned as an exact
`Fraction`; the comparisons of `d_b` with 0 are on the exact `Fraction(repr(d_b))`, never on float arithmetic. The `+1` keeps
`p` above zero for a finite number of draws, the same convention as the permutation p (R3). Fixtures: `paired_p_value`.

## S3. `paired_bootstrap(statistic, arrays, iterations, seed, level=0.95, min_iterations=1000) -> PairedBootstrapResult`

`arrays` is a sequence of one-dimensional arrays of equal length `n`, one value per patient (for example the per-patient
confidence scores of two mechanisms plus the labels). `statistic(*arrays) -> float` is evaluated on the original arrays
(`point`) and on each resample. All arrays in one draw use the same row of `bootstrap_indices(n, iterations, seed)`, so a
difference of two mechanisms is paired by construction and a patient is always resampled as a unit (SAP section 4).
- `iterations < min_iterations` raises `ValueError`; a test may lower `min_iterations` explicitly, analysis code never does.
- `values` is the length-`iterations` array of statistic values; `lower, upper = percentile_interval(values, level)`;
  `p_value = paired_bootstrap_p(values)` is meant for a statistic that is itself a difference.
- `PairedBootstrapResult` is a frozen dataclass: `point: float`, `values: ndarray`, `lower: float`, `upper: float`,
  `p_value: Fraction`, `iterations: int`.
Fixture `paired_bootstrap`: `n = 5`, two iterations, seed 0, index matrix `[[4,3,2,1,1],[0,0,0,0,4]]`, statistic
`mean(a) - mean(b)` on `a = [1,2,3,4,5]`, `b = [0,1,1,2,5]`: `point = 6/5`, `values = [6/5, 4/5]` (exact).
Tolerance (resolved 2026-11-14 after Codex's question `CODEX_P10_QUESTIONS.md`): the statistic is evaluated in floating point
(`np.mean(a[row]) - np.mean(b[row])` gives `1.2000000000000002` for the first row), so `point`, `values`, `lower` and `upper`
are compared with the fixture's exact fractions at an absolute tolerance of `1e-12`, relative `0`. The statistic callback is
not changed to chase bit-exactness. `paired_bootstrap_p` stays exact (it takes the `values` as given and compares them with
zero as `Fraction(repr(d))`).

## S4. Phase 10 internal results assembler (`evaluation/phase10_analysis.py`, `scripts/analyze_phase10.py`; T10.9)

Reads frozen artifacts only (no model run) and writes `phase10_analysis.json` with a SHA-256 sidecar into the primary run's
directory, schema `phase10_analysis.v1`. Reuses the patient-aligned per-mechanism scores and 0/1 error vectors that
`evaluation/phase09_analysis.py` already builds for each (condition, mechanism) cell (M1 and M2 raw and temperature-scaled
probability, M3 MC-dropout entropy, M4 ensemble, M5 confidence ranking, which is the M2 ranking by D-047); it does not
re-derive them. Primary run R2; ensemble members R2 to R6, as in Phase 09. Internal data only: UTSW calibration fits, UTSW
internal test (124 patients) scores.

**One resample matrix.** `bootstrap_indices(124, 2000, 0)` is built once and reused by every comparison and every metric
below (SAP section 4, paired by construction). Statistic for every AURC is `aurc_mean_over_cutoffs` (the Phase 09
definition, on the whole cutoff grid), ECE is the 10-bin ECE, Brier is the mean squared error of the probability.

**Confirmatory comparisons that fall inside the pre-registered family and can be computed on UTSW (14 of the 29).** Each
entry gives `point` (difference, first minus second), the 95% percentile interval, the raw two-sided p (`paired_bootstrap_p`,
or the DeLong p where stated), `n = 124`, and the family member id:
- A1 `AURC(M5) - AURC(M3)`, A2 `AURC(M5) - AURC(M4)`, A3 `AURC(M3) - AURC(M4)`, all `full`.
- B1 to B5 `AURC(M5, c) - AURC(M5, full)` for `c` in `drop_t1, drop_t1ce, drop_t2, drop_flair, t1ce_flair_only`.
- D1 `ECE(M1) - ECE(M2)`, D2 `Brier(M1) - Brier(M2)`, `full`. M1 is the raw probability, M2 the temperature-scaled one with
  `T` fitted on the UTSW calibration split (the full-input `T`, as in Phase 09).
- E1 `AUROC(R7) - AUROC(R2)` by `delong_paired_auroc` on the raw logits; E2 `AURC(R7) - AURC(R2)` by paired bootstrap;
  E3 and E4 the same for R8. Raw logits order patients the same as probabilities. When R7 or R8 has no frozen predictions,
  its two entries are written as `{"status": "absent", "reason": "..."}` and nothing else changes.
The family listing `bh_family` has one row per member of the 29 (and the 44 with EGD): id, block, comparison text, cohort,
and `status` in `computed` (the 14 above), `pending_external` (the 15 that need UCSF-PDGM) or `absent`. No adjusted p-value
is written into the confirmatory rows. A separate block `supplementary_bh_internal_only` holds `benjamini_hochberg(p, 0.05)`
over the computed members, with the label `"supplementary; not the pre-registered family (D-052)"`.

**Per-run metric intervals (acceptance criterion 3).** For each of R2, R7, R8 (when present) on the `full` internal test:
AUROC and AUPRC, AURC, selective risk at each grid coverage (the Phase 09 definition), ECE and Brier, each with the point value
and the 2000-draw percentile interval from the shared matrix, plus the Hanley-McNeil 95% AUROC interval beside the bootstrap
one, and the wider is flagged `quoted`. Segmentation Dice is copied from each run's `segmentation_dice.json` (internal test
split, per channel); HD95 is written as `{"status": "absent", "reason": "needs a segmentation freeze (T10.10)"}`.

**Resolved 2026-11-14 (Codex questions on S4).**
1. Per-run block. ECE and Brier are reported twice per run and labelled: from the raw probability (M1) and from the
   temperature-scaled probability (M2, each run's own `T` fitted on its full-input UTSW calibration split). The always-predict
   AUROC and AUPRC use the raw probability (the ranking does not depend on `T`). Per-run AURC and selective risk use the M5
   confidence ranking (the M2 ranking, D-047) with each run's own `T`; the ranking and so the AURC do not depend on `T`, which
   is why E2 and E4 (AURC of R7 or R8 against R2) use the same M5 scores and the Phase 09 error vectors for each run. Sets and
   thresholds are not needed in this assembler.
2. Single-class draws. The shared matrix is not changed and nothing is redrawn or stratified. For every statistic that needs
   both classes (AUROC, AUPRC, and the paired AUROC-difference interval of E1 and E3 if one is reported beside the DeLong p) a
   draw with only one label class is skipped, using one validity mask common to those statistics, and the output records
   `valid_draws` and `skipped_single_class_draws` next to the interval. Statistics that do not need both classes (AURC,
   selective risk, ECE, Brier, and every paired AURC, ECE or Brier difference) keep all draws. The analysis fails with a
   `ValueError` if no valid draw remains. The percentile interval is over the valid draws, whatever their number.

**Tests.** Synthetic frozen artifacts with a known planted difference: the planted comparison has `point` near the planted
value and an interval that covers it, a null comparison has `p` above 0.05 in most seeds, the family listing has 29 rows
(44 with EGD) with exactly 14 `computed` when R7 and R8 exist and 10 when they do not, no row of `bh_family` carries an
adjusted p, the shared-matrix property (two comparisons that use the same two arrays in swapped order give exactly negated
differences and equal p), and a missing-artifact case that fails loudly. The result file's SHA-256 sidecar verifies.

## Tests required

DeLong matches the fixtures and a brute-force O(m n) reference; identical predictors give `p = 1`; swapping the two models
negates `z`. `paired_bootstrap` is reproducible under a fixed seed, enforces `min_iterations`, resamples a patient as a unit
(an array with a duplicated patient row keeps both copies together because the index is shared across arrays), and its
interval covers a known difference at close to the nominal rate on simulated data (100 simulations, `iterations = 1000`,
coverage between 0.90 and 1.00). `paired_bootstrap_p` matches `paired_p_value` exactly. Property: the p-value never exceeds 1
and is monotone in how far the differences sit from zero.

## S5. Segmentation HD95 (T10.10; `evaluation/hd95.py`, `scripts/freeze_segmentation_hd95.py`)

Fixtures: `tests/fixtures/phase10_hd95.json` (expected values from a brute-force pairwise implementation, not from a distance
transform). Conventions chosen under D-053 and the Research Lead's answers of 2026-11-14.

**S5.1 `surface_voxels(mask) -> ndarray[bool]`.** `mask` is a 3-D boolean array. A surface voxel is a foreground voxel with at
least one of its six face neighbours in the background; voxels outside the array count as background (`binary_erosion` with
`generate_binary_structure(3, 1)` and `border_value = 0`; `surface = mask & ~eroded`).

**S5.2 `hd95(pred, truth, spacing=(2.0, 2.0, 2.0)) -> float | None`.** Both masks are boolean arrays of one shape; `spacing` is
the voxel size in mm along each axis. If either mask is empty the result is `None` (undefined). Otherwise, with `A` the surface
voxels of `pred` and `B` those of `truth`: the directed distances of `A` to `B` are, for each voxel of `A`, the Euclidean
distance in mm (spacing applied per axis) to the nearest voxel of `B` (a Euclidean distance transform of the complement of `B`
with `sampling = spacing`); `d95(A -> B)` is their 95th percentile with linear interpolation (`numpy.percentile(..., 95,
method="linear")`); `HD95 = max(d95(A -> B), d95(B -> A))`. This is the BraTS and MONAI convention (the larger of the two directed
95th percentiles, not the 95th percentile of the pooled distances). Symmetric in `pred` and `truth`; 0 for identical masks.
Tolerance against the fixtures: absolute `1e-9` mm.

**S5.3 `classify_case(pred, truth) -> str`.** `"evaluable"` (both non-empty), `"missed"` (truth non-empty, prediction empty),
`"false"` (truth empty, prediction non-empty), `"both_empty"`.

**S5.4 `grid_diagonal_penalty(shape, spacing) -> float`.** `sqrt(sum((n_i s_i)^2))` over axes: 332.5537... mm for `(96, 96, 96)`
at 2 mm (`penalty_mm_96_cube_2mm` in the fixture).

**S5.5 `summarize_hd95(outcomes, penalty) -> dict`.** `outcomes` is a list of `(case, value)` per patient for one channel, with
`case` from S5.3 and `value` the S5.2 result (a float for `evaluable`, `None` otherwise). Two tables, always both, labelled:
- `primary`: over the evaluable cases only: `n_evaluable`, `mean`, `median`, `q25`, `q75` (linear percentiles); `mean` and the
  others are `None` when `n_evaluable = 0`. Beside it the counts `missed`, `false`, `both_empty`, `n_patients`. No distance is
  invented for a non-evaluable case.
- `brats_penalty`: over all patients, `both_empty` = 0 mm, `missed` and `false` = `penalty`; `n`, `mean`, `median`, `q25`, `q75`,
  the `penalty` used, and the label `"BraTS-style penalty convention; the penalty is an arbitrary constant"`.
Fixture `aggregation`: values 10, 20, 30, 40 plus one missed, one false, one both-empty case give `primary` mean 25, median 25,
q25 17.5, q75 32.5 and `brats_penalty` mean `(100 + 2 penalty) / 7` (n = 7).

**S5.6 `scripts/freeze_segmentation_hd95.py --run-id RUN --device {cpu,cuda,auto} [--allow-sha-mismatch]`.** Same provenance
checks, model rebuild (from the run record, `model_config_from_record`), checkpoint load, deterministic mode and dataset
construction as `scripts/freeze_predictions.py` (reuse its helpers). For each of the UTSW calibration and internal-test splits
and each channel (`enhancing`, `necrotic_core`, `oedema`, the order of `freeze.py`): predicted mask = `sigmoid(seg_logit) > 0.5`
(the rule of `training/metrics.hard_dice`), truth = `seg > 0.5`, patients with `has_seg` False excluded and counted, spacing
`(2.0, 2.0, 2.0)` (the preprocessing grid) and the penalty of S5.4. Writes `segmentation_hd95.json` and its `.sha256` sidecar
into the run directory with exclusive creation (an existing file is a `FileExistsError`): per split and channel the S5.5 result,
`n_without_segmentation`, and the per-patient outcomes (`patient_id`, `case`, `value`) so a second person can recompute; plus
`run_id`, `git_sha`, `checkpoint_hash`. A model without a segmentation head is an error. No external cohort is read.

**S5.7 Phase 10 assembler.** `evaluation/phase10_analysis.py` replaces the `hd95` absent marker of a run with the
`internal_test` S5.5 result of that run's `segmentation_hd95.json` when the file exists (sidecar verified), and leaves the
marker when it does not. R7 and R8 are handled the same way.

**Tests.** Every fixture of `phase10_hd95.json`; `surface_voxels` on a single voxel, a 3x3x3 cube (26 surface voxels), a mask
touching the array border; symmetry and identity; a random-mask comparison against a brute-force implementation inside the
test (small grids, 50 random cases, tolerance `1e-9`); `summarize_hd95` on the fixture and on an all-non-evaluable channel
(`None` statistics, counts correct); the penalty value; the script's refusal to overwrite; the assembler picking the file up
and leaving the marker when absent.
