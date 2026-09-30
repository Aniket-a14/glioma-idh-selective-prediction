# C-022 — Benjamini-Hochberg correction: reference implementation and hand-worked fixtures

Assigned to Akshita1395. Branch `contrib/Akshita1395/bh-reference`. Read-only for you; the Research Lead edits this file.

## Why this exists

The frozen statistical analysis plan (`docs/research/protocols/STATISTICAL_ANALYSIS_PLAN.md`, section 6) controls the
false discovery rate over one family of confirmatory comparisons with the Benjamini-Hochberg procedure at q = 0.05. The
real implementation arrives in Phase 10. This row builds the independent check first, from the definition below, without
reading any code in this repository. Read section 6 of the plan for the context only.

## Files (nothing else may be touched)

- `tests/reference/bh_reference.py` (new): the reference, **Python standard library only**. No numpy, and no import from
  `glioma_selective`.
- `tests/reference/test_bh_reference.py` (new): the tests. Import with `import bh_reference`.
- `tests/reference/fixtures/bh_cases.json` (new): hand-worked cases, each with its arithmetic in a `"working"` string.

If `tests/reference/` already holds files from another row (for example C-017), add yours next to them; do not edit theirs.

## Conventions

`p_values`: a list of numbers in [0, 1]. Convert each to `fractions.Fraction(str(x))` internally so comparisons are exact,
and return `float` at the end. `ValueError` for: empty input, any value outside [0, 1], NaN, `q` outside (0, 1].
Results are returned **in the input order**, not sorted.

## Functions

1. `bh_adjusted(p_values) -> list[float]`: the BH adjusted p-values (q-values). With `m` values, ranks `k = 1..m` in
   ascending order of p (ties get consecutive ranks in input order), the raw step value is `p_(k) * m / k`; the adjusted
   value at rank `k` is the minimum of the raw step values over ranks `k..m` (a running minimum from the largest rank
   down), capped at 1.
2. `bh_reject(p_values, q) -> list[bool]`: the step-up rule. Find the largest rank `k` with `p_(k) <= k * q / m`; reject
   every hypothesis with rank `<= k`; reject none if no such `k` exists. It must agree with `bh_adjusted(...) <= q`
   for every input (a property test, and the reason to build both).
3. `holm_adjusted(p_values) -> list[float]`: Holm step-down adjusted p-values, `max over ranks <= k of (m - rank + 1) * p`,
   capped at 1. This is **not** used by the project. It is here only as the wrong-variant catalogue entry: a test must
   show that BH and Holm differ on at least one fixture, so a mix-up in the real code cannot pass.

## Sanity values to check your work against (checked by the Research Lead)

- `bh_adjusted([0.01, 0.04, 0.03, 0.005])` is `[0.02, 0.04, 0.04, 0.02]`; `holm_adjusted` of the same list is
  `[0.03, 0.06, 0.06, 0.02]`.
- `bh_adjusted([0.04, 0.01, 0.03])` is `[0.04, 0.03, 0.04]`.
- `bh_adjusted([0.2, 0.2, 0.2])` is `[0.2, 0.2, 0.2]`, and `bh_adjusted([0.5])` is `[0.5]`.
- The 15 p-values of Benjamini and Hochberg's 1995 example, `0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298,
  0.0344, 0.0459, 0.3240, 0.4262, 0.5719, 0.6528, 0.7590, 1.000`, give adjusted values beginning `0.0015, 0.003, 0.0095,
  0.035625, 0.0603, 0.063857...` and `bh_reject(..., 0.05)` rejects exactly the first four.
Derive your own fixtures too; these are only to catch a misread convention early.

## Milestones

The dates are deadlines, not start dates. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-10-07, open a **draft** pull request) functions 1 and 2, fixtures and tests.
2. (by Fri 2026-10-09, mark ready) function 3, the wrong-variant catalogue, the properties, the PR text.

## Tests required

- **Hand-worked fixtures** for both functions: one hypothesis; all p equal; already sorted; reverse sorted; ties at a
  step boundary; a p of exactly 0 and exactly 1; the running minimum actually binding (the adjusted value of a lower
  rank is pulled down by a higher rank); a case where the cap at 1 binds; a case where `p_(k) == k * q / m` exactly
  (equality rejects).
- **Two-route check.** Every expected number is derived by hand (in `"working"`) and the test recomputes it a second way
  (for example, brute force over every rank for the reject rule).
- **Properties** (fixed seed, at least 200 random lists of length 1 to 30, drawn with the standard library `random`):
  adjusted values are in [0, 1]; adjusted >= raw p; order-preserving (`p_i <= p_j` implies `adj_i <= adj_j`); permuting
  the input permutes the output the same way; `bh_reject` equals `bh_adjusted <= q`; BH rejects a superset of what
  Holm rejects at the same q.
- **Invalid input** raises `ValueError`: empty list, a value of 1.2 or -0.1, NaN, `q` of 0 and of 1.5.
- **Wrong-variant catalogue.** Write each of these as a deliberately wrong function inside the test file, and show that
  at least one fixture makes each one fail: no running minimum; running minimum taken in ascending order; using `m`
  where `k` belongs; dividing by `m - k`; Holm in place of BH; comparing `<` where `<=` is required.

## Pull request

State the file list, the number of fixtures, and list each deliberate break from the catalogue with the fixture that
catches it. Do not edit any file outside the three above. If your reference and a fixture disagree, the fixture's
`"working"` is wrong or your code is wrong: say which, do not adjust either to fit.
