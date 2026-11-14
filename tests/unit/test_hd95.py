"""S5 fixture checks and an independent face-neighbour/pairwise oracle."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from glioma_selective.evaluation.hd95 import (
    classify_case,
    grid_diagonal_penalty,
    hd95,
    summarize_hd95,
    surface_voxels,
)

FIXTURE = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase10_hd95.json").read_text()
)


def _mask(shape: list[int], voxels: list[list[int]]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    for voxel in voxels:
        mask[tuple(voxel)] = True
    return mask


def _brute_surface(mask: np.ndarray) -> np.ndarray:
    points = []
    for point in np.argwhere(mask):
        for axis, direction in itertools.product(range(3), (-1, 1)):
            neighbour = point.copy()
            neighbour[axis] += direction
            if (
                neighbour[axis] < 0
                or neighbour[axis] >= mask.shape[axis]
                or not mask[tuple(neighbour)]
            ):
                points.append(point)
                break
    return np.asarray(points)


@pytest.mark.parametrize("fixture", FIXTURE["hd95"], ids=lambda f: f["name"])
def test_every_distance_fixture(fixture: dict[str, Any]) -> None:
    pred = _mask(fixture["shape"], fixture["pred_voxels"])
    truth = _mask(fixture["shape"], fixture["truth_voxels"])
    result = hd95(pred, truth, fixture["spacing"])
    reverse = hd95(truth, pred, fixture["spacing"])
    if fixture["expected"] is None:
        assert result is reverse is None
    else:
        assert result == pytest.approx(fixture["expected"], abs=1e-9, rel=0)
        assert reverse == pytest.approx(result, abs=1e-9, rel=0)


@pytest.mark.parametrize("border", [False, True])
def test_cube_surface_and_array_border(border: bool) -> None:
    mask = np.ones((3, 3, 3), dtype=bool) if border else np.zeros((5, 5, 5), dtype=bool)
    if not border:
        mask[1:4, 1:4, 1:4] = True
    surface = surface_voxels(mask)
    assert surface.dtype == np.bool_
    assert surface.sum() == 26
    assert not surface[tuple(n // 2 for n in mask.shape)]
    assert np.array_equal(np.argwhere(surface), _brute_surface(mask))
    assert hd95(mask, mask) == 0.0


def test_single_surface_voxel_and_six_neighbours() -> None:
    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[1, 1, 1] = True
    assert np.array_equal(surface_voxels(mask), mask)
    # Only face neighbours erode the centre; background diagonals do not.
    for axis, direction in itertools.product(range(3), (-1, 1)):
        neighbour = [1, 1, 1]
        neighbour[axis] += direction
        mask[tuple(neighbour)] = True
    assert not surface_voxels(mask)[1, 1, 1]


def test_fifty_random_masks_against_independent_brute_force() -> None:
    rng = np.random.default_rng(105)
    for _ in range(50):
        shape = tuple(rng.integers(2, 7, size=3))
        pred = rng.random(shape) < rng.uniform(0.1, 0.9)
        truth = rng.random(shape) < rng.uniform(0.1, 0.9)
        spacing = rng.uniform(0.5, 4, size=3)
        a, b = _brute_surface(pred), _brute_surface(truth)
        if not len(a) or not len(b):
            assert hd95(pred, truth, spacing) is None
            continue
        distances = np.sqrt((((a[:, None] - b[None, :]) * spacing) ** 2).sum(axis=2))
        expected = max(
            np.percentile(distances.min(axis=1), 95, method="linear"),
            np.percentile(distances.min(axis=0), 95, method="linear"),
        )
        assert hd95(pred, truth, spacing) == pytest.approx(expected, abs=1e-9, rel=0)
        assert hd95(truth, pred, spacing) == pytest.approx(expected, abs=1e-9, rel=0)
        assert hd95(pred, pred, spacing) == 0.0


@pytest.mark.parametrize(
    ("p", "t", "case"),
    [
        (True, True, "evaluable"),
        (False, True, "missed"),
        (True, False, "false"),
        (False, False, "both_empty"),
    ],
)
def test_classification(p: bool, t: bool, case: str) -> None:
    assert classify_case(np.full((1, 1, 1), p), np.full((1, 1, 1), t)) == case


def test_penalty_and_aggregation_fixture() -> None:
    penalty = grid_diagonal_penalty((96, 96, 96), (2, 2, 2))
    assert penalty == pytest.approx(FIXTURE["penalty_mm_96_cube_2mm"], abs=1e-9, rel=0)
    aggregation = FIXTURE["aggregation"]
    outcomes = [("evaluable", value) for value in aggregation["values"]]
    outcomes += [(case, None) for case in ("missed", "false", "both_empty")]
    result = summarize_hd95(outcomes, penalty)
    assert result["primary"] == aggregation["primary"]
    assert result["n_patients"] == 7
    assert all(
        result[case] == aggregation[case] for case in ("missed", "false", "both_empty")
    )
    brats = result["brats_penalty"]
    assert brats["n"] == aggregation["brats"]["n"]
    assert brats["mean"] == pytest.approx(aggregation["brats"]["mean"], abs=1e-9, rel=0)
    assert [brats[k] for k in ("median", "q25", "q75")] == [30, 15, (40 + penalty) / 2]
    assert brats["penalty"] == penalty
    assert (
        brats["label"]
        == "BraTS-style penalty convention; the penalty is an arbitrary constant"
    )


@pytest.mark.parametrize(
    "outcomes", [[], [("missed", None), ("false", None), ("both_empty", None)]]
)
def test_no_evaluable_cases(outcomes: list[tuple[str, float | None]]) -> None:
    result = summarize_hd95(outcomes, 12.0)
    assert result["primary"] == {
        "n_evaluable": 0,
        "mean": None,
        "median": None,
        "q25": None,
        "q75": None,
    }
    assert result["n_patients"] == len(outcomes)
    for case in ("missed", "false", "both_empty"):
        assert result[case] == bool(outcomes)
    assert result["brats_penalty"]["n"] == len(outcomes)
    assert result["brats_penalty"]["mean"] == (8.0 if outcomes else None)
