from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from glioma_selective.tracking.predictions import (
    PREDICTION_COLUMNS,
    hash_patient_id,
    read_prediction_artifact,
    write_prediction_artifact,
)


def _rows() -> list[dict[str, object]]:
    return [
        {
            "patient_id": "UTSW-BT0001",
            "cohort": "utsw_calibration",
            "modality_condition": "full",
            "p_hat": 0.5,
            "logit": 0.0,
            "label": 1,
        },
        {
            "patient_id": "UTSW-BT0002",
            "cohort": "utsw_internal_test",
            "modality_condition": "full",
            "p_hat": 1.0 / (1.0 + math.exp(-1.0)),
            "logit": 1.0,
            "label": 0,
        },
    ]


def _write(path: Path, rows: list[dict[str, object]] | None = None) -> str:
    return write_prediction_artifact(
        _rows() if rows is None else rows,
        path,
        run_id="01K6JQY7YGXSP6ZBZD3YF8QXPT",
        git_sha="a" * 40,
        checkpoint_hash="b" * 64,
    )


def test_prediction_schema_order_types_roundtrip_and_id_hash(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    digest = _write(path)
    table = pq.read_table(path)
    assert tuple(table.column_names) == PREDICTION_COLUMNS
    assert table.schema.remove_metadata() == pa.schema(
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
    frame, metadata = read_prediction_artifact(path)
    assert isinstance(frame, pd.DataFrame)
    assert frame.columns.tolist() == list(PREDICTION_COLUMNS)
    assert frame["p_hat"].dtype == np.dtype("float32")
    assert frame["logit"].dtype == np.dtype("float32")
    assert frame["label"].dtype == np.dtype("int8")
    assert frame["patient_id"].tolist() == [
        hash_patient_id("UTSW-BT0001"),
        hash_patient_id("UTSW-BT0002"),
    ]
    assert "UTSW-BT0001" not in frame["patient_id"].tolist()
    assert metadata == {
        "run_id": "01K6JQY7YGXSP6ZBZD3YF8QXPT",
        "git_sha": "a" * 40,
        "checkpoint_hash": "b" * 64,
        "schema_version": "1",
    }
    assert (tmp_path / "predictions.parquet.sha256").read_text().startswith(digest)


def test_prediction_reader_detects_tampered_file_and_missing_sidecar(
    tmp_path: Path,
) -> None:
    path = tmp_path / "predictions.parquet"
    _write(path)
    content = bytearray(path.read_bytes())
    content[len(content) // 2] ^= 1
    path.write_bytes(content)
    with pytest.raises(ValueError, match="sidecar"):
        read_prediction_artifact(path)
    path.unlink()
    Path(str(path) + ".sha256").unlink()
    _write(path)
    Path(str(path) + ".sha256").unlink()
    with pytest.raises(ValueError, match="sidecar"):
        read_prediction_artifact(path)


def test_prediction_artifact_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    _write(path)
    with pytest.raises(FileExistsError):
        _write(path)


def test_prediction_writer_rejects_probability_logit_mismatch(tmp_path: Path) -> None:
    rows = _rows()
    rows[0]["p_hat"] = 0.8
    with pytest.raises(ValueError, match="sigmoid"):
        _write(tmp_path / "predictions.parquet", rows)


def test_prediction_writer_rejects_duplicate_and_nonfinite_values(
    tmp_path: Path,
) -> None:
    rows = _rows()
    duplicate = {**rows[0], "patient_id": "UTSW-BT0001"}
    with pytest.raises(ValueError, match="duplicate"):
        _write(tmp_path / "duplicate.parquet", [rows[0], duplicate])
    rows = _rows()
    rows[0]["p_hat"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        _write(tmp_path / "nan.parquet", rows)
    rows = _rows()
    rows[0]["logit"] = float("inf")
    with pytest.raises(ValueError, match="finite"):
        _write(tmp_path / "inf.parquet", rows)


def test_sha_mismatch_metadata_can_retain_record_sha(tmp_path: Path) -> None:
    path = tmp_path / "predictions.parquet"
    write_prediction_artifact(
        _rows(),
        path,
        run_id="01K6JQY7YGXSP6ZBZD3YF8QXPT",
        git_sha="c" * 40,
        checkpoint_hash="b" * 64,
        record_git_sha="a" * 40,
    )
    _frame, metadata = read_prediction_artifact(path)
    assert metadata["git_sha"] == "c" * 40
    assert metadata["record_git_sha"] == "a" * 40
