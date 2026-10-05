"""Frozen Phase 06 prediction artifacts.

``patient_id`` stores the first 16 hexadecimal characters of SHA-256 over the
canonical UTSW patient identifier. Raw identifiers must never be committed or
printed; prediction artifacts belong under the external ``artifacts/`` root.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from glioma_selective.tracking.run_record import sha256_file

__all__ = [
    "PREDICTION_COLUMNS",
    "hash_patient_id",
    "read_prediction_artifact",
    "write_prediction_artifact",
]

PREDICTION_COLUMNS: Final[tuple[str, ...]] = (
    "patient_id",
    "cohort",
    "modality_condition",
    "run_id",
    "checkpoint_hash",
    "p_hat",
    "logit",
    "mc_dropout_samples",
    "ensemble_member_probs",
    "nonconformity_score",
    "label",
)
SCHEMA_VERSION: Final[str] = "1"
_SCHEMA: Final[pa.Schema] = pa.schema(
    [
        pa.field("patient_id", pa.string(), nullable=False),
        pa.field("cohort", pa.string(), nullable=False),
        pa.field("modality_condition", pa.string(), nullable=False),
        pa.field("run_id", pa.string(), nullable=False),
        pa.field("checkpoint_hash", pa.string(), nullable=False),
        pa.field("p_hat", pa.float32(), nullable=False),
        pa.field("logit", pa.float32(), nullable=False),
        pa.field("mc_dropout_samples", pa.list_(pa.float32()), nullable=True),
        pa.field("ensemble_member_probs", pa.list_(pa.float32()), nullable=True),
        pa.field("nonconformity_score", pa.float32(), nullable=True),
        pa.field("label", pa.int8(), nullable=False),
    ]
)


def hash_patient_id(canonical_id: str) -> str:
    """Return a shareable 16-character SHA-256 prefix for a canonical ID."""
    if not isinstance(canonical_id, str) or not canonical_id:
        raise ValueError("canonical patient ID must be a non-empty string")
    return hashlib.sha256(canonical_id.encode("utf-8")).hexdigest()[:16]


def _sidecar_path(path: Path) -> Path:
    return path.with_name(path.name + ".sha256")


def _write_sidecar(path: Path, digest: str) -> None:
    _sidecar_path(path).write_text(f"{digest}  {path.name}\n", encoding="ascii")


def _validated_rows(
    rows: Sequence[Mapping[str, Any]], *, run_id: str, checkpoint_hash: str
) -> list[dict[str, Any]]:
    required = {
        "patient_id",
        "cohort",
        "modality_condition",
        "p_hat",
        "logit",
        "label",
    }
    allowed = set(PREDICTION_COLUMNS)
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("each prediction row must be a mapping")
        missing = required - set(row)
        extra = set(row) - allowed
        if missing or extra:
            raise ValueError("prediction row schema is invalid")
        patient = row["patient_id"]
        cohort = row["cohort"]
        condition = row["modality_condition"]
        if not all(
            isinstance(value, str) and value for value in (patient, cohort, condition)
        ):
            raise ValueError("prediction identifiers must be non-empty strings")
        p_hat, logit = row["p_hat"], row["logit"]
        if isinstance(p_hat, bool) or isinstance(logit, bool):
            raise ValueError("p_hat and logit must be finite numbers")
        try:
            probability, score = float(p_hat), float(logit)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("p_hat and logit must be finite numbers") from error
        if not math.isfinite(probability) or not math.isfinite(score):
            raise ValueError("p_hat and logit must be finite numbers")
        if not 0.0 <= probability <= 1.0:
            raise ValueError("p_hat must be in [0, 1]")
        expected = (
            1.0 / (1.0 + math.exp(-score))
            if score >= 0
            else math.exp(score) / (1 + math.exp(score))
        )
        if abs(probability - expected) > 1e-6:
            raise ValueError("p_hat must equal sigmoid(logit) within 1e-6")
        label = row["label"]
        if isinstance(label, bool) or label not in (0, 1):
            raise ValueError("label must be 0 or 1")
        hashed_id = hash_patient_id(patient)
        duplicate_key = (hashed_id, cohort, condition)
        if duplicate_key in seen:
            raise ValueError("duplicate patient within cohort and modality condition")
        seen.add(duplicate_key)
        item: dict[str, Any] = {column: None for column in PREDICTION_COLUMNS}
        item.update(row)
        item.update(
            patient_id=hashed_id,
            run_id=run_id,
            checkpoint_hash=checkpoint_hash,
            p_hat=np.float32(probability),
            logit=np.float32(score),
            label=np.int8(label),
        )
        output.append(item)
    if not output:
        raise ValueError("prediction artifact must contain at least one row")
    return output


def write_prediction_artifact(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    *,
    run_id: str,
    git_sha: str,
    checkpoint_hash: str,
    record_git_sha: str | None = None,
) -> str:
    """Validate and freeze predictions to a hashed zstd Parquet artifact.

    Returns the artifact SHA-256. Existing artifacts or sidecars are never
    replaced. ``record_git_sha`` is included only when the scorer explicitly
    allows a current-tree/run-record SHA mismatch.
    """
    target = Path(path)
    sidecar = _sidecar_path(target)
    if target.exists() or sidecar.exists():
        raise FileExistsError(f"prediction artifact already exists: {target.name}")
    if not all(
        isinstance(value, str) and value for value in (run_id, git_sha, checkpoint_hash)
    ):
        raise ValueError(
            "run_id, git_sha, and checkpoint_hash must be non-empty strings"
        )
    if record_git_sha is not None and (
        not isinstance(record_git_sha, str) or not record_git_sha
    ):
        raise ValueError("record_git_sha must be a non-empty string")
    validated = _validated_rows(rows, run_id=run_id, checkpoint_hash=checkpoint_hash)
    metadata = {
        b"run_id": run_id.encode(),
        b"git_sha": git_sha.encode(),
        b"checkpoint_hash": checkpoint_hash.encode(),
        b"schema_version": SCHEMA_VERSION.encode(),
    }
    if record_git_sha is not None:
        metadata[b"record_git_sha"] = record_git_sha.encode()
    table = pa.Table.from_pylist(validated, schema=_SCHEMA.with_metadata(metadata))
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, target, compression="zstd")
    digest = sha256_file(target)
    _write_sidecar(target, digest)
    return digest


def read_prediction_artifact(path: str | Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Verify a prediction sidecar and return its DataFrame and metadata."""
    target = Path(path)
    sidecar = _sidecar_path(target)
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0]
    except (OSError, UnicodeError, IndexError) as error:
        raise ValueError(
            "prediction artifact SHA-256 sidecar is missing or invalid"
        ) from error
    actual = sha256_file(target)
    if expected.lower() != actual:
        raise ValueError("prediction artifact does not match its SHA-256 sidecar")
    table = pq.read_table(target)
    if tuple(table.column_names) != PREDICTION_COLUMNS:
        raise ValueError("prediction artifact has an unexpected schema")
    raw_metadata = table.schema.metadata or {}
    metadata = {key.decode(): value.decode() for key, value in raw_metadata.items()}
    return table.to_pandas(), metadata
