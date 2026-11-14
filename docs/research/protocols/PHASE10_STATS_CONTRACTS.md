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
