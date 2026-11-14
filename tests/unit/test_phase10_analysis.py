"""S4 acceptance checks on synthetic, hashed frozen prediction artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np
import pytest

from glioma_selective.evaluation import phase10_analysis as analysis
from glioma_selective.evaluation.calibration_metrics import (
    brier_score,
    expected_calibration_error,
)
from glioma_selective.evaluation.phase09_analysis import (
    CONDITIONS,
    _aligned_conditions,
    _condition_scores,
    _load_condition_frames,
    _patient_roster,
)
from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)
from glioma_selective.tracking.predictions import write_prediction_artifact

CHECKPOINT = "c" * 64
MEMBERS = ["R3", "R4", "R5", "R6"]
REPOSITORY = Path(__file__).resolve().parents[2]


def _json_artifact(path: Path, document: dict[str, Any]) -> None:
    payload = json.dumps(document, sort_keys=True).encode()
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    path.with_name(path.name + ".sha256").write_text(f"{digest}  {path.name}\n")


def _row(
    patient: str, cohort: str, condition: str, label: int, p: float, i: int
) -> dict[str, Any]:
    # M3 deliberately trusts the errors more than the correct cases, independently
    # of the deterministic probability. Each row still has the frozen 30 passes.
    mc_p = 0.99 if i < 3 else 0.51
    return {
        "patient_id": patient,
        "cohort": cohort,
        "modality_condition": condition,
        "label": label,
        "p_hat": p,
        "logit": math.log(p / (1 - p)),
        "mc_dropout_samples": [mc_p] * 30,
    }


def _prepare(
    root: Path,
    run_id: str,
    *,
    inverted: bool = False,
    n: int = 12,
    labels: list[int] | None = None,
    full_only: bool = False,
    reverse_rows: bool = False,
) -> Path:
    directory = root / "experiments" / run_id
    (directory / "conditions").mkdir(parents=True)
    (directory / "record.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "status": "completed",
                "checkpoint_hash": CHECKPOINT,
            }
        )
    )
    targets = labels if labels is not None else [i % 2 for i in range(n)]
    for condition in CONDITIONS if not full_only else ("full",):
        rows = [
            _row(
                f"cal-{i}",
                "utsw_calibration",
                condition,
                i % 2,
                (0.3 if i % 2 else 0.7)
                if inverted and i < 3
                else (0.7 if i % 2 else 0.3),
                i,
            )
            for i in range(12)
        ]
        for i, label in enumerate(targets):
            confidence = (
                (0.97 - 0.01 * i if i < 3 else 0.51 + 0.01 * i)
                if inverted
                else (0.51 + 0.01 * i if i < 3 else 0.65 + 0.02 * i)
            )
            predicted = 1 - label if i < 3 else label
            p = confidence if predicted else 1 - confidence
            rows.append(_row(f"test-{i}", "utsw_internal_test", condition, label, p, i))
        if reverse_rows:
            rows.reverse()
        if not full_only:
            write_prediction_artifact(
                rows,
                directory / "conditions" / f"{condition}.parquet",
                run_id=run_id,
                git_sha="synthetic",
                checkpoint_hash=CHECKPOINT,
            )
        if condition == "full":
            write_prediction_artifact(
                rows,
                directory / "predictions.parquet",
                run_id=run_id,
                git_sha="synthetic",
                checkpoint_hash=CHECKPOINT,
            )
    _json_artifact(
        directory / "conditions" / "conditions_meta.json",
        {"run_id": run_id, "checkpoint_hash": CHECKPOINT},
    )
    _json_artifact(
        directory / "segmentation_dice.json",
        {
            "run_id": run_id,
            "checkpoint_hash": CHECKPOINT,
            "splits": {
                "calibration": {"per_channel": {"ET": 0.1}, "mean": 0.1},
                "internal_test": {
                    "per_channel": {"WT": 0.6, "TC": 0.4, "ET": 0.5},
                    "mean": 0.5,
                },
            },
        },
    )
    return directory


def _all_runs(
    root: Path, *, ablations: bool = False, labels: list[int] | None = None
) -> None:
    for run_id in ("R2", *MEMBERS):
        _prepare(root, run_id, labels=labels, reverse_rows=run_id == "R4")
    if ablations:
        _prepare(
            root, "R7", inverted=True, labels=labels, full_only=True, reverse_rows=True
        )
        _prepare(root, "R8", labels=labels, full_only=True)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


@pytest.fixture(scope="module", params=[False, True])
def complete(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("s4-complete")
    _all_runs(root, ablations=True)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("GLIOMA_ARTIFACT_ROOT", str(root))
        path = analysis.analyze_phase10(
            "R2",
            ensemble_run_ids=MEMBERS,
            r7_run_id="R7",
            r8_run_id="R8",
            iterations=1000,
            include_egd=request.param,
        )
    return path, _read(path)


def test_complete_family_matches_frozen_blocks_and_has_no_adjusted_p(
    complete: tuple[Path, dict[str, Any]],
) -> None:
    _, report = complete
    assert report["schema"] == "phase10_analysis.v1"
    family = report["bh_family"]
    has_egd = any(row["cohort"] == "egd" for row in family)
    assert len(family) == len({row["id"] for row in family}) == (44 if has_egd else 29)
    assert sum(row["status"] == "computed" for row in family) == 14
    assert sum(row["status"] == "pending_external" for row in family) == (
        30 if has_egd else 15
    )
    assert {
        block: sum(row["block"] == block for row in family) for block in "ABCDE"
    } == (
        {"A": 9, "B": 15, "C": 2, "D": 6, "E": 12}
        if has_egd
        else {"A": 6, "B": 10, "C": 1, "D": 4, "E": 8}
    )
    assert {row["cohort"] for row in family} == (
        {"utsw", "ucsf_pdgm", "egd"} if has_egd else {"utsw", "ucsf_pdgm"}
    )
    assert not any("adjusted" in key for row in family for key in row)
    assert not any(
        "adjusted" in key for row in report["confirmatory"].values() for key in row
    )
    assert (
        report["supplementary_bh_internal_only"]["label"]
        == "supplementary; not the pre-registered family (D-052)"
    )
    assert len(report["supplementary_bh_internal_only"]["members"]) == 14
    for row in report["confirmatory"].values():
        assert row["n"] == 12 and row["status"] == "computed"
        assert 0 <= float(Fraction(row["p_value"])) <= 1


def test_planted_aurc_difference_and_interval(
    complete: tuple[Path, dict[str, Any]],
) -> None:
    _, report = complete
    # 12 distinct confidence scores, three errors. R2 errors occupy cutoffs
    # 10,11,12; R7 errors occupy 1,2,3. Hand-sum risk at all 12 cutoffs.
    best = sum((Fraction(k - 9, k) for k in range(10, 13)), Fraction()) / 12
    worst = sum((Fraction(min(k, 3), k) for k in range(1, 13)), Fraction()) / 12
    planted = float(worst - best)
    row = report["confirmatory"]["E2"]
    assert row["point"] == pytest.approx(planted, abs=1e-12)
    assert row["lower"] <= planted <= row["upper"]
    assert report["confirmatory"]["E1"]["method"] == "delong_paired_auroc"
    # R8 is a patient-shuffled copy of R2, so both AUROC and AURC are null.
    for key in ("E3", "E4"):
        assert report["confirmatory"][key]["point"] == 0
        assert float(Fraction(report["confirmatory"][key]["p_value"])) == 1


def test_metrics_calibration_labels_dice_and_sidecar(
    complete: tuple[Path, dict[str, Any]],
) -> None:
    path, report = complete
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        path.with_name(path.name + ".sha256").read_text() == f"{digest}  {path.name}\n"
    )
    primary_interval = report["runs"]["R2"]["auroc"]["bootstrap_95_interval"]
    for key in ("E1", "E3"):
        for count in ("valid_draws", "skipped_single_class_draws"):
            assert report["confirmatory"][key][count] == primary_interval[count]
    assert report["runs"]["R7"]["temperature"] > report["runs"]["R2"]["temperature"]
    for run in report["runs"].values():
        assert run["n"] == 12 and run["coverage"] == 1
        assert run["selective_mechanism"] == "M5"
        assert set(run["selective_risk_at_coverage"]) == {
            str(c) for c in analysis.COVERAGE_GRID
        }
        assert run["calibration"]["M1"]["probability"] == "raw"
        assert run["calibration"]["M2"]["probability"] == "temperature_scaled"
        assert run["segmentation_dice"] == {
            "per_channel": {"WT": 0.6, "TC": 0.4, "ET": 0.5},
            "mean": 0.5,
        }
        assert run["hd95"] == {
            "status": "absent",
            "reason": "needs a segmentation freeze (T10.10)",
        }
        assert run["auroc"]["quoted"] in (
            "bootstrap_95_interval",
            "hanley_mcneil_95_interval",
        )
        for metric in ("auroc", "auprc"):
            interval = run[metric]["bootstrap_95_interval"]
            assert (
                interval["valid_draws"] + interval["skipped_single_class_draws"] == 1000
            )
        assert (
            run["aurc_mean_over_cutoffs"]["bootstrap_95_interval"]["valid_draws"]
            == 1000
        )


def test_absent_ablations_cli_uses_one_matrix_and_egd_listing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _all_runs(tmp_path)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(tmp_path))
    calls = []
    original = analysis.bootstrap_indices

    def spy(n: int, iterations: int, seed: int) -> np.ndarray:
        calls.append((n, iterations, seed))
        return original(n, iterations, seed)

    monkeypatch.setattr(analysis, "bootstrap_indices", spy)
    # Load the actual CLI file so the requested argument spelling is exercised.
    spec = importlib.util.spec_from_file_location(
        "s4_cli", REPOSITORY / "scripts" / "analyze_phase10.py"
    )
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    argv = ["--run-id", "R2", "--r7-run-id", "unfinished-R7", "--iterations", "1000"]
    for member in MEMBERS:
        argv.extend(["--ensemble-run-id", member])
    assert cli.main(argv) == 0
    path = Path(capsys.readouterr().out.strip())
    report = _read(path)
    assert calls == [(12, 1000, 0)]
    assert len(report["bh_family"]) == 29
    assert sum(row["status"] == "computed" for row in report["bh_family"]) == 10
    for key in ("E1", "E2", "E3", "E4"):
        assert set(report["confirmatory"][key]) == {"status", "reason"}
        assert report["confirmatory"][key]["status"] == "absent"
    with pytest.raises(FileExistsError):
        analysis.analyze_phase10("R2", ensemble_run_ids=MEMBERS, iterations=1000)
    # This is listing-only metadata, with no artifact root configured.
    monkeypatch.delenv("GLIOMA_ARTIFACT_ROOT")
    family = analysis._family(True)
    assert len(family) == 44
    assert sum(row["cohort"] == "egd" for row in family) == 15
    assert all(
        row["status"] == "pending_external" for row in family if row["cohort"] != "utsw"
    )


def test_shared_draw_differences_negate_and_null_p_over_seeds() -> None:
    a = np.array([0.1, 0.4, 0.7, 0.9])
    b = np.array([0.4, 0.7, 0.1, 0.9])
    n_null = 0
    for seed in range(10):
        matrix = bootstrap_indices(4, 1000, seed)
        first = analysis._estimate(np.mean, (a,), matrix)
        second = analysis._estimate(np.mean, (b,), matrix)
        forward = analysis._difference(first, second, "test", 4)
        reverse = analysis._difference(second, first, "test", 4)
        assert forward["point"] == -reverse["point"]
        assert np.array_equal(first.draws - second.draws, -(second.draws - first.draws))
        assert forward["p_value"] == reverse["p_value"]
        assert forward["lower"] == pytest.approx(-reverse["upper"])
        n_null += float(Fraction(forward["p_value"])) > 0.05
    assert n_null >= 8


def test_same_validity_mask_and_all_draws_kept_for_other_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    labels = [0] * 11 + [1]
    _all_runs(tmp_path, labels=labels)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(tmp_path))
    report = _read(
        analysis.analyze_phase10("R2", ensemble_run_ids=MEMBERS, iterations=1000)
    )
    run = report["runs"]["R2"]
    draws = bootstrap_indices(12, 1000, 0)
    # Patient hash ordering changes positions, so check the actual common mask.
    directory = tmp_path / "experiments" / "R2"
    frames, (predictions, _, mc) = _load_condition_frames("R2", directory, CHECKPOINT)
    ids, aligned_labels = _patient_roster(frames, predictions, mc)
    valid = analysis._valid_class_draws(aligned_labels, draws)
    valid_count = int(valid.sum())
    assert 0 < valid_count < 1000
    aligned, _, _ = _aligned_conditions(frames, ids, 30)
    for metric in ("auroc", "auprc"):
        interval = run[metric]["bootstrap_95_interval"]
        assert interval["valid_draws"] == valid_count
        assert interval["skipped_single_class_draws"] == 1000 - valid_count
    for mechanism, column in (("M1", "raw_p"), ("M2", "scaled_full")):
        for name, statistic in (
            ("brier", brier_score),
            ("ece", expected_calibration_error),
        ):
            value = run["calibration"][mechanism][name]
            assert value["bootstrap_95_interval"]["valid_draws"] == 1000
            p = aligned["full"][column]
            expected = percentile_interval(
                np.asarray([statistic(p[row], aligned_labels[row]) for row in draws])
            )
            assert (
                value["bootstrap_95_interval"]["lower"],
                value["bootstrap_95_interval"]["upper"],
            ) == expected
    assert run["aurc_mean_over_cutoffs"]["bootstrap_95_interval"]["valid_draws"] == 1000
    assert all(
        row["bootstrap_95_interval"]["valid_draws"] == 1000
        for row in run["selective_risk_at_coverage"].values()
    )
    assert (
        report["confirmatory"]["B1"]["lower"]
        == report["confirmatory"]["B1"]["upper"]
        == 0
    )
    # No valid row is a hard failure, with no new sampling attempt.
    all_one_class = np.zeros((1000, len(ids)), dtype=np.int64)
    with pytest.raises(ValueError, match="all bootstrap resamples"):
        analysis._valid_class_draws(aligned_labels, all_one_class)


@pytest.mark.parametrize("broken", ["condition", "dice", "sidecar", "member"])
def test_missing_required_artifact_fails_before_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    _all_runs(tmp_path)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(tmp_path))
    main = tmp_path / "experiments" / "R2"
    target = {
        "condition": main / "conditions" / "drop_t1.parquet.sha256",
        "dice": main / "segmentation_dice.json",
        "sidecar": main / "predictions.parquet.sha256",
        "member": tmp_path
        / "experiments"
        / "R4"
        / "conditions"
        / "full.parquet.sha256",
    }[broken]
    target.unlink()
    with pytest.raises(ValueError, match="invalid|missing"):
        analysis.analyze_phase10("R2", ensemble_run_ids=MEMBERS, iterations=1000)
    assert not (main / "phase10_analysis.json").exists()


def test_ablation_patient_mismatch_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _all_runs(tmp_path)
    _prepare(tmp_path, "R7", n=10, full_only=True)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="patient sets or labels differ"):
        analysis.analyze_phase10(
            "R2", ensemble_run_ids=MEMBERS, r7_run_id="R7", iterations=1000
        )


def test_phase09_builders_are_reused_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _all_runs(tmp_path)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(tmp_path))
    directory = tmp_path / "experiments" / "R2"
    frames, (predictions, _, mc) = _load_condition_frames("R2", directory, CHECKPOINT)
    ids, _ = _patient_roster(frames, predictions, mc)
    aligned, _, _ = _aligned_conditions(frames, ids, 30)
    scores, errors = _condition_scores("full", aligned["full"], "R2", ids, MEMBERS, {})
    single_scores, single_errors = analysis._single_model_scores(
        aligned["full"]["raw_p"],
        aligned["full"]["scaled_full"],
        aligned["full"]["labels"],
    )
    for mechanism in ("M1", "M2", "M5"):
        assert scores[mechanism] == single_scores[mechanism]
        assert np.array_equal(errors[mechanism], single_errors[mechanism])


def test_hanley_mcneil_matches_published_table() -> None:
    # Independent published examples, p.33, eqs.1-2 (source in helper docstring).
    # Expected SEs are rounded by the authors to four decimal places.
    for auc, positives, negatives, expected in (
        (0.85, 40, 40, 0.0437),
        (0.905, 51, 58, 0.0307),
    ):
        interval = analysis._hanley_mcneil(auc, positives, negatives)
        se = (interval["upper"] - interval["lower"]) / (2 * NormalDist().inv_cdf(0.975))
        assert se == pytest.approx(expected, abs=0.00005)


@pytest.mark.parametrize("iterations", [0, 999, True, 1000.5])
def test_minimum_iterations_enforced_before_artifacts(iterations: Any) -> None:
    with pytest.raises(ValueError):
        analysis.analyze_phase10("R2", ensemble_run_ids=MEMBERS, iterations=iterations)


def test_cli_help_is_runnable_from_checkout() -> None:
    result = subprocess.run(
        [sys.executable, str(REPOSITORY / "scripts" / "analyze_phase10.py"), "--help"],
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join((str(REPOSITORY / "src"), str(REPOSITORY))),
        },
    )
    for flag in (
        "--run-id",
        "--ensemble-run-id",
        "--r7-run-id",
        "--r8-run-id",
        "--iterations",
        "--seed",
    ):
        assert flag in result.stdout


def test_null_aurc_comparison_over_seeds() -> None:
    scores = np.asarray([0.2, 0.4, 0.6, 0.8])
    errors = np.asarray([0, 1, 0, 1])
    above = 0
    for seed in range(10):
        matrix = bootstrap_indices(4, 1000, seed)
        first = analysis._estimate(analysis._aurc, (scores, errors), matrix)
        second = analysis._estimate(
            analysis._aurc, (scores[::-1], errors[::-1]), matrix
        )
        row = analysis._difference(first, second, "null-aurc", 4)
        assert row["point"] == 0
        above += float(Fraction(row["p_value"])) > 0.05
    assert above >= 8
