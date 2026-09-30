"""T04.8 report-only range check for normalized brain voxels."""

from __future__ import annotations

import math

import numpy as np
from scripts.zscore_range_check import aggregate_group, render_report

from glioma_selective.preprocessing.normalize import (
    ModalityStats,
    NormalizationStats,
)
from glioma_selective.preprocessing.zscore_check import (
    ZSummary,
    flag_summary,
    reference_ranges,
    summarize_volume,
)


def _stats(mean: float = 2.0, std: float = 2.0) -> NormalizationStats:
    modalities = {
        sequence: ModalityStats(mean=mean, std=std, voxel_count=3)
        for sequence in ("T1", "T1ce", "T2", "FLAIR")
    }
    return NormalizationStats(
        fit_cohort="utsw",
        fit_split="train",
        patient_count=1,
        train_roster_sha256="a" * 64,
        split_manifest_sha256="b" * 64,
        modalities=modalities,
    )


def _summary(
    mean: float,
    std: float,
    p99_9: float,
    *,
    finite: bool = True,
) -> ZSummary:
    return ZSummary(
        n=4,
        mean=mean,
        std=std,
        minimum=-1.0,
        maximum=p99_9,
        p0_1=-0.9,
        p99_9=p99_9,
        finite=finite,
    )


def test_summary_matches_hand_worked_values_and_excludes_background() -> None:
    # Brain input {2, 4, 6} has median 4, so it rescales to {0.5, 1, 1.5}.
    # Frozen mean=2 and std=2 give z={-0.75, -0.5, -0.25}; thus n=3,
    # mean=-0.5, population std=sqrt(0.125/3), min=-0.75, max=-0.25.
    # Linear percentiles are -0.75 + 0.002*0.25 = -0.7495 and
    # -0.5 + 0.998*0.25 = -0.2505.
    volume = np.array([0, 2, 4, 0, 6], dtype=np.float32)
    summary = summarize_volume(volume, "T1", _stats())

    assert summary.n == 3
    assert summary.mean == -0.5
    assert math.isclose(summary.std, math.sqrt(0.125 / 3.0))
    assert summary.minimum == -0.75
    assert summary.maximum == -0.25
    assert math.isclose(summary.p0_1, -0.7495)
    assert math.isclose(summary.p99_9, -0.2505)
    assert summary.finite


def test_percentile_is_computed_on_brain_values_with_numpy_linear_interpolation() -> (
    None
):
    # Brain input {1, 2, 3, 4} has median 2.5 and rescales to
    # {0.4, 0.8, 1.2, 1.6}; mean=0 and std=1 leave those values unchanged.
    # p99.9 is at position 0.999*3=2.997: 1.2 + 0.997*0.4 = 1.5988.
    volume = np.array([0, 1, 2, 3, 4], dtype=np.float32)
    summary = summarize_volume(volume, "T2", _stats(mean=0.0, std=1.0))

    assert summary.n == 4
    assert math.isclose(summary.p99_9, 1.5988, rel_tol=1e-7)


def test_summary_is_invariant_to_volume_scale() -> None:
    volume = np.array([0, 2, 4, 0, 6], dtype=np.float32)
    original = summarize_volume(volume, "T1", _stats())
    scaled = summarize_volume(volume * 1000, "T1", _stats())

    assert scaled.n == original.n
    assert scaled.finite == original.finite
    for field in ("mean", "std", "minimum", "maximum", "p0_1", "p99_9"):
        assert math.isclose(
            getattr(scaled, field),
            getattr(original, field),
            rel_tol=1e-5,
        )


def test_summarizing_does_not_change_the_input_array() -> None:
    volume = np.array([0, 2, 4, 0, 6], dtype=np.float32)
    original = volume.copy()

    summarize_volume(volume, "FLAIR", _stats())

    np.testing.assert_array_equal(volume, original)


def test_reference_ranges_use_minimum_and_maximum_across_train_patients() -> None:
    summaries = {
        "p1": {"T1": _summary(1.0, 2.0, 3.0)},
        "p2": {"T1": _summary(-1.0, 4.0, 5.0)},
        "p3": {"T1": _summary(0.5, 3.0, 4.0)},
    }

    assert reference_ranges(summaries) == {
        "T1": {"mean": (-1.0, 1.0), "std": (2.0, 4.0), "p99_9": (3.0, 5.0)}
    }


def test_flags_values_above_below_and_at_train_boundaries() -> None:
    reference = {"mean": (0.0, 1.0), "std": (2.0, 3.0), "p99_9": (4.0, 5.0)}

    assert flag_summary(_summary(1.1, 2.5, 4.5), reference) == ["mean"]
    assert flag_summary(_summary(0.5, 1.9, 4.5), reference) == ["std"]
    assert flag_summary(_summary(0.5, 2.5, 5.1), reference) == ["p99_9"]
    assert flag_summary(_summary(0.0, 3.0, 4.0), reference) == []


def test_non_finite_summary_always_has_a_non_finite_flag() -> None:
    reference = {"mean": (0.0, 1.0), "std": (2.0, 3.0), "p99_9": (4.0, 5.0)}

    assert flag_summary(_summary(0.5, 2.5, 4.5, finite=False), reference) == [
        "non_finite"
    ]


def test_script_aggregate_helpers_only_report_aggregates() -> None:
    reference = {"T1": {"mean": (0.0, 1.0), "std": (2.0, 3.0), "p99_9": (4.0, 5.0)}}
    summaries = {"private-id-a": {"T1": _summary(0.5, 2.5, 4.5)}}

    aggregate = aggregate_group(summaries, reference)
    rendered = render_report({"train": summaries}, reference)

    assert aggregate["patient_count"] == 1
    assert aggregate["patients_with_any_flag"] == 0
    assert "private-id-a" not in rendered
    assert "EGD: skipped (not downloaded)" in rendered
