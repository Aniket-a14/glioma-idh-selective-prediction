# C-017 — Calibration metrics: reference implementation and hand-worked fixtures

Assigned to Akshita1395. Branch `contrib/Akshita1395/calibration-reference`. Read-only for you; the Research Lead
edits this file.

## Why this exists

Phase 07 will compute Brier, ECE and a conformal quantile. Phase 07 T07.10 requires each to be checked against an
independent implementation, because a wrong binning rule or an off-by-one quantile gives plausible-looking numbers that
are simply incorrect. You are writing that independent check now, before the real code exists, so the real code has
something to be tested against. `DECISION_LOG.md` D-033 explains why several ECE variants are built (read D-033 first).
You choose nothing: every variant is its own named function.

## Files (nothing else may be touched)

- `tests/reference/calibration_reference.py` (new): the reference functions, **Python standard library only**. Do not
  import numpy, and do not import anything from `glioma_selective`. The point is that it shares no code and no
  mental model with the real implementation.
- `tests/reference/test_calibration_reference.py` (new): the tests. Import the reference with
  `import calibration_reference` (pytest puts this folder on the path; no package `__init__`).
- `tests/reference/fixtures/calibration_cases.json` (new): the hand-worked cases, each with its worked arithmetic
  written out in a `"working"` string.

## Functions

All inputs are plain lists. `probs` are predicted probabilities of class 1 (IDH-mutant), `labels` are 0 or 1.
Raise `ValueError` for: empty input, unequal lengths, a probability outside [0, 1] or NaN, a label not in {0, 1},
`n_bins < 1`, an unknown scheme.

1. `brier_score(probs, labels) -> float`: mean of `(p - y)^2`.
2. `reliability_bins(probs, labels, n_bins, scheme="equal_width", right_closed=False, variant="positive_class")`
   returns a list of `n_bins` dicts with keys `lower`, `upper`, `count`, `mean_confidence`, `observed`.
   - `variant="positive_class"`: score is `p`; `observed` is the fraction of labels equal to 1 in the bin;
     `mean_confidence` is the mean `p`.
   - `variant="top_label"`: score is `max(p, 1 - p)`; the predicted label is 1 if `p > 0.5` else 0 (`p == 0.5`
     predicts 0); `observed` is the fraction of bin members whose predicted label equals the true label;
     `mean_confidence` is the mean score.
   - `scheme="equal_width"`: bins split [0, 1] into `n_bins` equal parts. With `right_closed=False` a bin is
     `[lo, hi)` and the last bin is `[lo, 1]`. With `right_closed=True` a bin is `(lo, hi]` and the first bin is
     `[0, hi]`. Use exact arithmetic for the edges (multiply and compare with `fractions.Fraction` built from
     `str(value)`) so a value such as 0.3 with 10 bins lands where a person would say it does.
   - `scheme="equal_mass"`: sort by score (stable, ties keep input order), cut into `n_bins` consecutive groups whose
     sizes are `n // n_bins`, plus one extra for each of the first `n % n_bins` groups. `lower` and `upper` are the
     smallest and largest score in the group. `right_closed` is ignored. Empty groups (when `n < n_bins`) report
     `count` 0 and `None` for the other four keys.
   - Empty bins in `equal_width` report `count` 0 and `None` for `mean_confidence` and `observed`.
3. `ece(probs, labels, n_bins, scheme="equal_width", right_closed=False, variant="positive_class") -> float`:
   sum over non-empty bins of `(count / n) * abs(observed - mean_confidence)`.
4. `mce(...)` with the same arguments: the largest `abs(observed - mean_confidence)` over non-empty bins.
5. `conformal_rank(n, alpha) -> int`: `ceil((n + 1) * (1 - alpha))`. **`alpha` must be exact**: accept an `int`,
   `str` or `Fraction`, and a float only by converting through `Fraction(str(alpha))`. Reason: in floating point,
   `(9 + 1) * (1 - 0.7)` is `3.0000000000000004`, `ceil` gives 4, and the exact answer is 3 (checked by the Research
   Lead; `n = 19, alpha = 0.85` gives 4 against 3 as well). It does not go wrong for alpha 0.05, 0.1 or 0.2 up to
   n = 5000, so the tests must also include one of the failing cases above and show a naive float version fails it.
6. `conformal_quantile(scores, alpha) -> float`: the `k`-th smallest score with `k = conformal_rank(n, alpha)`, or
   `math.inf` when `k > n`. `ValueError` for empty scores, NaN scores, alpha not in (0, 1). This is the order
   statistic only. Do **not** define a nonconformity score, prediction sets or an abstention rule: D-002 and D-003
   are open.

## Milestones

The dates are deadlines, not start dates; starting this weekend is fine. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-09-23, open a **draft** pull request) `brier_score`, `conformal_rank`, `conformal_quantile`, with
   fixtures and tests.
2. (by Thu 2026-09-24) `reliability_bins`, `ece`, `mce` with fixtures and tests.
3. (by Fri 2026-09-25, mark the pull request ready) the wrong-variant catalogue, the property tests and the PR text.

## Tests required

- **Hand-worked fixtures.** At least: Brier on 4 points; an 8-sample toy ECE for each `variant`; a 10-point conformal
  set with alpha 0.1 and alpha 0.2 (hand-derive the rank and the quantile in `"working"`); values that sit exactly on a
  bin edge, showing `right_closed` False and True give different bins; an `equal_mass` case with `n % n_bins != 0`;
  a case with tied scores in `equal_mass`.
- **Two-route check.** For every hand-worked number, the fixture stores the value you derived by hand, and the test
  recomputes it a second way (for example `fractions.Fraction` arithmetic written inline in the test, not by calling the
  reference) and asserts both routes agree. An agent must not derive the expected value by running the function and
  pasting the output.
- **Wrong-variant catalogue.** In the test file, define at least three deliberately wrong versions of each of
  `brier_score`, `ece` and `conformal_quantile` (examples: `(p - y)` without the square; bins weighted equally instead
  of by count; `ceil(n * (1 - alpha))` without the `+1`; `floor` instead of `ceil`; right-closed and left-closed
  swapped). Assert that every wrong version disagrees with at least one fixture, so a test that cannot tell right from
  wrong is caught.
- **Properties:** Brier in [0, 1], and 0 for perfect 0/1 predictions, and 0.25 for constant 0.5; ECE and MCE in [0, 1];
  the bin counts sum to `n`; ECE unchanged when the samples are shuffled (equal_width); a constructed perfectly
  calibrated set gives ECE 0; the rank never exceeds `n + 1`; the quantile is one of the input scores or `inf`;
  every `ValueError` case above.

## Not allowed

Any real data, any file under `data/` or `artifacts/`, any import from `glioma_selective`, any new dependency, any edit
to a file outside the three above. If a definition here looks wrong or ambiguous, do not fix it: write it under "Open
questions" in the pull request and implement it exactly as written.

## Pull request text must contain

The list of functions and what each fixture proves; for each wrong variant, which fixture catches it; the commands you
ran and their output; the Open questions section (write "none" only if there are none).
