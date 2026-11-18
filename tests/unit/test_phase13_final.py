"""Phase 13 final step: pooled BH over 29 tests and the claim table."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from glioma_selective.evaluation.phase13_final import FamilyError, finalize

INTERNAL = [
    "A1",
    "A2",
    "A3",
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "D1",
    "D2",
    "E1",
    "E2",
    "E3",
    "E4",
]
EXTERNAL = [*INTERNAL[:10], "C1", *INTERNAL[10:]]


def _write(path: Path, document: dict[str, Any]) -> Path:
    payload = json.dumps(document).encode()
    path.write_bytes(payload)
    path.with_name(path.name + ".sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  {path.name}\n", encoding="ascii"
    )
    return path


def _files(
    tmp_path: Path, p_values: list[Any], external_keys: list[str] | None = None
) -> tuple[Path, Path, Path, Path]:
    keys = external_keys or EXTERNAL
    members = [f"utsw:{k}" for k in INTERNAL] + [f"ucsf_pdgm:{k}" for k in EXTERNAL]
    iterator = iter(p_values)
    row = lambda: {"status": "computed", "p_value": next(iterator)}  # noqa: E731
    internal10 = {
        "bh_family": [{"id": m} for m in members],
        "confirmatory": {k: row() for k in INTERNAL},
    }
    external10 = {"confirmatory": {k: row() for k in keys}}
    claims_i = {
        c: {"worst_status": "supported"} for c in ("C1", "C2", "C4", "C5", "C6")
    }
    claims_i["C3"] = {"status": "not evaluated"}
    claims_e = {c: {"worst_status": "refuted"} for c in ("C4", "C5", "C6")} | {
        "C3": {"status": "supported", "secondary_worst_status": "inconclusive"}
    }
    return (
        _write(tmp_path / "i09.json", {"claims": claims_i}),
        _write(tmp_path / "i10.json", internal10),
        _write(tmp_path / "e09.json", {"claims": claims_e}),
        _write(tmp_path / "e10.json", external10),
    )


def test_bh_hand_calculation(tmp_path: Path) -> None:
    # p_k = k/1000, k = 1..28: adjusted 0.029 each; p = 0.9 at rank 29 stays 0.9.
    p = [f"{k}/1000" for k in range(1, 29)] + [0.9]
    i09, i10, e09, e10 = _files(tmp_path, p)
    out = finalize(i09, i10, e09, e10, tmp_path / "final.json")
    doc = json.loads(out.read_text())
    rows = doc["family"]["members"]
    assert len(rows) == 29 and doc["family"]["n_rejected"] == 28
    assert {r["bh_adjusted_p_value"] for r in rows if r["reject_q_0.05"]} == {
        str(Fraction(29, 1000))
    }
    assert [r for r in rows if not r["reject_q_0.05"]][0][
        "bh_adjusted_p_value"
    ] == "9/10"
    sidecar = out.with_name("final.json.sha256").read_text().split()[0]
    assert sidecar == hashlib.sha256(out.read_bytes()).hexdigest()


def test_claim_table_restates_frozen_status(tmp_path: Path) -> None:
    i09, i10, e09, e10 = _files(tmp_path, [0.5] * 29)
    doc = json.loads(finalize(i09, i10, e09, e10, tmp_path / "f.json").read_text())
    assert doc["claims"]["C3"]["external_headline_full"] == "supported"
    assert doc["claims"]["C3"]["external_worst_over_conditions"] == "inconclusive"
    assert doc["claims"]["C4"] == {"internal": "supported", "external": "refuted"}


def test_wrong_family_is_refused(tmp_path: Path) -> None:
    i09, i10, e09, e10 = _files(tmp_path, [0.5] * 28, [*EXTERNAL[:-1]])
    with pytest.raises(FamilyError):
        finalize(i09, i10, e09, e10, tmp_path / "f.json")


def test_output_is_write_once_and_tamper_is_caught(tmp_path: Path) -> None:
    i09, i10, e09, e10 = _files(tmp_path, [0.5] * 29)
    finalize(i09, i10, e09, e10, tmp_path / "f.json")
    with pytest.raises(FileExistsError):
        finalize(i09, i10, e09, e10, tmp_path / "f.json")
    e10.write_bytes(e10.read_bytes() + b" ")
    with pytest.raises(ValueError, match="sidecar"):
        finalize(i09, i10, e09, e10, tmp_path / "g.json")
