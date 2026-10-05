# Phase 09 selective-prediction metric contracts (T09.8, independent-implementation pattern)

Status: written 2026-10-05 for D-047 (Phase 09 core metrics built early). Fixtures: `tests/fixtures/phase09_selective.json`
(every number is an exact fraction string, derived by hand and re-derived with `fractions.Fraction`). The conventions are
those of D-033 and PREREGISTRATION.md section 6, and they are the same ones the C-018 contributor reference follows
(`docs/research/contributor_specs/C-018_SELECTIVE_PREDICTION_REFERENCE.md`), so a C-018 reference, when it arrives, checks
the same fixtures. This file does not touch conformal sets (see `PHASE07_METRIC_CONTRACTS.md`, K1-K4).

Conventions for every function:
- `scores`: one number per patient, **higher means more confident and is accepted first**. `losses`: non-negative, 0/1 error
  is the main use. `correct`: 0 or 1.
- Sort by score descending. A **tie block** is a maximal run of exactly equal scores. Ties are never split.
- Comparisons and means use exact rational arithmetic on `Fraction(repr(x))`; the result is rounded to a float once.
- Errors (`ValueError`): empty input, unequal lengths, NaN or infinite score, negative, NaN or infinite loss,
  `target_coverage` outside (0, 1], `correct` not in {0, 1}.

## S1. Risk-coverage points

`rc_points(scores, losses)` returns one `(coverage, risk)` per tie block, at the block's end: coverage = (patients up to and
including the block) / n, risk = mean loss of those patients. Coverage is strictly increasing; the last point has coverage 1
and risk equal to the mean loss.

## S2. Selective risk at a target coverage (T09.4)

`selective_risk_at_coverage(scores, losses, target_coverage)`: the first S1 point whose coverage is **at least** the target
(exact comparison). Returns `(attained_coverage, risk)`. The attained coverage is always reported with the risk.

## S3. AURC (T09.3), two named definitions

- `aurc_mean_over_cutoffs(scores, losses)`: mean over the n cutoffs `k = 1..n` of the risk at cutoff `k`; a cutoff that falls
  inside a tie block takes the risk of that block's end. **This is the pre-registered definition** (D-033).
- `aurc_trapezoid(scores, losses, start_at_zero=False)`: trapezoid area of the S1 points from the first point's coverage to 1;
  with `start_at_zero=True` the point `(0, first risk)` is added first. A curve with a single point has area 0.
- `oracle_aurc(losses)`: `aurc_mean_over_cutoffs` with patients ordered by loss, smallest first. No ordering reaches a lower
  value, so AURC >= `oracle_aurc` always.

## S4. Monotonicity violations (T09.6)

`monotonicity_violations(points)`: over every pair of S1 points `i < j` (so coverage `c_i < c_j`) with `risk_i > risk_j`,
the count of such pairs and the sum of `risk_i - risk_j`. `(0, 0.0)` for a non-decreasing risk sequence. A well-behaved
mechanism has risk that falls as coverage falls, so every such pair is a violation of C5.

## S5. Rejected-but-correct rate (T09.7)

`rejected_but_correct_rate(scores, correct, target_coverage)`: the accepted set is the cases up to the S2 attained coverage;
the rest are rejected. Returns `(fraction of rejected cases with correct == 1, number rejected)`; the fraction is `None` when
nothing is rejected.

## S6. Score conventions per mechanism (T09.1, T07.2, T07.9)

All map to `scores` above (higher = more confident):
- M1 raw and M2 temperature-scaled: `max(p, 1 - p)` of the raw or scaled P(mutant).
- M3 MC-dropout: `-H(mean_t p_t)` with `H(q) = -q ln q - (1 - q) ln (1 - q)` in nats, `0 ln 0 = 0`.
- M4 ensemble: `-Var_m(p_m)`, the population variance (divide by N, not N - 1) of the member probabilities.
- M5 conformal, score-threshold view: `max(p, 1 - p)` of the temperature-scaled P(mutant), i.e. `1 - (nonconformity of the
  predicted label)`. **M1, M2 and M5 therefore rank patients identically** (temperature scaling is monotone in the logit, and
  `max(p, 1 - p) = sigmoid(|z| / T)`), so their risk-coverage curves and AURC are identical up to rounding ties; they differ
  only in operating points and in the set-valued coverage analysis (see D-047).

## Cross-check rule (T09.8)

Claude implements S1, S4, S6 (`selective/risk_coverage.py`, `selective/abstention.py`). Codex implements S2, S3, S5 and the
oracle from this file alone (`selective/aurc.py`, `evaluation/selective_metrics.py`), without reading Claude's code. Both
must reproduce every fixture exactly (to float rounding), and Codex's AURC must equal the mean of the risks implied by
Claude's S1 points on random inputs. The C-018 contributor reference, when delivered, is a third check.
