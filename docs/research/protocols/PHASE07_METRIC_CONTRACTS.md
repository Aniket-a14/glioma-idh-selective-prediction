# Phase 07 metric contracts (T07.10, independent-implementation pattern)

Status: written 2026-10-05 for D-045 (Phase 07 pull-forward). Fixtures: `tests/fixtures/phase07_contracts.json`.
Every formula below has a hand-calculated fixture. An implementation is correct when it reproduces the fixtures; where two
implementations (Claude and Codex) both do, they must also agree on randomized inputs to 1e-12.

Conventions used by every function:
- `p_hat` is P(IDH-mutant), a probability in [0, 1]. Label 1 = mutant, 0 = wild-type.
- Inputs are validated: non-empty, equal lengths, finite, probabilities in [0, 1], labels in {0, 1}, alpha in (0, 1).
  Anything else raises `ValueError`.
- Comparisons that decide an index or a threshold use **exact rational arithmetic**: interpret each float with
  `Fraction(repr(x))` (the shortest decimal string), never `x * n` in floating point.
- Fitting happens on the calibration split only. These functions never see the internal test split or external data.

## K1. Nonconformity score (M5)

`nonconformity_score(p_hat, label) = 1 - p_hat` if `label == 1` else `p_hat`. This is `1 - p(true class)`, the
least-ambiguous-classifier score for two classes. `p_hat` is the temperature-scaled probability (K5), D-045.

## K2. Conformal quantile with the n+1 correction

`conformal_quantile(scores, alpha)`: let `n = len(scores)`, `k = ceil((n + 1) * (1 - alpha))`, computed exactly.
If `k > n`, return `+inf` (the set is every label; the guarantee still holds). Otherwise return the `k`-th smallest score
(1-indexed, ties allowed). It returns an element of `scores` or `+inf`, never an interpolation.

## K3. Prediction set, abstention, coverage

Given `q = conformal_quantile(...)`:
- class 1 is in the set iff `1 - p_hat <= q`; class 0 is in the set iff `p_hat <= q` (both `<=`, matching K2). The left side is
  the K1 score of that label, computed exactly and rounded once to a double, so a calibration point is always inside the set
  built from a quantile equal to its own score. Where the exact decimal value of a score and its rounded double differ by
  less than one ulp, the two readings can disagree for a point that sits exactly on `q`; the T07.10 cross-check found no
  such case on about 58,000 random and grid set comparisons (10,201 on the 0.01 decimal grid, 48,000 random).
- `prediction_set(p_hat, q)` returns a sorted tuple: `()`, `(0,)`, `(1,)` or `(0, 1)`.
- The predictor **abstains iff the set is not a singleton** (D-003). An empty set is an abstention, reported separately.
- `empirical_coverage(sets, labels)` = fraction of patients whose true label is in their set.
- `conformal_summary(sets, labels)` returns `coverage`, `abstention_rate` (set size != 1), `empty_rate`, `full_rate` (set size 2).
  Rates are over all patients, as plain floats.

## K4. Conformal risk control (named secondary, D-002)

Loss for one patient at confidence threshold `tau`, with `c = max(p_hat, 1 - p_hat)` and `y_hat = 1 if p_hat >= 0.5 else 0`:
`loss(tau) = 1 if (c >= tau and y_hat != y) else 0`. It is bounded by `B = 1` and non-increasing in `tau`.
This is the rate of accepted errors, `P(accept and wrong)`, not the conditional selective risk. CRC controls the first and
the study reports the realized selective risk beside it (D-045).

`crc_threshold(p_hat, labels, alpha)` returns `tau_hat`:
- candidates = the sorted unique confidences of the calibration set, plus `+inf`;
- `R(tau) = (1/n) * sum_i loss_i(tau)`;
- `tau_hat` = the smallest candidate with `(n/(n+1)) * R(tau) + 1/(n+1) <= alpha`, evaluated exactly (equality passes);
- if no candidate satisfies it, return `+inf` (reject everything).
A patient is accepted iff `c >= tau_hat`.

## K5. Temperature scaling (M2)

`fit_temperature(logits, labels)` finds `w = 1/T` minimizing the mean binary cross-entropy of `sigmoid(w * z_i)` on the
calibration split. The objective is convex in `w`, so the minimum is unique unless the data are separable. Search
`T` in `[0.05, 20]`; if the unconstrained optimum lies outside, return the nearer bound. Return `T`. Tolerance 1e-6 on `T`.
`apply_temperature(logits, T)` returns `sigmoid(logits / T)`. T must be positive.

## K6. Brier score

`brier_score(p_hat, labels) = mean((p_hat - y)^2)`.

## K7. Expected calibration error and reliability bins

Pre-registered convention (PREREGISTRATION.md section 6): positive-class ECE on `p_hat`, 10 equal-width bins, left-closed
`[a, b)`, with `1.0` in the last bin. Bin index = `min(floor(10 * p_hat), 9)`, computed exactly.
`ECE = sum_b (n_b / n) * |mean(y in b) - mean(p_hat in b)|` over non-empty bins.
`reliability_bins(p_hat, labels, n_bins=10)` returns for every bin (including empty ones) `count`, `mean_p`, `frac_pos`;
empty bins have `mean_p = frac_pos = None`.
Sensitivity variants (5 and 15 bins, equal-mass 10 bins) are out of scope for this contract; `n_bins` is a parameter.

## Cross-check rule (T07.10)

Claude implements K1-K4 in `src/glioma_selective/calibration/` from this file. Codex implements K1-K3 independently from
this file in `tests/reference/conformal_reference.py` (standard library only, no project imports), and implements K5-K7
as the production code in `src/glioma_selective/calibration/temperature.py` and
`src/glioma_selective/evaluation/calibration_metrics.py`. The existing C-017 reference (`tests/reference/calibration_reference.py`)
is a third, contributor-written check of K6 and K7. Disagreement beyond 1e-12 on any shared input is investigated and recorded
in the decision log before either side merges.
