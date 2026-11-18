"""Phase 12 external analysis on synthetic frozen artifacts (no real cohort data)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from tests.unit import test_phase10_analysis as p10

from glioma_selective.evaluation import firewall, phase12_analysis
from glioma_selective.evaluation.phase09_analysis import (
    CONDITIONS,
    _aligned_conditions,
    _load_condition_frames,
    _patient_roster,
)
from glioma_selective.evaluation.phase12_analysis import (
    FreezeProvenanceError,
    analyze_external,
)
from glioma_selective.selective.aurc import aurc_mean_over_cutoffs
from glioma_selective.tracking.predictions import (
    read_prediction_artifact,
    write_prediction_artifact,
)

COHORT = "ucsf_pdgm"
CHECKPOINT = p10.CHECKPOINT
CODE_SHA = "a" * 40
PRIMARY_ROLES = {
    "primary_seed0": "R2",
    "ensemble_seed1": "R3",
    "ensemble_seed2": "R4",
    "ensemble_seed3": "R5",
    "ensemble_seed4": "R6",
    "m6_comparator_r1": "R1",
}
ABLATION_ROLES = {"ablation_r7_whole_brain": "R7", "ablation_r8_two_stage": "R8"}


def _sealed_manifest(
    root: Path, name: str, roles: dict[str, str], temperature: float
) -> tuple[Path, str]:
    """A signed, sealed manifest with every field the firewall requires."""
    document: dict[str, Any] = {
        field: {"synthetic": field} for field in firewall.MANIFEST_FIELDS
    }
    document.update(
        code_commit_sha=CODE_SHA,
        git_tree_clean=True,
        model_checkpoints=[
            {
                "role": role,
                "run_id": run,
                "path": f"artifacts:experiments/{run}/checkpoints/best.pt",
                "sha256": CHECKPOINT,
            }
            for role, run in roles.items()
        ],
        calibration_parameters={"temperature": temperature},
        authorizing_signature={
            "name": "Synthetic Lead",
            "date": "2026-11-18",
            "status": "signed",
        },
    )
    path = root / "gate_e" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    path.with_name(path.name + ".sha256").write_text(f"{digest}  {path.name}\n")
    return path, digest


def _external_rows(
    root: Path, run: str, condition: str, shift: float
) -> list[dict[str, Any]]:
    """The run's internal test rows, renamed to the external cohort and nudged."""
    directory = root / "experiments" / run
    source = (
        directory / "conditions" / f"{condition}.parquet"
        if (directory / "conditions" / f"{condition}.parquet").exists()
        else directory / "predictions.parquet"
    )
    frame, _ = read_prediction_artifact(source)
    test = frame[frame["cohort"] == "utsw_internal_test"]
    rows = []
    for row in test.to_dict("records"):
        # Stored patient ids are pseudonymised hashes, so use them as a stable key.
        number = int(str(row["patient_id"]), 16) % 97
        p = min(
            0.98, max(0.02, 0.9 * float(row["p_hat"]) + 0.05 + shift * 0.01 * number)
        )
        rows.append(
            {
                "patient_id": f"ext-{row['patient_id']}",
                "cohort": COHORT,
                "modality_condition": condition,
                "label": int(row["label"]) if shift == 0 else number % 2,
                "p_hat": p,
                "logit": math.log(p / (1 - p)),
                "mc_dropout_samples": [
                    min(0.98, max(0.02, float(x) * 0.95 + 0.02))
                    for x in row["mc_dropout_samples"]
                ],
            }
        )
    return rows


def _freeze_external(
    root: Path,
    run_id: str,
    manifest_path: Path,
    digest: str,
    roles: dict[str, str],
    *,
    shift: float = 0.0,
    report_digest: str | None = None,
) -> Path:
    directory = root / "experiments" / "external_frozen" / COHORT / run_id
    for role, run in roles.items():
        for condition in CONDITIONS:
            write_prediction_artifact(
                _external_rows(root, run, condition, shift),
                directory / role / f"{condition}.parquet",
                run_id=run_id,
                git_sha=CODE_SHA,
                checkpoint_hash=CHECKPOINT,
                freeze_manifest_sha256=digest,
            )
    manifest = json.loads(manifest_path.read_text())
    report = {
        "run_id": run_id,
        "cohort": COHORT,
        "counts": {c: 12 for c in CONDITIONS},
        "git_sha": CODE_SHA,
        "post_run_git_sha": CODE_SHA,
        "git_sha_unchanged": True,
        "freeze_manifest_sha256": report_digest or digest,
        "model_checkpoints": manifest["model_checkpoints"],
    }
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    (directory / "report.json").write_bytes(payload)
    (directory / "report.json.sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  report.json\n"
    )
    return directory


def _scenario(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    shift: float = 0.0,
    with_ablation: bool = True,
    report_digest: str | None = None,
    temperature_offset: float = 0.0,
) -> dict[str, Any]:
    p10._all_runs(root, ablations=True)
    p10._prepare(root, "R1")
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(root))
    run_dir = root / "experiments" / "R2"
    frames, _ = _load_condition_frames("R2", run_dir, CHECKPOINT)
    ids, _ = _patient_roster(frames, frames["full"], None)
    _aligned, temperature, _scaled = _aligned_conditions(frames, ids, 30)
    manifest1, digest1 = _sealed_manifest(
        root, "freeze_manifest.json", PRIMARY_ROLES, temperature + temperature_offset
    )
    monkeypatch.setattr(firewall, "freeze_manifest_path", lambda: manifest1)
    monkeypatch.setenv(firewall.FLAG_NAME, "1")
    _freeze_external(
        root,
        "ext1",
        manifest1,
        digest1,
        PRIMARY_ROLES,
        shift=shift,
        report_digest=report_digest,
    )
    result: dict[str, Any] = {"manifest1": manifest1, "temperature": temperature}
    if with_ablation:
        manifest2, digest2 = _sealed_manifest(
            root, "freeze_manifest_r7r8.json", ABLATION_ROLES, temperature
        )
        _freeze_external(root, "ext2", manifest2, digest2, ABLATION_ROLES, shift=shift)
        result["manifest2"] = manifest2
    return result


def _run(info: dict[str, Any], *, with_ablation: bool = True) -> tuple[dict, dict]:
    kwargs: dict[str, Any] = {"iterations": 1000, "permutations": 50}
    if with_ablation:
        kwargs.update(ablation_run_id="ext2", ablation_manifest_path=info["manifest2"])
    out09, out10 = analyze_external("R2", "ext1", info["manifest1"], **kwargs)
    return json.loads(out09.read_text()), json.loads(out10.read_text())


def test_full_external_analysis_writes_claims_family_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch)
    doc09, doc10 = _run(info)
    assert doc09["schema"] == "phase09_analysis.v1"
    assert set(doc09["claims"]) == {"C3", "C4", "C5", "C6"}
    assert doc09["claims"]["C3"]["status"] == doc09["claims"]["C3"]["full"]["status"]
    for condition in CONDITIONS:
        cells = doc09["conditions"][condition]
        for mechanism in ("M1", "M2", "M3", "M4", "M5", "M6"):
            assert cells[mechanism].get("absent") is not True, (condition, mechanism)
        assert set(doc09["conformal"][condition]) == {"carried_over", "refit"}
    assert doc09["results_summary"]["absent_cells"] == []
    provenance = doc09["provenance"]
    assert provenance["test_cohort"] == COHORT
    assert provenance["test_patient_count"] == 12
    assert provenance["external_run_id"] == "ext1"
    assert (
        provenance["freeze_manifest_sha256"]
        == hashlib.sha256(info["manifest1"].read_bytes()).hexdigest()
    )
    assert doc10["schema"] == "phase10_external_analysis.v1"
    family = {row["id"]: row for row in doc10["family"]}
    assert len(family) == 15
    assert all(row["status"] == "computed" for row in family.values())
    assert {key.split(":")[1] for key in family} == {
        *(f"A{i}" for i in (1, 2, 3)),
        *(f"B{i}" for i in range(1, 6)),
        "C1",
        "D1",
        "D2",
        *(f"E{i}" for i in range(1, 5)),
    }
    assert doc10["confirmatory"]["C1"]["method"] == "unpaired_independent_resamples"
    assert "segmentation_dice" not in doc10["runs"]["R2"]


def test_without_the_second_run_block_e_is_pending_not_computed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch, with_ablation=False)
    _doc09, doc10 = _run(info, with_ablation=False)
    statuses = {row["id"].split(":")[1]: row["status"] for row in doc10["family"]}
    assert [statuses[f"E{i}"] for i in range(1, 5)] == ["pending_external"] * 4
    assert statuses["A1"] == "computed"


def test_e_block_matches_a_direct_aurc_on_the_external_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch)
    _doc09, doc10 = _run(info)

    def aurc(run: str) -> float:
        frame, _ = read_prediction_artifact(
            tmp_path
            / "experiments"
            / "external_frozen"
            / COHORT
            / ("ext2" if run in ("R7", "R8") else "ext1")
            / {
                "R2": "primary_seed0",
                "R7": "ablation_r7_whole_brain",
                "R8": "ablation_r8_two_stage",
            }[run]
            / "full.parquet"
        )
        frame = frame.sort_values("patient_id")
        p = frame["p_hat"].to_numpy(dtype=float)
        label = frame["label"].to_numpy()
        return aurc_mean_over_cutoffs(
            np.maximum(p, 1 - p).tolist(),
            ((p >= 0.5) != (label == 1)).astype(int).tolist(),
        )

    assert doc10["confirmatory"]["E2"]["point"] == pytest.approx(
        aurc("R7") - aurc("R2"), abs=1e-12
    )
    assert doc10["confirmatory"]["E4"]["point"] == pytest.approx(
        aurc("R8") - aurc("R2"), abs=1e-12
    )


def test_nothing_is_fitted_on_external_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Different external labels and probabilities leave every fitted value alone."""
    first = _scenario(tmp_path / "a", monkeypatch, shift=0.0)
    doc09_a, _ = _run(first)
    second = _scenario(tmp_path / "b", monkeypatch, shift=1.0)
    doc09_b, _ = _run(second)
    assert doc09_a["provenance"]["full_temperature"] == pytest.approx(
        doc09_b["provenance"]["full_temperature"], abs=0
    )
    for condition in CONDITIONS:
        for alpha in ("0.05", "0.1", "0.2"):
            for variant in ("carried_over", "refit"):
                a = doc09_a["conformal"][condition][variant][alpha]["quantile"]
                b = doc09_b["conformal"][condition][variant][alpha]["quantile"]
                assert a == b, (condition, variant, alpha)
    assert doc09_a["conditions"] != doc09_b["conditions"]  # the external data differ


def test_flag_off_blocks_before_any_external_file_is_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch)
    monkeypatch.delenv(firewall.FLAG_NAME)
    opened: list[Path] = []
    original = phase12_analysis.read_prediction_artifact
    monkeypatch.setattr(
        phase12_analysis,
        "read_prediction_artifact",
        lambda path: opened.append(path) or original(path),
    )
    with pytest.raises(firewall.ExternalEvaluationNotAuthorized):
        analyze_external("R2", "ext1", info["manifest1"], iterations=1000)
    assert opened == []
    assert not (
        tmp_path
        / "experiments/external_frozen/ucsf_pdgm/ext1/phase09_external_analysis.json"
    ).exists()


def test_report_manifest_hash_mismatch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch, with_ablation=False, report_digest="0" * 64)
    with pytest.raises(FreezeProvenanceError, match="freeze_manifest_sha256"):
        analyze_external("R2", "ext1", info["manifest1"], iterations=1000)


def test_manifest_temperature_must_equal_the_utsw_fit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(
        tmp_path, monkeypatch, with_ablation=False, temperature_offset=0.01
    )
    with pytest.raises(FreezeProvenanceError, match="temperature"):
        analyze_external("R2", "ext1", info["manifest1"], iterations=1000)


def test_a_modified_external_file_fails_its_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch, with_ablation=False)
    victim = (
        tmp_path
        / "experiments/external_frozen/ucsf_pdgm/ext1/ensemble_seed2/drop_t1.parquet"
    )
    victim.write_bytes(victim.read_bytes() + b"x")
    with pytest.raises(ValueError):
        analyze_external("R2", "ext1", info["manifest1"], iterations=1000)


def test_a_second_analysis_into_the_same_run_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _scenario(tmp_path, monkeypatch, with_ablation=False)
    _run(info, with_ablation=False)
    with pytest.raises(FileExistsError):
        _run(info, with_ablation=False)
