"""The Gate E firewall: raises by default, raises with the flag but no valid signed
manifest, permits when both hold, and guards nothing but external cohorts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from glioma_selective.evaluation import firewall
from glioma_selective.evaluation.firewall import (
    EXTERNAL_COHORTS,
    FLAG_NAME,
    MANIFEST_FIELDS,
    ExternalEvaluationNotAuthorized,
    assert_external_eval_authorized,
)

ON = {FLAG_NAME: "1"}


def _manifest(**overrides: Any) -> dict[str, Any]:
    document: dict[str, Any] = {field: f"value of {field}" for field in MANIFEST_FIELDS}
    document["authorizing_signature"] = {"name": "Research Lead", "date": "2026-12-01"}
    document.update(overrides)
    return document


def _write(path: Path, document: Any, *, sidecar: str | None = "match") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document).encode()
    path.write_bytes(payload)
    if sidecar == "match":
        path.with_name(path.name + ".sha256").write_text(
            f"{hashlib.sha256(payload).hexdigest()}  {path.name}\n"
        )
    elif sidecar is not None:
        path.with_name(path.name + ".sha256").write_text(sidecar)
    return path


def test_the_fifteen_manifest_fields_are_listed_once() -> None:
    assert len(MANIFEST_FIELDS) == 15 == len(set(MANIFEST_FIELDS))
    assert EXTERNAL_COHORTS == ("ucsf_pdgm", "egd")


@pytest.mark.parametrize("cohort", EXTERNAL_COHORTS)
def test_raises_by_default_when_the_flag_is_not_set(
    cohort: str, tmp_path: Path
) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", _manifest())
    with pytest.raises(ExternalEvaluationNotAuthorized, match=FLAG_NAME):
        assert_external_eval_authorized(cohort, environ={}, manifest_path=manifest)


@pytest.mark.parametrize("value", ["0", "", "true", "yes", "01", " 1", "2"])
def test_only_the_exact_value_one_counts_as_set(value: str, tmp_path: Path) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", _manifest())
    with pytest.raises(ExternalEvaluationNotAuthorized, match=FLAG_NAME):
        assert_external_eval_authorized(
            "ucsf_pdgm", environ={FLAG_NAME: value}, manifest_path=manifest
        )


def test_raises_when_the_flag_is_set_but_there_is_no_manifest(tmp_path: Path) -> None:
    with pytest.raises(ExternalEvaluationNotAuthorized, match="no freeze manifest"):
        assert_external_eval_authorized(
            "egd", environ=ON, manifest_path=tmp_path / "freeze_manifest.json"
        )


def test_raises_when_the_sidecar_is_missing_or_wrong(tmp_path: Path) -> None:
    no_sidecar = _write(
        tmp_path / "a" / "freeze_manifest.json", _manifest(), sidecar=None
    )
    with pytest.raises(ExternalEvaluationNotAuthorized, match="sidecar"):
        assert_external_eval_authorized("egd", environ=ON, manifest_path=no_sidecar)
    wrong = _write(
        tmp_path / "b" / "freeze_manifest.json", _manifest(), sidecar="0" * 64 + "  x\n"
    )
    with pytest.raises(ExternalEvaluationNotAuthorized, match="does not match"):
        assert_external_eval_authorized("egd", environ=ON, manifest_path=wrong)


def test_a_manifest_edited_after_hashing_is_refused(tmp_path: Path) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", _manifest())
    manifest.write_bytes(manifest.read_bytes() + b" ")
    with pytest.raises(ExternalEvaluationNotAuthorized, match="does not match"):
        assert_external_eval_authorized("ucsf_pdgm", environ=ON, manifest_path=manifest)


@pytest.mark.parametrize("field", MANIFEST_FIELDS)
def test_every_manifest_field_is_required(field: str, tmp_path: Path) -> None:
    document = _manifest()
    del document[field]
    manifest = _write(tmp_path / "freeze_manifest.json", document)
    with pytest.raises(ExternalEvaluationNotAuthorized, match=field):
        assert_external_eval_authorized("ucsf_pdgm", environ=ON, manifest_path=manifest)


@pytest.mark.parametrize("empty", ["", [], {}, None])
def test_an_empty_field_counts_as_missing(empty: Any, tmp_path: Path) -> None:
    manifest = _write(
        tmp_path / "freeze_manifest.json", _manifest(c4_tolerance_band=empty)
    )
    with pytest.raises(ExternalEvaluationNotAuthorized, match="c4_tolerance_band"):
        assert_external_eval_authorized("egd", environ=ON, manifest_path=manifest)


@pytest.mark.parametrize(
    "signature",
    [
        None,
        "Research Lead",
        {"name": "Research Lead"},
        {"date": "2026-12-01"},
        {"name": "", "date": "x"},
    ],
)
def test_an_unsigned_manifest_is_refused(signature: Any, tmp_path: Path) -> None:
    manifest = _write(
        tmp_path / "freeze_manifest.json", _manifest(authorizing_signature=signature)
    )
    with pytest.raises(ExternalEvaluationNotAuthorized):
        assert_external_eval_authorized("ucsf_pdgm", environ=ON, manifest_path=manifest)


def test_a_manifest_that_is_not_a_json_object_is_refused(tmp_path: Path) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", ["not", "an", "object"])
    with pytest.raises(ExternalEvaluationNotAuthorized, match="JSON object"):
        assert_external_eval_authorized("egd", environ=ON, manifest_path=manifest)
    broken = tmp_path / "broken" / "freeze_manifest.json"
    broken.parent.mkdir()
    broken.write_bytes(b"{not json")
    broken.with_name(broken.name + ".sha256").write_text(
        hashlib.sha256(b"{not json").hexdigest() + "  x\n"
    )
    with pytest.raises(ExternalEvaluationNotAuthorized, match="valid JSON"):
        assert_external_eval_authorized("egd", environ=ON, manifest_path=broken)


@pytest.mark.parametrize("cohort", EXTERNAL_COHORTS)
def test_permits_access_when_the_flag_and_a_signed_manifest_both_hold(
    cohort: str, tmp_path: Path
) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", _manifest())
    result = assert_external_eval_authorized(cohort, environ=ON, manifest_path=manifest)
    assert result is None


@pytest.mark.parametrize("cohort", ["utsw", "UCSF_PDGM", "ucsf", "tcga", "", "egd "])
def test_only_external_cohort_names_are_accepted(cohort: str, tmp_path: Path) -> None:
    manifest = _write(tmp_path / "freeze_manifest.json", _manifest())
    with pytest.raises(ValueError, match="external cohorts"):
        assert_external_eval_authorized(cohort, environ=ON, manifest_path=manifest)


def test_the_default_manifest_location_is_under_the_artifact_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(tmp_path))
    location = firewall.freeze_manifest_path()
    assert location.name == "freeze_manifest.json"
    assert location.parent.name == "gate_e"
    assert "experiments" in location.parts


def test_error_messages_carry_no_label_or_metric_values(tmp_path: Path) -> None:
    with pytest.raises(ExternalEvaluationNotAuthorized) as caught:
        assert_external_eval_authorized(
            "ucsf_pdgm", environ={}, manifest_path=tmp_path / "m.json"
        )
    assert "auroc" not in str(caught.value).lower()


def test_the_test_session_is_not_authorized() -> None:
    # CI runs with the flag at 0, so an accidental external evaluation must fail.
    assert os.environ.get(FLAG_NAME, "0") != "1"
