"""External-evaluation firewall (EXTERNAL_VALIDATION_PROTOCOL.md section 2, Phase 11).

Every code path that joins UCSF-PDGM or EGD predictions to their labels, or reads an
external performance number, calls ``assert_external_eval_authorized`` first. It raises
unless both hold:

1. ``GLIOMA_EXTERNAL_EVAL_AUTHORIZED`` is exactly ``"1"`` in the environment (unset,
   ``0`` and anything else do not count), and
2. a signed freeze manifest exists at ``experiments/gate_e/freeze_manifest.json`` under
   the artifact root, its SHA-256 sidecar matches the file, all fifteen manifest
   fields are present and non-empty, and the authorizing signature has a name and
   a date.

Flipping the flag is a logged, dated, Research-Lead-only action (``GATE_E_LOG.md``).
This is defence in depth: a determined operator who owns the flag can bypass it, and the
procedural controls matter more. Error messages never contain label or metric values.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from glioma_selective.utils import paths

__all__ = [
    "EXTERNAL_COHORTS",
    "FLAG_NAME",
    "MANIFEST_FIELDS",
    "ExternalEvaluationNotAuthorized",
    "assert_external_eval_authorized",
    "freeze_manifest_path",
]

FLAG_NAME = "GLIOMA_EXTERNAL_EVAL_AUTHORIZED"
EXTERNAL_COHORTS = ("ucsf_pdgm", "egd")

# The fifteen fields of the freeze manifest (PHASE_11 "The freeze manifest").
MANIFEST_FIELDS = (
    "code_commit_sha",
    "model_checkpoints",
    "preprocessing",
    "normalization_statistics",
    "exclusion_manifest",
    "utsw_split_manifest",
    "calibration_parameters",
    "conformal",
    "abstention_definition",
    "operating_points",
    "missing_modality_conditions",
    "primary_metrics",
    "c4_tolerance_band",
    "statistical_analysis_plan",
    "authorizing_signature",
)


class ExternalEvaluationNotAuthorized(PermissionError):
    """Raised when external labels or performance are requested before Gate E."""


def freeze_manifest_path() -> Path:
    """Where the signed freeze manifest must live (under the artifact root)."""
    return paths.experiments_dir() / "gate_e" / "freeze_manifest.json"


def _empty(value: Any) -> bool:
    return value is None or (hasattr(value, "__len__") and len(value) == 0)


def _check_manifest(manifest_path: Path) -> None:
    sidecar = manifest_path.with_name(manifest_path.name + ".sha256")
    try:
        content = manifest_path.read_bytes()
    except OSError as error:
        raise ExternalEvaluationNotAuthorized(
            "no freeze manifest at the Gate E location"
        ) from error
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0]
    except (OSError, UnicodeError, IndexError) as error:
        raise ExternalEvaluationNotAuthorized(
            "freeze manifest has no readable SHA-256 sidecar"
        ) from error
    if hashlib.sha256(content).hexdigest() != expected:
        raise ExternalEvaluationNotAuthorized(
            "freeze manifest does not match its SHA-256 sidecar"
        )
    try:
        document = json.loads(content)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ExternalEvaluationNotAuthorized(
            "freeze manifest is not valid JSON"
        ) from error
    if not isinstance(document, dict):
        raise ExternalEvaluationNotAuthorized("freeze manifest must be a JSON object")
    missing = [field for field in MANIFEST_FIELDS if _empty(document.get(field))]
    if missing:
        raise ExternalEvaluationNotAuthorized(
            f"freeze manifest fields missing or empty: {', '.join(missing)}"
        )
    signature = document["authorizing_signature"]
    if (
        not isinstance(signature, dict)
        or _empty(signature.get("name"))
        or _empty(signature.get("date"))
    ):
        raise ExternalEvaluationNotAuthorized(
            "freeze manifest is not signed: authorizing_signature needs name and date"
        )


def assert_external_eval_authorized(
    cohort: str,
    *,
    environ: Mapping[str, str] | None = None,
    manifest_path: Path | None = None,
) -> None:
    """Raise ``ExternalEvaluationNotAuthorized`` unless Gate E has been passed.

    ``cohort`` must be an external cohort (``ucsf_pdgm`` or ``egd``); any other name,
    UTSW included, is a ``ValueError`` so a typo cannot slip past the guard.
    """
    if cohort not in EXTERNAL_COHORTS:
        raise ValueError(
            f"the firewall guards external cohorts {EXTERNAL_COHORTS}, not {cohort!r}"
        )
    env = os.environ if environ is None else environ
    if env.get(FLAG_NAME) != "1":
        raise ExternalEvaluationNotAuthorized(
            f"{FLAG_NAME} is not 1: external labels and performance are blocked "
            f"until Gate E ({cohort})"
        )
    _check_manifest(freeze_manifest_path() if manifest_path is None else manifest_path)
