# Phase 09 statistics contracts (T09.5, T09.6, T09.7, T09.10; independent-implementation pattern)

Status: written 2026-10-11 under D-050. Fixtures: `tests/fixtures/phase09_stats.json`. Every fraction string is exact and was
re-derived with `fractions.Fraction`. The decision rules are those of `STATISTICAL_ANALYSIS_PLAN.md` sections 4-6 and
`PREREGISTRATION.md` sections 8-10; this file adds no new statistical choice except the three readings listed in D-050.

Conventions for every function:
- NumPy randomness comes from `numpy.random.default_rng(seed)` only. No global state, no `np.random.seed`.
- Probabilities and p-values that are compared against a threshold use exact arithmetic on `Fraction(repr(x))`.
- Errors (`ValueError`): empty input, unequal lengths, NaN or infinite value, `iterations` or `permutations` below 1,
  `level` outside (0, 1), `q` outside (0, 1), `alpha` outside (0, 1).

## Resampling primitives (Codex, `statistics/`)

### R1. `bootstrap_indices(n, iterations, seed) -> ndarray[int64]` (`statistics/resampling.py`)
Shape `(iterations, n)`. Equal to `numpy.random.default_rng(seed).integers(0, n, size=(iterations, n))`. One call produces
the index matrix for a whole analysis; every mechanism and every condition of a cohort reuses the same matrix, which is what
makes the comparisons paired (SAP section 4). Fixture: `n=5, iterations=2, seed=0` gives `[[4,3,2,1,1],[0,0,0,0,4]]`.

### R2. `percentile_interval(values, level=0.95) -> (lo, hi)` (`statistics/resampling.py`)
`numpy.percentile(values, [100(1-level)/2, 100(1+level)/2], method="linear")`. Returns Python floats. A single value gives
`(v, v)`. The two percentile positions are computed in exact arithmetic from the decimal text of `level`
(`50 (1 - level)` and `50 (1 + level)` as `Fraction(repr(level))` expressions) and only then converted to float; plain float
evaluation gives `2.500000000000002` at `level = 0.95`, not `2.5`. (Found by Codex while implementing; recorded here.)

### R3. `enrichment_permutation_test(rejected, errors, permutations, seed) -> EnrichmentResult` (`statistics/permutation.py`)
`rejected` and `errors` are 0/1 per patient (1 = rejected / 1 = misclassified). Let `n` patients, `m = sum(rejected)`,
`E = sum(errors)`, `k_obs = sum(errors[rejected == 1])`.
- `observed = k_obs / m - E / n` (error rate among rejected minus overall error rate), the C6 statistic.
- Null: a uniformly random subset of size `m`. With `rng = default_rng(seed)`, permutation `b` uses
  `subset = rng.permutation(n)[:m]` and `k_b = sum(errors[subset])`.
- `p_value = (1 + #{b : k_b >= k_obs}) / (permutations + 1)`; the comparison is on integer counts, never on floats.
- `m == 0` returns `EnrichmentResult(observed=None, p_value=None, n_rejected=0)`; `m == n` is legal (`observed = 0`, `p = 1`).
- `EnrichmentResult` is a frozen dataclass with `observed: float | None`, `p_value: float | None`, `n_rejected: int`.

### R3x. `enrichment_exact_p(rejected, errors) -> Fraction | None` (`statistics/permutation.py`)
The exact one-sided p: `P(K >= k_obs)` with `K ~ Hypergeometric(population n, successes E, draws m)`, as a `Fraction`; `None`
when `m == 0`. Used to check R3: for 10,000 permutations the Monte Carlo p must satisfy
`|p_mc - p_exact| <= 4 sqrt(p_exact (1 - p_exact) / permutations) + 1 / (permutations + 1)`.

### R4. `benjamini_hochberg(p_values, q) -> (adjusted, reject)` (`statistics/multiplicity.py`)
Step-up. With `m` tests, ranks `i = 1..m` by ascending p: `adj_(i) = min over j >= i of (m / j) p_(j)`, capped at 1;
`reject = adj <= q`, compared exactly. `adjusted` is returned as `list[Fraction]`, `reject` as `list[bool]`, both in input
order. Equal p-values share the same adjusted value.

## Claim rules (Claude, `selective/claims.py`, `selective/coverage.py`)

All statuses are one of `"supported"`, `"inconclusive"`, `"refuted"`. Worst-status order: refuted > inconclusive > supported
(`worst_status(statuses)`).

### D1. `status_risk_difference(points, uppers)`: C1, C2, C3
Inputs per grid coverage `phi`: `points[i]` = point estimate of `D(phi)` and `uppers[i]` = upper 95% limit of the paired
bootstrap of `D(phi)`; `D` is selective risk (S2, attained coverage) minus always-predict risk (mean loss).
- refuted if any `points[i] >= 0`;
- else supported if every `uppers[i] < 0`;
- else inconclusive.

### D2. `status_c5(points, lowers)`: C5
Inputs per adjacent pair of grid coverages (higher coverage to the next lower one): `points[k]` = risk at the lower coverage
minus risk at the higher coverage (an increase is positive); `lowers[k]` = lower 95% limit of the paired bootstrap of that
difference.
- refuted if any `lowers[k] > 0` (a significant increase);
- else supported if every `points[k] <= 0` (no observed increase);
- else inconclusive.

### D3. `status_c6(observed, adjusted_p)`: C6
Per grid coverage: `observed[i]` = R3 `observed`, `adjusted_p[i]` = R4 adjusted p over the five grid coverages.
- refuted if any `observed[i] <= 0`;
- else supported if every `adjusted_p[i] < 0.05` (strict);
- else inconclusive.

### D4. `status_c4(lo, hi, band)`: C4
`half_width = (hi - lo) / 2`. `characterized = half_width <= band`. The deviation label:
- `preserved` if `-band <= lo` and `hi <= band`;
- `degraded` if `hi < -band` or `lo > band`;
- `indeterminate` otherwise.
Claim level: refuted when any condition has `characterized == False`, else supported. The same function is called with
`band = 0.07` (primary, D-004) and `band = 0.05` (secondary); only the 0.07 call decides the claim.

### D5. `coverage_deviation_bootstrap(cal_p, cal_labels, test_p, test_labels, alpha, iterations, seed)`: C4, T09.5
Two-stage (SAP section 4). `rng = default_rng(seed)`; per iteration, in this order: draw
`ci = rng.integers(0, n_cal, n_cal)`, refit the split-conformal quantile on `cal_p[ci], cal_labels[ci]`
(`calibration.conformal.conformal_quantile`, exact `ceil((n + 1)(1 - alpha))`), draw `ti = rng.integers(0, n_test, n_test)`,
measure the empirical coverage of the prediction sets on `test_p[ti], test_labels[ti]`. The draw is
`coverage - (1 - alpha)`. Returns the array of `iterations` deviations. Fixture `degenerate_all_confident_correct`: every
draw equals `1/5`.

### D6. `monotonicity_total_bootstrap(scores, losses, iterations, seed)`: T09.6
Per iteration draw `idx = rng.integers(0, n, n)`, build the S1 points of `scores[idx], losses[idx]`, take the S4 magnitude
sum. Returns the array of totals; the report quotes the S4 total on the original data and the R2 interval of the array.

## Cross-check rule

Codex implements R1-R4 from this file alone, without reading the claim code. Claude implements D1-D6 against the R1-R4
signatures. Both sides run every fixture in `phase09_stats.json`. R3 is also checked against R3x on every enrichment fixture
at 10,000 permutations. The BH fixtures and the contributor reference for BH (PR #16) are a third check for R4.
