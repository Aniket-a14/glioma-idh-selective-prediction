"""Independent tests for the C-022 multiple-testing reference."""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path

import bh_reference
import pytest

FIXTURES = json.loads(
    Path(__file__)
    .with_name("fixtures")
    .joinpath("bh_cases.json")
    .read_text(encoding="utf-8")
)


def _fractions(values: list[float]) -> list[Fraction]:
    return [Fraction(str(value)) for value in values]


def _independent_bh(values: list[float]) -> list[float]:
    exact = _fractions(values)
    ranked = sorted(enumerate(exact), key=lambda item: item[1])
    count = len(ranked)
    output = [Fraction(0) for _ in values]
    for position, (original_index, _) in enumerate(ranked):
        output[original_index] = min(
            [
                min(Fraction(1), ranked[later][1] * count / (later + 1))
                for later in range(position, count)
            ]
        )
    return [float(value) for value in output]


def _independent_reject(values: list[float], q: float) -> list[bool]:
    exact = _fractions(values)
    exact_q = Fraction(str(q))
    ranked = sorted(enumerate(exact), key=lambda item: item[1])
    largest = max(
        (
            position
            for position, (_, value) in enumerate(ranked, start=1)
            if value * len(values) <= position * exact_q
        ),
        default=0,
    )
    ranks = {
        original_index: position
        for position, (original_index, _) in enumerate(ranked, start=1)
    }
    return [ranks[index] <= largest for index in range(len(values))]


def _independent_holm(values: list[float]) -> list[float]:
    exact = _fractions(values)
    ranked = sorted(enumerate(exact), key=lambda item: item[1])
    count = len(ranked)
    output = [Fraction(0) for _ in values]
    for position, (original_index, _) in enumerate(ranked):
        output[original_index] = min(
            Fraction(1),
            max(
                (count - earlier + 1) * ranked[earlier - 1][1]
                for earlier in range(1, position + 2)
            ),
        )
    return [float(value) for value in output]


@pytest.mark.parametrize("case", FIXTURES, ids=[case["name"] for case in FIXTURES])
def test_hand_worked_fixtures_have_two_independent_routes(
    case: dict[str, object],
) -> None:
    p_values = case["p_values"]
    q = case["q"]
    expected_bh = case["expected_bh"]
    expected_reject = case["expected_reject"]
    expected_holm = case["expected_holm"]

    assert bh_reference.bh_adjusted(p_values) == pytest.approx(expected_bh)
    assert _independent_bh(p_values) == pytest.approx(expected_bh)
    assert bh_reference.bh_reject(p_values, q) == expected_reject
    assert _independent_reject(p_values, q) == expected_reject
    assert bh_reference.holm_adjusted(p_values) == pytest.approx(expected_holm)
    assert _independent_holm(p_values) == pytest.approx(expected_holm)


def test_contract_sanity_values() -> None:
    assert bh_reference.bh_adjusted([0.01, 0.04, 0.03, 0.005]) == pytest.approx(
        [0.02, 0.04, 0.04, 0.02]
    )
    assert bh_reference.holm_adjusted([0.01, 0.04, 0.03, 0.005]) == pytest.approx(
        [0.03, 0.06, 0.06, 0.02]
    )
    assert bh_reference.bh_adjusted([0.04, 0.01, 0.03]) == pytest.approx(
        [0.04, 0.03, 0.04]
    )
    assert bh_reference.bh_adjusted([0.2, 0.2, 0.2]) == pytest.approx([0.2, 0.2, 0.2])
    assert bh_reference.bh_adjusted([0.5]) == pytest.approx([0.5])


def test_wrong_variant_catalogue_is_caught() -> None:
    binding = next(case for case in FIXTURES if case["name"] == "running_minimum_binds")
    tie = next(case for case in FIXTURES if case["name"] == "ties_at_step_boundary")
    equality = next(
        case for case in FIXTURES if case["name"] == "exact_equality_boundary"
    )

    def wrong_no_running_minimum(values: list[float]) -> list[float]:
        exact = _fractions(values)
        ranked = sorted(enumerate(exact), key=lambda item: item[1])
        count = len(ranked)
        output = [Fraction(0) for _ in values]
        for position, (original_index, value) in enumerate(ranked, start=1):
            output[original_index] = min(Fraction(1), value * count / position)
        return [float(value) for value in output]

    def wrong_ascending_running_minimum(values: list[float]) -> list[float]:
        exact = _fractions(values)
        ranked = sorted(enumerate(exact), key=lambda item: item[1])
        count = len(ranked)
        running = Fraction(1)
        output = [Fraction(0) for _ in values]
        for position, (original_index, value) in enumerate(ranked, start=1):
            running = min(running, value * count / position)
            output[original_index] = min(Fraction(1), running)
        return [float(value) for value in output]

    def wrong_m_instead_of_rank(values: list[float]) -> list[float]:
        exact = _fractions(values)
        count = len(exact)
        # This deliberately uses m/m instead of the rank-specific m/k.
        return [float(value * count / count) for value in exact]

    def wrong_divide_by_m_minus_k(values: list[float]) -> list[float]:
        exact = _fractions(values)
        ranked = sorted(enumerate(exact), key=lambda item: item[1])
        count = len(ranked)
        output = [Fraction(0) for _ in values]
        for position, (original_index, value) in enumerate(ranked, start=1):
            denominator = count - position or 1
            output[original_index] = min(Fraction(1), value * count / denominator)
        return [float(value) for value in output]

    assert wrong_no_running_minimum(binding["p_values"]) != binding["expected_bh"]
    assert wrong_no_running_minimum(tie["p_values"]) != tie["expected_bh"]
    assert (
        wrong_ascending_running_minimum(binding["p_values"]) != binding["expected_bh"]
    )
    assert wrong_m_instead_of_rank(binding["p_values"]) != binding["expected_bh"]
    assert wrong_divide_by_m_minus_k(binding["p_values"]) != binding["expected_bh"]
    assert bh_reference.holm_adjusted(binding["p_values"]) != binding["expected_bh"]

    def wrong_strict_reject(values: list[float], q: float) -> list[bool]:
        exact = _fractions(values)
        exact_q = Fraction(str(q))
        ranked = sorted(enumerate(exact), key=lambda item: item[1])
        largest = max(
            (
                position
                for position, (_, value) in enumerate(ranked, start=1)
                if value * len(values) < position * exact_q
            ),
            default=0,
        )
        ranks = {
            original_index: position
            for position, (original_index, _) in enumerate(ranked, start=1)
        }
        return [ranks[index] <= largest for index in range(len(values))]

    assert (
        wrong_strict_reject(equality["p_values"], equality["q"])
        != equality["expected_reject"]
    )
    assert bh_reference.bh_adjusted(tie["p_values"]) == pytest.approx(
        tie["expected_bh"]
    )


def test_properties_over_250_fixed_seed_random_lists() -> None:
    randomizer = random.Random(220)
    for _ in range(250):
        length = randomizer.randint(1, 30)
        p_values = [randomizer.random() for _ in range(length)]
        q = 0.01 + 0.98 * randomizer.random()
        adjusted = bh_reference.bh_adjusted(p_values)
        assert all(0.0 <= value <= 1.0 for value in adjusted)
        assert all(
            value + 1e-15 >= p_value
            for value, p_value in zip(adjusted, p_values, strict=False)
        )
        for left, left_value in enumerate(p_values):
            for right, right_value in enumerate(p_values):
                if left_value <= right_value:
                    assert adjusted[left] <= adjusted[right] + 1e-15

        permutation = list(range(length))
        randomizer.shuffle(permutation)
        permuted = [p_values[index] for index in permutation]
        permuted_adjusted = bh_reference.bh_adjusted(permuted)
        assert permuted_adjusted == pytest.approx(
            [adjusted[index] for index in permutation]
        )

        assert bh_reference.bh_reject(p_values, q) == [value <= q for value in adjusted]
        holm_reject = [value <= q for value in bh_reference.holm_adjusted(p_values)]
        bh_reject = bh_reference.bh_reject(p_values, q)
        assert all(
            not holm or bh for holm, bh in zip(holm_reject, bh_reject, strict=False)
        )


@pytest.mark.parametrize(
    "call",
    [
        lambda: bh_reference.bh_adjusted([]),
        lambda: bh_reference.bh_adjusted([1.2]),
        lambda: bh_reference.bh_adjusted([-0.1]),
        lambda: bh_reference.bh_adjusted([float("nan")]),
        lambda: bh_reference.bh_reject([0.1], 0),
        lambda: bh_reference.bh_reject([0.1], 1.5),
        lambda: bh_reference.holm_adjusted([]),
    ],
)
def test_invalid_inputs_raise_value_error(call) -> None:
    with pytest.raises(ValueError):
        call()
