"""The external-analysis seam must not change any internal analysis output.

``phase09_analysis`` and ``phase10_analysis`` gained an optional ``test_cohort``
argument so the same frozen code paths can score UCSF-PDGM. This test runs both
analyses on the synthetic fixtures and compares the JSON (without the git SHA,
which changes with every commit) against digests recorded from the code before
the seam existed (``tests/fixtures/external_seam_internal_digests.json``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from tests.unit import test_phase09_analysis as p09
from tests.unit import test_phase10_analysis as p10

from glioma_selective.evaluation import phase09_analysis, phase10_analysis

FIXTURE = Path(__file__).parents[1] / "fixtures" / "external_seam_internal_digests.json"


def _strip(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k != "git_sha"}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def _digest(path: Path) -> str:
    document = _strip(json.loads(path.read_text()))
    payload = json.dumps(document, sort_keys=True, allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def current_digests(root: Path, patch: pytest.MonkeyPatch) -> dict[str, str]:
    run09 = "R2"
    p09._prepare(root / "p09", patch, run09)
    for member in ("R3", "R4", "R5", "R6"):
        p09._prepare(root / "p09", patch, member)
    report09 = phase09_analysis.analyze_phase09(
        run09,
        ensemble_run_ids=("R3", "R4", "R5", "R6"),
        iterations=60,
        permutations=200,
        seed=0,
    )
    p10._all_runs(root / "p10", ablations=True)
    patch.setenv("GLIOMA_ARTIFACT_ROOT", str(root / "p10"))
    report10 = phase10_analysis.analyze_phase10(
        "R2",
        ensemble_run_ids=p10.MEMBERS,
        r7_run_id="R7",
        r8_run_id="R8",
        iterations=1000,
    )
    return {"phase09": _digest(report09), "phase10": _digest(report10)}


def test_internal_outputs_are_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = json.loads(FIXTURE.read_text())
    assert current_digests(tmp_path, monkeypatch) == expected
