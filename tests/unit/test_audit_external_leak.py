"""T11.7 audit: each check fires on a planted leak, quiet on a clean tree."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "audit_external_leak",
    Path(__file__).resolve().parents[2] / "scripts" / "audit_external_leak.py",
)
assert _SPEC is not None and _SPEC.loader is not None
audit = importlib.util.module_from_spec(_SPEC)
sys.modules["audit_external_leak"] = audit
_SPEC.loader.exec_module(audit)

LOG_HEADER = "| Date | Event |\n|---|---|\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    base = tmp_path / "src" / "glioma_selective"
    for name in ("models", "training", "selective", "data", "evaluation"):
        (base / name).mkdir(parents=True)
        (base / name / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests" / "fixtures").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "paper").mkdir()
    log = tmp_path / "docs" / "research" / "protocols"
    log.mkdir(parents=True)
    (log / "GATE_E_LOG.md").write_text(LOG_HEADER, encoding="utf-8")
    return tmp_path


def _run(repo: Path, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("environ", {})
    return audit.run_audit(repo, **kwargs)


def _checks(report: dict[str, Any], blocking: bool = True) -> set[str]:
    return {f["check"] for f in report["findings"] if f["blocking"] == blocking}


def test_clean_tree_has_no_blocking_findings(repo: Path) -> None:
    report = _run(repo)
    assert report["blocking_count"] == 0


def test_flag_in_environment(repo: Path) -> None:
    assert "flag" in _checks(_run(repo, environ={audit.FLAG: "1"}))


@pytest.mark.parametrize(
    "line",
    ["GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1", "export GLIOMA_EXTERNAL_EVAL_AUTHORIZED='1'"],
)
def test_flag_in_dotenv(repo: Path, line: str) -> None:
    (repo / ".env").write_text(line + "\n", encoding="utf-8")
    assert "flag" in _checks(_run(repo))


def test_flag_zero_in_dotenv_is_fine(repo: Path) -> None:
    (repo / ".env").write_text("GLIOMA_EXTERNAL_EVAL_AUTHORIZED=0\n", encoding="utf-8")
    assert _run(repo)["blocking_count"] == 0


def test_model_code_naming_external_cohort(repo: Path) -> None:
    path = repo / "src" / "glioma_selective" / "training" / "loop.py"
    path.write_text("COHORT = 'ucsf_pdgm'\n", encoding="utf-8")
    assert "model_code" in _checks(_run(repo))


def test_label_reader_outside_allowlist(repo: Path) -> None:
    path = repo / "src" / "glioma_selective" / "evaluation" / "report.py"
    path.write_text("p = paths.external_data_dir() / 'x.csv'\n", encoding="utf-8")
    assert "label_readers" in _checks(_run(repo))


def test_label_reader_inside_allowlist(repo: Path) -> None:
    path = repo / "src" / "glioma_selective" / "data" / "metadata.py"
    path.write_text(
        "p = paths.external_data_dir() / 'UCSF-PDGM-metadata_v2.csv'\n",
        encoding="utf-8",
    )
    assert "label_readers" not in _checks(_run(repo))


def test_fixture_with_patient_id(repo: Path) -> None:
    (repo / "tests" / "fixtures" / "ids.json").write_text(
        '["UCSF-PDGM-0004"]', encoding="utf-8"
    )
    assert "fixtures" in _checks(_run(repo))


def test_artifact_with_cohort_and_metric(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    root = tmp_path_factory.mktemp("artifacts")
    (root / "run").mkdir()
    (root / "run" / "metrics.json").write_text(
        '{"ucsf_pdgm": {"auroc": 0.81}}\n', encoding="utf-8"
    )
    assert "artifacts" in _checks(_run(repo, artifact_roots=[root]))


def test_artifact_comparison_label_without_number_is_clean(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    root = tmp_path_factory.mktemp("artifacts")
    (root / "analysis.json").write_text(
        '{"cohort": "ucsf_pdgm", "comparison": "AURC(M5, ucsf_pdgm)", "p": null}',
        encoding="utf-8",
    )
    assert _run(repo, artifact_roots=[root])["blocking_count"] == 0


def test_artifact_text_log_line_with_number(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    root = tmp_path_factory.mktemp("artifacts")
    (root / "run.log").write_text("ucsf auroc 0.8123\n", encoding="utf-8")
    assert "artifacts" in _checks(_run(repo, artifact_roots=[root]))


def test_artifact_internal_only_is_clean(
    repo: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    root = tmp_path_factory.mktemp("artifacts")
    (root / "metrics.json").write_text('{"utsw": {"auroc": 0.88}}\n', encoding="utf-8")
    assert _run(repo, artifact_roots=[root])["blocking_count"] == 0


def test_unreadable_artifact_root_is_a_review_item(repo: Path, tmp_path: Path) -> None:
    report = _run(repo, artifact_roots=[tmp_path / "missing"])
    assert "artifacts" in _checks(report, blocking=False)
    assert report["blocking_count"] == 0


def test_doc_line_is_review_not_blocking(repo: Path) -> None:
    (repo / "docs" / "note.md").write_text("UCSF-PDGM AUROC 0.8123\n", encoding="utf-8")
    report = _run(repo)
    assert "docs" in _checks(report, blocking=False)
    assert report["blocking_count"] == 0


def test_gate_log_entry_blocks(repo: Path) -> None:
    log = repo / "docs" / "research" / "protocols" / "GATE_E_LOG.md"
    log.write_text(LOG_HEADER + "| 2027-01-05 | authorized |\n", encoding="utf-8")
    assert "gate_log" in _checks(_run(repo))


def test_missing_gate_log_blocks(repo: Path) -> None:
    (repo / "docs" / "research" / "protocols" / "GATE_E_LOG.md").unlink()
    assert "gate_log" in _checks(_run(repo))


def test_main_exit_code(repo: Path) -> None:
    assert audit.main(["--repo", str(repo)]) == 0
    (repo / "tests" / "fixtures" / "ids.json").write_text(
        "UCSF-PDGM-0004", encoding="utf-8"
    )
    assert audit.main(["--repo", str(repo)]) == 1
