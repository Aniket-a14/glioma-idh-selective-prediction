# C-018 — Selective-prediction metrics: reference implementation and hand-worked fixtures

Assigned to solankisuryansh. Branch `contrib/solankisuryansh/selective-reference`. Read-only for you; the Research Lead
edits this file.

## Why this exists

Phase 09 computes the risk-coverage curve, AURC, selective risk at a matched coverage, the monotonicity violation total
and the rejected-but-correct rate. Phase 09 T09.8 requires an independent cross-check of AURC and the risk-coverage
curve. You are writing that check now, before the real code exists. `DECISION_LOG.md` D-033 explains why some of these
metrics have more than one reasonable definition (read D-033 first): you build each definition as its own named
function and choose none.

Definitions come from SPEC section 1.2 and 4.7 and from the Phase 09 file (`docs/research/phases/PHASE_09_SELECTIVE_PREDICTION_INTERNAL.md`,
T09.6 and T09.7). Read those.

## Files (nothing else may be touched)

- `tests/reference/selective_reference.py` (new): the reference, **Python standard library only**. No numpy, and no
  import from `glioma_selective`.
- `tests/reference/test_selective_reference.py` (new): the tests. Import with `import selective_reference`.
- `tests/reference/fixtures/selective_cases.json` (new): hand-worked cases, each with its arithmetic in a `"working"`
  string.

## Conventions used by every function

`scores`: one number per case, **higher means more confident, accepted first**. `losses`: one non-negative number per
case (0/1 error is the main use). Sort by score, highest first. A **tie block** is a maximal run of exactly equal
scores. Convert every score and loss to `fractions.Fraction(str(x))` internally so that comparisons and means are
exact, and return `float` at the end. `ValueError` for: empty input, unequal lengths, NaN score, negative or NaN loss,
`target_coverage` outside (0, 1]. `correct` values must be 0 or 1.

## Functions

1. `rc_points(scores, losses, ties="block") -> list[tuple[float, float]]`, the risk-coverage points
   `(coverage, risk)`, coverage strictly increasing.
   - `ties="block"`: one point per tie block, at its end: coverage is `(cases up to and including the block) / n`, risk is
     the mean loss of those cases.
   - `ties="input_order"`: ties are ordered by input position (a stable sort); one point per case, `k = 1..n`.
2. `selective_risk_at_coverage(scores, losses, target_coverage) -> tuple[float, float]`: using block ties, the first
   point whose coverage is at least `target_coverage` (compare exactly); return `(attained_coverage, risk)`.
3. `aurc_mean_over_cutoffs(scores, losses, ties="block") -> float`: the mean over the `n` cutoffs `k = 1..n` of the risk
   at cutoff `k`. With `ties="block"` a cutoff inside a tie block takes the risk of that block's end (the nearest
   attainable point that includes the case). With `ties="input_order"` it is the plain mean of the `n` risks.
4. `aurc_trapezoid(scores, losses, start_at_zero=False) -> float`: block points `(c_i, r_i)`; area by the trapezoid rule
   from `c_1` to 1. With `start_at_zero=True`, first add the point `(0, r_1)`.
5. `monotonicity_violations(points) -> tuple[int, float]`: over all pairs `i < j` of points, where `R_i > R_j`: the
   count of such pairs and the sum of `R_i - R_j` (Phase 09 T09.6: `sum max(0, R(phi_i) - R(phi_j))` for
   `phi_i < phi_j`).
6. `rejected_but_correct_rate(scores, correct, target_coverage) -> tuple[float | None, int]`: take the accepted set of
   function 2 (block ties); the rejected cases are the rest; return the fraction of rejected cases with `correct == 1`
   and the number rejected; the rate is `None` when nothing is rejected.
7. `oracle_aurc(losses) -> float`: `aurc_mean_over_cutoffs` when cases are ordered by loss, smallest first, so ties never
   matter; the best AURC any ordering can reach.

## Sanity values to check your work against (checked by the Research Lead)

For `scores = [0.9, 0.8, 0.7, 0.6]`, `losses = [0, 0, 1, 0]`: risks at k = 1..4 are `0, 0, 1/3, 1/4`;
`aurc_mean_over_cutoffs = 7/48 = 0.14583...`; `aurc_trapezoid = 11/96 = 0.11458...` (equal with `start_at_zero=True`,
here); `selective_risk_at_coverage(..., 0.5) = (0.5, 0.0)`; at target 0.6 it is `(0.75, 1/3)`;
`monotonicity_violations` is `(1, 1/12)`; with `correct = [1, 1, 0, 1]` and target 0.5 the rejected-but-correct result is
`(0.5, 2)`.
For `scores = [0.9, 0.9, 0.5]` with `losses = [1, 0, 0]` and again with `losses = [0, 1, 0]`: `ties="block"` gives the same
AURC `4/9` both times, while `ties="input_order"` gives two different numbers. That is the reason D-033 exists.
Derive your own fixtures too; these are only to catch a misread convention early.

## Milestones

The dates are deadlines, not start dates; starting this weekend is fine. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-09-23, open a **draft** pull request) functions 1 and 2, fixtures and tests.
2. (by Thu 2026-09-24) functions 3, 4, 5.
3. (by Fri 2026-09-25, mark ready) functions 6 and 7, the wrong-variant catalogue, the properties, the PR text.

## Tests required

- **Hand-worked fixtures** for every function, including: no ties; a tie block at the top, in the middle and at the
  bottom; all scores equal; one case; all losses 0; all losses 1; a target coverage that falls between two attainable
  points; a target of exactly 1.
- **Two-route check.** Every expected number is derived by hand (in `"working"`) and the test recomputes it a second way
  (inline `Fraction` arithmetic that does not call the reference). Never paste the function's own output as the expected
  value.
- **Wrong-variant catalogue.** In the test file define at least three deliberately wrong versions of each of
  `rc_points`, `aurc_mean_over_cutoffs` and `selective_risk_at_coverage` (examples: ascending sort; dividing by `n - 1`;
  `>` instead of `>=` on the coverage; ignoring ties; risk over the rejected set instead of the accepted set). Assert every
  wrong version disagrees with at least one fixture.
- **Properties:** the last point has coverage 1 and risk equal to the mean loss; coverage strictly increases; risk at
  every point is between the smallest and largest loss; `aurc_mean_over_cutoffs` with `ties="block"` is unchanged by any
  permutation of the input (test 50 seeded shuffles), while `ties="input_order"` is not on tied data; AURC is at least
  `oracle_aurc`; when every case is correct the AURC is 0; a perfectly ranked score (distinct scores, all errors last)
  reaches `oracle_aurc`; `monotonicity_violations` is `(0, 0.0)` for a non-decreasing risk sequence.

## Not allowed

Anything about conformal prediction, prediction sets, nonconformity scores, or the abstention rule of D-003. This task
is the score-threshold curve only. No real data, no file under `data/` or `artifacts/`, no new dependency, no edit
outside the three files above. If a definition looks wrong or ambiguous, do not fix it: list it under "Open questions"
in the pull request and implement it exactly as written.

## Pull request text must contain

Each function and what each fixture proves; for each wrong variant, the fixture that catches it; the commands you ran and
their output; the Open questions section (write "none" only if there are none).
