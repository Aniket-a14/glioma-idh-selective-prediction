"""Phase 12 operational contract, using temporary synthetic inputs only."""

from __future__ import annotations

import builtins
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from scripts import run_external_evaluation as driver

from glioma_selective.data import dataset, metadata
from glioma_selective.data.adapters import ucsf_pdgm
from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.evaluation import firewall
from glioma_selective.leakage.cohort_manifest import (
    ROSTER_CONSTRUCTION,
    compute_roster_sha256,
)
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.models.segresnet import ModelConfig, build_model
from glioma_selective.preprocessing.normalize import (
    ModalityStats,
    NormalizationStats,
    write_normalization_stats,
)
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.training.checkpoint import save_model_weights
from glioma_selective.utils import paths

SHA = "a" * 40
STAND_IN = "synthetic_external"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seal(path: Path, document: dict[str, Any]) -> None:
    path.write_text(json.dumps(document))
    path.with_name(path.name + ".sha256").write_text(f"{_digest(path)}  {path.name}\n")


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Actual inventory builder, label parser, dataset constructor and scorer."""
    torch.set_num_threads(1)
    repo, data, artifacts = (tmp_path / name for name in ("repo", "data", "artifacts"))
    for root in (repo, data, artifacts):
        root.mkdir()
    monkeypatch.setattr(paths, "data_root", lambda: data)
    monkeypatch.setattr(paths, "artifact_root", lambda: artifacts)
    monkeypatch.setattr(driver, "REPOSITORY_ROOT", repo)
    monkeypatch.setitem(
        driver._COHORT_DATASETS, STAND_IN, (Cohort.UCSF_PDGM, dataset.IDHDataset)
    )
    monkeypatch.setattr(
        firewall, "EXTERNAL_COHORTS", (*firewall.EXTERNAL_COHORTS, STAND_IN)
    )
    monkeypatch.setattr(driver, "git_state", lambda _: (SHA, True))
    monkeypatch.setenv(firewall.FLAG_NAME, "1")

    ids = tuple(f"UCSF-PDGM-{index:04d}" for index in (1, 2))
    for patient in (*ids, "UCSF-PDGM-0003"):
        (data / "external/ucsf_pdgm" / patient).mkdir(parents=True)
    (data / "raw/utsw/UTSW-BT0001").mkdir(parents=True)
    manifests = data / "manifests"
    manifests.mkdir()
    exclusion = manifests / "exclusions.json"
    exclusion.write_text(
        json.dumps(
            {"exclusions": [{"cohort": "ucsf_pdgm", "patient_id": "UCSF-PDGM-0003"}]}
        )
    )
    post_qc = repo / "docs/research/manifests/cohort_manifest_post_qc.json"
    post_qc.parent.mkdir(parents=True)
    post_qc.write_text(
        json.dumps(
            {
                "cohorts": {
                    "ucsf_pdgm": {
                        "retained_patient_count": 2,
                        "roster_sha256": compute_roster_sha256(ids, Cohort.UCSF_PDGM),
                        "roster_construction": ROSTER_CONSTRUCTION,
                    }
                }
            }
        )
    )
    (manifests / "preprocessing_outputs.json").write_text(
        json.dumps({"ucsf_pdgm": {patient: {} for patient in ids}})
    )
    stats = NormalizationStats(
        fit_cohort="utsw",
        fit_split="train",
        patient_count=2,
        train_roster_sha256="b" * 64,
        split_manifest_sha256="c" * 64,
        modalities={
            sequence.value: ModalityStats(mean=0, std=1, voxel_count=8)
            for sequence in CORE_SEQUENCES
        },
    )
    stats_path = manifests / "normalization.json"
    write_normalization_stats(stats_path, stats)
    labels = tmp_path / "synthetic_labels.csv"
    labels.write_text(
        "ID,IDH,1p/19q\n"
        "UCSF-PDGM-001,IDH1 p.R132H,UNREAD\n"
        "UCSF-PDGM-002,wildtype,UNREAD\n"
    )
    monkeypatch.setattr(
        metadata,
        "default_metadata_specs",
        lambda: (
            metadata.MetadataFileSpec("UCSF-PDGM", labels, ",", "ID", {"IDH": "IDH"}),
        ),
    )

    def patient_image(self: Any, patient: str) -> tuple[np.ndarray, np.ndarray, bool]:
        # Keep the actual constructor, ID selection and channel zeroing; stand in
        # for the expensive image/cache I/O with small synthetic volumes.
        self._patient_entry(patient)
        image = np.stack(
            [np.full((16, 16, 16), float(i + 1), dtype=np.float32) for i in range(4)]
        )
        return image, np.zeros((3, 16, 16, 16), dtype=np.float32), False

    monkeypatch.setattr(dataset.IDHDataset, "_load_patient", patient_image)
    cfg = repo / "conditions.yaml"
    shutil.copyfile(
        driver.__file__.replace(
            "scripts/run_external_evaluation.py", "configs/evaluation/conditions.yaml"
        ),
        cfg,
    )
    preprocessing = repo / "preprocessing.yaml"
    preprocessing.write_text("frozen: true\n")
    torch.manual_seed(17)
    model = build_model(ModelConfig(init_filters=8, head_hidden=8))
    weights = artifacts / "weights.pt"
    save_model_weights(weights, model, epoch=1)
    checkpoints = []
    for index in range(6):
        run_id = "0" * 25 + str(index)
        role = f"ensemble_seed{index}" if index < 5 else "m6_comparator_r1"
        directory = paths.experiments_dir() / run_id
        directory.mkdir(parents=True)
        (directory / "record.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "seed": index,
                    "checkpoint_hash": _digest(weights),
                    "config": {"model": {"init_filters": 8, "head_hidden": 8}},
                }
            )
        )
        checkpoints.append(
            {
                "role": role,
                "run_id": run_id,
                "path": "artifacts:weights.pt",
                "sha256": _digest(weights),
            }
        )
    # Start with the published shape, replacing every input with temporary data.
    spec = json.loads(
        (
            Path(__file__).parents[2] / "docs/research/protocols/freeze_spec.json"
        ).read_text()
    )
    document = dict(spec["literal"])
    document.update(
        {
            "code_commit_sha": SHA,
            "git_tree_clean": True,
            "model_checkpoints": checkpoints,
            "preprocessing": {
                "config_path": "repo:preprocessing.yaml",
                "config_sha256": _digest(preprocessing),
            },
            "normalization_statistics": {
                "path": "data:manifests/normalization.json",
                "sha256": _digest(stats_path),
            },
            "exclusion_manifest": {
                "path": "data:manifests/exclusions.json",
                "sha256": _digest(exclusion),
            },
            "utsw_split_manifest": {"path": "unused", "sha256": "d" * 64},
            "statistical_analysis_plan": {"path": "unused", "sha256": "e" * 64},
            "authorizing_signature": {"name": "Synthetic test", "date": "2026-01-01"},
        }
    )
    document["missing_modality_conditions"].update(
        {
            "cohorts": [STAND_IN],
            "config": "repo:conditions.yaml",
            "config_sha256": _digest(cfg),
        }
    )
    manifest = firewall.freeze_manifest_path()
    manifest.parent.mkdir(parents=True)
    _seal(manifest, document)
    return {
        "manifest": manifest,
        "document": document,
        "labels": labels,
        "repo": repo,
        "data": data,
        "artifacts": artifacts,
        "weights": weights,
        "post_qc": post_qc,
        "output": paths.experiments_dir() / "external_frozen" / STAND_IN / "test-run",
    }


@pytest.mark.parametrize("flag", [None, "0"])
def test_firewall_runs_before_any_file_open(
    harness: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    flag: str | None,
) -> None:
    if flag is None:
        monkeypatch.delenv(firewall.FLAG_NAME)
    else:
        monkeypatch.setenv(firewall.FLAG_NAME, flag)
    calls = []

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        calls.append(args)
        raise AssertionError("firewall must run before opening anything")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    with pytest.raises(firewall.ExternalEvaluationNotAuthorized):
        driver.run_external_evaluation(STAND_IN, "test-run")
    assert calls == []


def test_full_frozen_path_no_refit_or_metric_output(
    harness: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def no_refit(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("no calibration fit is allowed in this driver")

    monkeypatch.setattr(
        "glioma_selective.calibration.temperature.fit_temperature", no_refit
    )
    monkeypatch.setattr(
        "glioma_selective.calibration.conformal.conformal_quantile", no_refit
    )
    output = driver.run_external_evaluation(STAND_IN, "test-run", device="cpu")
    files = sorted(output.rglob("*.parquet"))
    assert len(files) == 36  # five ensemble members, the comparator, six conditions
    for file in files:
        frame, meta = read_prediction_artifact(file)
        assert len(frame) == 2
        assert set(frame["cohort"]) == {STAND_IN}
        assert all(len(draws) == 30 for draws in frame["mc_dropout_samples"])
        assert meta["freeze_manifest_sha256"] == _digest(harness["manifest"])
        assert meta["git_sha"] == SHA
        assert meta["run_id"] == "test-run"
        assert meta["checkpoint_hash"] == _digest(harness["weights"])
    report = json.loads((output / "report.json").read_text())
    assert report["git_sha_unchanged"] is True
    assert report["post_run_git_sha"] == SHA
    assert (
        report["calibration_parameters"]
        == harness["document"]["calibration_parameters"]
    )
    assert report["conformal"] == harness["document"]["conformal"]
    assert (
        _digest(output / "report.json")
        == (output / "report.json.sha256").read_text().split()[0]
    )
    captured = capsys.readouterr()
    expected = "".join(
        f"rows[{STAND_IN}:{condition}]=2\n"
        for condition in harness["document"]["missing_modality_conditions"][
            "conditions"
        ]
    )
    assert captured.out == expected
    assert captured.err == ""
    assert not any(
        word in (captured.out + captured.err).lower()
        for word in ("auroc", "ece", "brier")
    )


@pytest.mark.parametrize(
    "mismatch",
    [
        "checkpoint",
        "normalization",
        "preprocessing",
        "conditions",
        "exclusion",
        "roster_count",
        "roster_digest",
        "git_sha",
        "dirty",
        "manifest_dirty",
    ],
)
def test_mismatch_writes_nothing_and_reads_no_labels(
    harness: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
) -> None:
    doc = harness["document"]
    changed = {
        "checkpoint": harness["weights"],
        "normalization": harness["data"] / "manifests/normalization.json",
        "preprocessing": harness["repo"] / "preprocessing.yaml",
        "conditions": harness["repo"] / "conditions.yaml",
        "exclusion": harness["data"] / "manifests/exclusions.json",
    }
    if mismatch in changed:
        with changed[mismatch].open("ab") as stream:
            stream.write(b"changed")
    elif mismatch.startswith("roster"):
        post_qc = json.loads(harness["post_qc"].read_text())
        entry = post_qc["cohorts"]["ucsf_pdgm"]
        entry[
            "retained_patient_count" if mismatch == "roster_count" else "roster_sha256"
        ] = 3 if mismatch == "roster_count" else "f" * 64
        harness["post_qc"].write_text(json.dumps(post_qc))
    elif mismatch == "git_sha":
        monkeypatch.setattr(driver, "git_state", lambda _: ("b" * 40, True))
    elif mismatch == "dirty":
        monkeypatch.setattr(driver, "git_state", lambda _: (SHA, False))
    elif mismatch == "manifest_dirty":
        doc["git_tree_clean"] = False
        _seal(harness["manifest"], doc)
    monkeypatch.setattr(
        ucsf_pdgm, "load_labels", lambda: pytest.fail("labels read before verification")
    )
    with pytest.raises(driver.FreezeMismatchError):
        driver.run_external_evaluation(STAND_IN, "test-run", device="cpu")
    assert not harness["output"].exists()


@pytest.mark.parametrize("problem", ["unsigned", "unsealed"])
def test_unsigned_and_unsealed_rejected(harness: dict[str, Any], problem: str) -> None:
    harness["document"]["authorizing_signature"]["name"] = None
    if problem == "unsigned":
        _seal(harness["manifest"], harness["document"])
    else:
        harness["manifest"].write_text(json.dumps(harness["document"]))
    with pytest.raises(firewall.ExternalEvaluationNotAuthorized):
        driver.run_external_evaluation(STAND_IN, "test-run")
    assert not harness["output"].exists()


def test_existing_directory_untouched(harness: dict[str, Any]) -> None:
    output = harness["output"]
    output.mkdir(parents=True)
    sentinel = output / "original"
    sentinel.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        driver.run_external_evaluation(STAND_IN, "test-run", device="cpu")
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"original"


def test_post_run_sha_mismatch_is_refused(
    harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    states = iter(((SHA, True), ("b" * 40, True)))
    monkeypatch.setattr(driver, "git_state", lambda _: next(states))
    with pytest.raises(driver.FreezeMismatchError, match="post-run"):
        driver.run_external_evaluation(STAND_IN, "test-run", device="cpu")
    assert not (harness["output"] / "report.json").exists()


def test_adapter_is_guarded_directly(
    harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(firewall.FLAG_NAME)
    harness["labels"].unlink()
    with pytest.raises(firewall.ExternalEvaluationNotAuthorized):
        ucsf_pdgm.load_labels()


def test_audit_has_no_blocking_findings() -> None:
    from scripts.audit_external_leak import run_audit

    result = run_audit(Path(__file__).parents[2])
    assert result["blocking_count"] == 0


@pytest.mark.parametrize(
    "value",
    [
        "IDH1 p.R132H",
        "IDH1 p.R132C",
        "IDH1 p.R132G",
        "IDH1 p.R132S",
        "IDH1 p.Arg132His",
        "IDH2 p.R172K",
        "IDH2 p.Arg172Trp",
        "mutated (NOS)",
        "wildtype",
    ],
)
def test_published_idh_mapping(harness: dict[str, Any], value: str) -> None:
    harness["labels"].write_text(f"ID,IDH\nUCSF-PDGM-001,{value}\n")
    assert ucsf_pdgm.load_labels() == {
        "UCSF-PDGM-0001": "wildtype" if value == "wildtype" else "mutant"
    }


@pytest.mark.parametrize(
    "content",
    [
        "ID,IDH\nUCSF-PDGM-001,unknown\n",
        "ID,IDH\nUCSF-PDGM-001,wildtype\nUCSF-PDGM-0001,wildtype\n",
        "ID,other\nUCSF-PDGM-001,wildtype\n",
    ],
)
def test_label_parser_fails_closed(harness: dict[str, Any], content: str) -> None:
    harness["labels"].write_text(content)
    with pytest.raises(ValueError):
        ucsf_pdgm.load_labels()


def test_cli_help_works_with_source_pythonpath(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    repo = Path(__file__).parents[2]
    result = subprocess.run(
        [sys.executable, str(repo / "scripts/run_external_evaluation.py"), "--help"],
        cwd=repo,
        env={
            **os.environ,
            "PYTHONPATH": "src",
            firewall.FLAG_NAME: "0",
            "MPLCONFIGDIR": str(tmp_path / "mpl"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--cohort {ucsf_pdgm}" in result.stdout
