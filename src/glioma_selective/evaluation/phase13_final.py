"""Phase 13 final step: one Benjamini-Hochberg pass and the claim table (T13.2, T13.3).

Reads the four frozen aggregate files (internal and external Phase 09 and Phase 10
analysis), checks each against its SHA-256 sidecar, pools the confirmatory p-values
into one family, applies BH at q = 0.05 once (D-052) and copies each claim's frozen
status. It recomputes no metric and fits nothing; adjudication is the frozen rule's
status, restated, not re-derived.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from glioma_selective.evaluation.condition_analysis import _read_json_with_sidecar
from glioma_selective.statistics.multiplicity import benjamini_hochberg

FAMILY_SIZE = 29
Q = 0.05
CLAIM_IDS = ("C1", "C2", "C3", "C4", "C5", "C6")
SCHEMA = "phase13_final_analysis.v1"


class FamilyError(ValueError):
    """The pooled family does not match the pre-registered composition."""


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _family(
    internal10: dict[str, Any], external10: dict[str, Any]
) -> list[tuple[str, float]]:
    expected = [row["id"] for row in internal10["bh_family"]]
    pooled: list[tuple[str, float]] = []
    for cohort, document in (("utsw", internal10), ("ucsf_pdgm", external10)):
        for key, row in document["confirmatory"].items():
            if row.get("status") != "computed" or row.get("p_value") is None:
                raise FamilyError(f"{cohort}:{key} has no computed p-value")
            pooled.append((f"{cohort}:{key}", _p_value(row["p_value"])))
    ids = [member for member, _ in pooled]
    if len(ids) != FAMILY_SIZE or len(set(ids)) != FAMILY_SIZE:
        raise FamilyError(f"family has {len(ids)} members, expected {FAMILY_SIZE}")
    if sorted(ids) != sorted(expected):
        raise FamilyError("pooled members differ from the pre-registered family")
    return pooled


def _p_value(value: Any) -> float:
    """Frozen permutation p-values are stored as reduced fraction strings."""
    return float(Fraction(value)) if isinstance(value, str) else float(value)


def _claims(internal09: dict[str, Any], external09: dict[str, Any]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for claim in CLAIM_IDS:
        internal = internal09["claims"].get(claim, {})
        external = external09["claims"].get(claim)
        table[claim] = {
            "internal": internal.get("worst_status", internal.get("status")),
            "external": (
                None
                if external is None
                else external.get("worst_status", external.get("status"))
            ),
        }
    # C3 is defined on external data; its frozen headline is the `full` condition and
    # the worst status over conditions is reported beside it (freeze spec).
    table["C3"]["external_headline_full"] = external09["claims"]["C3"]["status"]
    table["C3"]["external_worst_over_conditions"] = external09["claims"]["C3"][
        "secondary_worst_status"
    ]
    return table


def finalize(
    internal09: Path,
    internal10: Path,
    external09: Path,
    external10: Path,
    output: Path,
) -> Path:
    """Write ``output`` (write-once) and its SHA-256 sidecar."""
    sidecar = output.with_name(output.name + ".sha256")
    if output.exists() or sidecar.exists():
        raise FileExistsError(f"{output.name} already exists")
    i09 = _read_json_with_sidecar(internal09)
    i10 = _read_json_with_sidecar(internal10)
    e09 = _read_json_with_sidecar(external09)
    e10 = _read_json_with_sidecar(external10)
    pooled = _family(i10, e10)
    adjusted, reject = benjamini_hochberg([p for _, p in pooled], Q)  # type: ignore[misc]
    rows = [
        {
            "id": member,
            "raw_p_value": p,
            "bh_adjusted_p_value": str(value),
            "bh_adjusted_p_value_float": float(value),
            "reject_q_0.05": bool(flag),
        }
        for (member, p), value, flag in zip(pooled, adjusted, reject, strict=True)
    ]
    document = {
        "schema": SCHEMA,
        "family": {
            "size": FAMILY_SIZE,
            "q": Q,
            "rule": "one Benjamini-Hochberg pass over 14 UTSW and 15 UCSF-PDGM "
            "confirmatory comparisons (D-052); raw p-values from the frozen files",
            "members": rows,
            "n_rejected": sum(1 for row in rows if row["reject_q_0.05"]),
        },
        "claims": _claims(i09, e09),
        "inputs": {
            path.name: _digest(path)
            for path in (internal09, internal10, external09, external10)
        },
    }
    payload = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    output.write_bytes(payload)
    sidecar.write_text(
        f"{hashlib.sha256(payload).hexdigest()}  {output.name}\n", encoding="ascii"
    )
    return output
