"""Hand-calculated checks of the standalone metric functions in the Person C pack."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
from scripts import person_c_recompute as pc


def test_aurc_and_selective_risk_with_a_tie_block() -> None:
    scores = np.array([0.9, 0.8, 0.7, 0.7])
    losses = np.array([0.0, 1.0, 0.0, 1.0])
    # risk at the tie-block ends: 0, 1/2, 1/2; cutoffs 1..4 take 0, 1/2, 1/2, 1/2
    assert pc.aurc(scores, losses) == 0.375
    assert pc.selective_risk(scores, losses, 0.5) == (0.5, 0.5)
    assert pc.selective_risk(scores, losses, 0.75) == (1.0, 0.5)


def test_auroc_counts_ties_as_half_and_average_precision_groups_ties() -> None:
    scores = np.array([0.9, 0.8, 0.3, 0.8])
    labels = np.array([1, 1, 0, 0])
    assert pc.auroc(scores, labels) == 0.875
    # thresholds 0.9 (tp 1/1), 0.8 (tp 2 of 3): recall steps 1/2 and 1/2
    assert pc.average_precision(scores, labels) == 0.5 * 1.0 + 0.5 * (2 / 3)


def test_paired_p_is_exact_and_capped_at_one() -> None:
    draws = np.array([0.0, 1.0, -1.0, 2.0])
    assert pc.paired_p(draws) == Fraction(1)
    assert pc.paired_p(np.ones(9)) == Fraction(2 * (1 + 0), 10)


def test_temperature_is_one_for_calibrated_logits_and_delong_identical_is_one() -> None:
    logits = np.array([-2.0, -1.0, 1.0, 2.0] * 50)
    labels = np.array([0, 0, 1, 1] * 50)
    assert pc.fit_temperature(logits, labels) < 1.0  # perfectly separated: sharpen
    scores = np.array([0.1, 0.4, 0.35, 0.8, 0.7, 0.2])
    y = np.array([0, 0, 1, 1, 1, 0])
    diff, p = pc.delong_p(scores, scores, y)
    assert diff == 0.0 and p == 1.0


def test_exact_bin_index_puts_one_in_the_last_bin() -> None:
    bins = pc._bins(np.array([0.0, 0.1, 0.3, 0.7, 0.99, 1.0]))
    assert bins.tolist() == [0, 1, 3, 7, 9, 9]
