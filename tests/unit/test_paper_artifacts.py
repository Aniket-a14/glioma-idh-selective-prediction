"""Phase 13 rules 1-10, exercised on frozen synthetic assembler output only."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from tests.unit import test_paper_tables as support

from glioma_selective.cli import build_paper_artifacts as builder
from glioma_selective.evaluation.firewall import (
    FLAG_NAME,
    MANIFEST_FIELDS,
    ExternalEvaluationNotAuthorized,
)
from glioma_selective.visualization.abstention import abstention_figure
from glioma_selective.visualization.coverage import coverage_figure
from glioma_selective.visualization.reliability import reliability_figure
from glioma_selective.visualization.risk_coverage import (
    figure_style,
    risk_coverage_figure,
)

frozen_run = support.frozen_run
documents = support.documents
write_json = support.write_json

REPO = Path(__file__).resolve().parents[2]
MODULES = [
    REPO / "src/glioma_selective/cli/build_paper_artifacts.py",
    *sorted((REPO / "src/glioma_selective/visualization").glob("*.py")),
]


def set_roots(monkeypatch: pytest.MonkeyPatch, frozen_run: Path) -> None:
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(frozen_run.parents[2]))
    monkeypatch.delenv("GLIOMA_ARTIFACT_ROOT", raising=False)
    monkeypatch.delenv("GLIOMA_DATA_ROOT", raising=False)
    monkeypatch.setenv(FLAG_NAME, "0")


def test_rc_every_point_and_both_intervals_survive(frozen_run: Path) -> None:
    phase09, _ = documents(frozen_run)
    with figure_style():
        fig, caption = risk_coverage_figure(phase09)
    axes = fig.axes[::2]
    for ax, condition in zip(axes, sorted(phase09["conditions"]), strict=True):
        cells = phase09["conditions"][condition]
        present = [
            cells[name]
            for name in ("M1", "M2", "M3", "M4", "M5", "M6")
            if not cells[name].get("absent")
        ]
        assert len(ax.lines) == len(present)
        for line, cell in zip(ax.lines, present, strict=True):
            np.testing.assert_array_equal(line.get_xydata(), cell["rc_points"])
        segments = [collection.get_segments()[0] for collection in ax.collections]
        expected = []
        for cell in present:
            for _, op in sorted(cell["selective_risk_at_coverage"].items()):
                expected.extend(
                    (
                        [
                            [op["attained_coverage"], op["risk_95_interval"]["lower"]],
                            [op["attained_coverage"], op["risk_95_interval"]["upper"]],
                        ],
                        [
                            [op["attained_coverage_95_interval"]["lower"], op["risk"]],
                            [op["attained_coverage_95_interval"]["upper"], op["risk"]],
                        ],
                    )
                )
        np.testing.assert_array_equal(segments, expected)
        assert ax.get_xlim() == ax.get_ylim() == (0, 1)
    assert "between operating points has no stored intervals" in caption
    fig.clear()


def test_absent_figure_slots_include_reason_and_no_fake_line(frozen_run: Path) -> None:
    phase09, _ = documents(frozen_run)
    for factory in (risk_coverage_figure, abstention_figure):
        with figure_style():
            fig, _ = factory(phase09)
        for ax, slot, condition in zip(
            fig.axes[::2], fig.axes[1::2], sorted(phase09["conditions"]), strict=True
        ):
            assert len(ax.lines) == 4
            text = " ".join(item.get_text().replace("\n", " ") for item in slot.texts)
            for mechanism in ("M4", "M6"):
                assert mechanism in text and "absent" in text
                assert phase09["conditions"][condition][mechanism]["reason"] in text
        fig.clear()


def test_all_generated_figure_captions_label_simulation(frozen_run: Path) -> None:
    phase09, _ = documents(frozen_run)
    frames, _ = builder._prediction_frames(frozen_run, phase09, "R2")
    with figure_style():
        figures = [
            factory(phase09)
            for factory in (risk_coverage_figure, coverage_figure, abstention_figure)
        ]
        figures.append(
            reliability_figure(
                frames, phase09["provenance"]["full_temperature"], "utsw_internal_test"
            )
        )
    for fig, caption in figures:
        assert "simulated" in caption
        for ax in fig.axes:
            if ax.get_title().startswith("drop_") or ax.get_title().startswith(
                "t1ce_flair_only"
            ):
                assert "simulated" in ax.get_title()
        fig.clear()


def test_no_literal_result_values_in_sources() -> None:
    # Grep numeric results in labels and literal result dictionaries; named
    # constants (precision, layout, axis limits and tolerance) are permitted.
    result_keys = {
        "risk",
        "auroc",
        "ece",
        "brier",
        "aurc",
        "empirical_coverage",
        "count",
        "rejected_but_correct_rate",
    }
    for path in MODULES:
        tree = ast.parse(path.read_text())
        allowed = set()
        for assignment in tree.body:
            if isinstance(assignment, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "COLUMN_DIGITS"
                for target in assignment.targets
            ):
                allowed.update(id(node) for node in ast.walk(assignment))
        for node in ast.walk(tree):
            if id(node) in allowed:
                continue
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    if isinstance(key, ast.Constant) and key.value in result_keys:
                        assert not (
                            isinstance(value, ast.Constant)
                            and isinstance(value.value, int | float)
                        ), (path, node.lineno)
            if isinstance(node, ast.FormattedValue):
                assert not (
                    isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, int | float)
                ), (path, node.lineno)


def test_import_graph_has_no_models_or_training_or_checkpoint_reads() -> None:
    pending = list(MODULES)
    visited = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
                if node.module in (
                    "glioma_selective.evaluation",
                    "glioma_selective.utils",
                ):
                    modules += [node.module + "." + name.name for name in node.names]
            elif isinstance(node, ast.Import):
                modules = [name.name for name in node.names]
            else:
                continue
            for module in modules:
                assert not module.startswith(
                    ("glioma_selective.models", "glioma_selective.training")
                )
                if module.startswith("glioma_selective"):
                    candidate = REPO / "src" / (module.replace(".", "/") + ".py")
                    if candidate.exists():
                        pending.append(candidate)
        assert not any(
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.endswith(".pt")
            for node in ast.walk(tree)
        )


@pytest.mark.parametrize("cohort", ["ucsf_pdgm", "egd"])
def test_external_guard_precedes_any_file_open(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, cohort: str
) -> None:
    monkeypatch.setenv(FLAG_NAME, "0")
    with pytest.raises(ExternalEvaluationNotAuthorized):
        builder.build_paper_artifacts(
            "missing",
            out_dir=tmp_path / "out",
            external_analyses=((cohort, tmp_path / "does-not-exist.json"),),
        )
    assert not (tmp_path / "out").exists()


def test_external_explicit_path_calls_existing_firewall(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Isolated fake freeze manifest; never authorizes or opens a real external file.
    source = tmp_path / "synthetic_external.json"
    write_json(source, {"synthetic": True})
    manifest = {field: "synthetic" for field in MANIFEST_FIELDS}
    manifest["authorizing_signature"] = {
        "name": "Synthetic test only",
        "date": "synthetic",
    }
    manifest_path = tmp_path / "freeze_manifest.json"
    write_json(manifest_path, manifest)
    monkeypatch.setenv(FLAG_NAME, "1")
    monkeypatch.setattr(builder.firewall, "freeze_manifest_path", lambda: manifest_path)
    assert builder.load_external_analysis("ucsf_pdgm", source).document() == {
        "synthetic": True
    }


@pytest.mark.parametrize("kind", ["missing", "mismatch"])
def test_sidecar_is_mandatory_and_checked_before_json_parse(
    tmp_path: Path, kind: str
) -> None:
    path = tmp_path / "frozen.json"
    path.write_bytes(b"not JSON")
    if kind == "mismatch":
        path.with_suffix(".json.sha256").write_text("0" * 64)
    with pytest.raises(ValueError, match="SHA-256"):
        builder.FrozenInput.read(path)


def test_paper_output_is_refused_before_any_input_read() -> None:
    with pytest.raises(ValueError, match="human-owned"):
        builder.build_paper_artifacts("missing", out_dir=REPO / "paper/figures")


def test_required_key_is_not_filled_in(frozen_run: Path) -> None:
    phase09, _ = documents(frozen_run)
    del phase09["conditions"]["full"]["M1"]["rc_points"]
    with pytest.raises(KeyError, match="rc_points"):
        risk_coverage_figure(phase09)


def test_m6_overlay_preserves_main_claims_and_rejects_wrong_run(
    frozen_run: Path,
) -> None:
    phase09, _ = documents(frozen_run)
    extra = json.loads((frozen_run / "phase09_m6_analysis.json").read_text())
    with pytest.raises(ValueError, match="M6 run_id"):
        builder._merge_m6(phase09, extra, "wrong")
    original_claims = json.dumps(phase09["claims"], sort_keys=True)
    builder._merge_m6(phase09, extra, "R1")
    assert json.dumps(phase09["claims"], sort_keys=True) == original_claims
    assert phase09["conditions"]["full"]["M6"] == extra["conditions"]["full"]


def test_cli_builds_without_torch_or_checkpoint_access_and_copies_claims(
    frozen_run: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    set_roots(monkeypatch, frozen_run)
    out = tmp_path / "output with spaces"
    program = r"""
import builtins
import sys
from pathlib import Path
class BlockTorch:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch."):
            raise AssertionError("torch import forbidden")
sys.meta_path.insert(0, BlockTorch())
original_open = builtins.open
def guarded_open(path, *args, **kwargs):
    if isinstance(path, (str, bytes, Path)) and str(path).endswith(".pt"):
        raise AssertionError("checkpoint read forbidden")
    return original_open(path, *args, **kwargs)
builtins.open = guarded_open
from glioma_selective.cli.build_paper_artifacts import main
raise SystemExit(main(sys.argv[1:]))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            "--run-id",
            "R2",
            "--m6-run-id",
            "R1",
            "--out-dir",
            str(out),
        ],
        env={**os.environ, "PYTHONPATH": str(REPO / "src")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(list(out.glob("*.png"))) == len(list(out.glob("*.pdf"))) == 5
    assert len(list(out.glob("*.csv"))) == len(list(out.glob("*.tex"))) == 6
    phase09, _ = documents(frozen_run)
    assert json.loads((out / "CLAIMS.json").read_text()) == {"utsw": phase09["claims"]}
    registry = (out / "REGISTRY_ROWS.md").read_text()
    assert registry.count("GENERATED") == 11
    assert registry.splitlines()[0] == builder.REGISTRY_HEADER
    assert (
        hashlib.sha256((frozen_run / "phase09_analysis.json").read_bytes()).hexdigest()[
            :12
        ]
        in registry
    )
    assert "--m6-run-id R1" in registry
    assert "ucsf_pdgm" not in registry and "egd" not in registry
    # Execute the exact registry command rather than merely inspect its spelling.
    command = registry.splitlines()[2].split(" | ")[3].strip("`")
    replay = subprocess.run(
        command, shell=True, cwd=REPO, capture_output=True, text=True
    )
    assert replay.returncode == 0, replay.stderr


def test_absence_labels_do_not_overlap_each_other_or_axes(frozen_run: Path) -> None:
    phase09, _ = documents(frozen_run)
    with figure_style():
        fig, _ = risk_coverage_figure(phase09)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for ax, slot in zip(fig.axes[::2], fig.axes[1::2], strict=True):
            labels = [text.get_window_extent(renderer) for text in slot.texts]
            xlabel = ax.xaxis.label.get_window_extent(renderer)
            assert all(not label.overlaps(xlabel) for label in labels)
            assert not labels[0].overlaps(labels[1])
    fig.clear()


def test_cohort_flow_copies_source_retained_and_excluded_counts(
    frozen_run: Path,
) -> None:
    root = frozen_run.parents[2]
    cohort = json.loads(
        (root / "data/manifests/cohort_manifest_post_qc.json").read_text()
    )
    exclusion = json.loads(
        (root / "data/manifests/exclusion_manifest_post_qc.json").read_text()
    )
    with figure_style():
        fig, _ = builder.cohort_flow_figure(cohort, exclusion)
    texts = [text.get_text() for ax in fig.axes for text in ax.texts]
    assert (
        f"Source patients: {exclusion['cohorts']['utsw']['source_patient_count']}"
        in texts
    )
    assert f"Retained: {cohort['cohorts']['utsw']['retained_patient_count']}" in texts
    assert f"Excluded: {cohort['cohorts']['utsw']['excluded_patient_count']}" in texts
    fig.clear()


def test_manifest_without_sidecar_is_marked_unsealed_but_mismatch_still_fails(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cohort_manifest_post_qc.json"
    path.write_text("{}")
    unsealed = builder.FrozenInput.read(path, require_sidecar=False)
    assert unsealed.sealed is False
    assert unsealed.registry_source().endswith("(no sidecar)")
    with pytest.raises(ValueError, match="sidecar"):
        builder.FrozenInput.read(path)
    path.with_suffix(".json.sha256").write_text("0" * 64)
    with pytest.raises(ValueError, match="mismatch"):
        builder.FrozenInput.read(path, require_sidecar=False)


def test_manifest_path_falls_back_to_committed_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(tmp_path))
    found = builder._manifest_path("cohort_manifest_post_qc.json")
    assert found == REPO / "docs/research/manifests/cohort_manifest_post_qc.json"
