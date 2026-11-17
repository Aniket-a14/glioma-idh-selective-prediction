"""CPU-only checks of the independent Phase 11 manifest contract and fixtures."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from scripts import generate_freeze_manifest as cli

from glioma_selective.evaluation.firewall import (
    FLAG_NAME,
    MANIFEST_FIELDS,
    ExternalEvaluationNotAuthorized,
    assert_external_eval_authorized,
)
from glioma_selective.evaluation.freeze_manifest import (
    ManifestError,
    build_manifest,
    git_state,
    seal_manifest,
    write_manifest,
)
from glioma_selective.utils import paths

_REPO = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO / "tests" / "fixtures" / "phase11_manifest"
_COMMIT = "0123456789abcdef0123456789abcdef01234567"
_CREATED = "2026-01-01T00:00:00Z"


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """All reads and edits use a private copy, including synthetic data roots."""
    copied = Path(shutil.copytree(_FIXTURE, tmp_path / "fixture"))
    monkeypatch.setattr(
        paths, "external_data_dir", lambda: copied / "data" / "external"
    )
    return copied


def _roots(fixture: Path) -> dict[str, Path]:
    return {key: fixture / key for key in ("repo", "data", "artifacts")}


def _build(fixture: Path, **kwargs: Any) -> dict[str, Any]:
    arguments = {"code_commit_sha": _COMMIT, "created_utc": _CREATED, **kwargs}
    return build_manifest(fixture / "spec.json", roots=_roots(fixture), **arguments)


def _serialize(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(document), indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode()


def _spec(fixture: Path) -> dict[str, Any]:
    return json.loads((fixture / "spec.json").read_bytes())  # type: ignore[no-any-return]


def _save_spec(fixture: Path, spec: Any) -> None:
    (fixture / "spec.json").write_text(json.dumps(spec), encoding="utf-8")


def _record_path(fixture: Path, run: str = "RUNA") -> Path:
    return fixture / "artifacts" / "experiments" / run / "record.json"


def _change_record(fixture: Path, key: str, value: Any, run: str = "RUNA") -> None:
    path = _record_path(fixture, run)
    record = json.loads(path.read_bytes())
    record[key] = value
    path.write_text(json.dumps(record), encoding="utf-8")


def _sidecar(output: Path) -> Path:
    return output.with_name(output.name + ".sha256")


def test_golden_bytes(fixture: Path) -> None:
    assert (
        _serialize(_build(fixture)) == (fixture / "expected_manifest.json").read_bytes()
    )


def test_write_hash_and_refuse_second_write(fixture: Path, tmp_path: Path) -> None:
    manifest = _build(fixture)
    output = tmp_path / "output" / "freeze_manifest.json"
    assert write_manifest(manifest, output) == output
    content = output.read_bytes()
    sidecar = _sidecar(output).read_bytes()
    assert content == _serialize(manifest)
    assert sidecar == f"{hashlib.sha256(content).hexdigest()}  {output.name}\n".encode()
    with pytest.raises(FileExistsError):
        write_manifest(manifest, output)
    assert output.read_bytes() == content
    assert _sidecar(output).read_bytes() == sidecar


@pytest.mark.parametrize(
    "link_errno", sorted({errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV})
)
def test_write_without_hard_links(
    fixture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    link_errno: int,
) -> None:
    manifest = _build(fixture)
    output = tmp_path / "output" / "freeze_manifest.json"

    def unsupported_link(source: Path, destination: Path) -> None:
        raise OSError(link_errno, "hard links unsupported")

    monkeypatch.setattr(os, "link", unsupported_link)
    assert write_manifest(manifest, output) == output
    content = _serialize(manifest)
    sidecar = f"{hashlib.sha256(content).hexdigest()}  {output.name}\n".encode()
    assert output.read_bytes() == content
    assert _sidecar(output).read_bytes() == sidecar
    with pytest.raises(FileExistsError):
        write_manifest(manifest, output)
    assert output.read_bytes() == content
    assert _sidecar(output).read_bytes() == sidecar
    assert set(output.parent.iterdir()) == {output, _sidecar(output)}


def test_fallback_sidecar_publication_failure_removes_manifest(
    fixture: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _build(fixture)
    output = tmp_path / "output" / "freeze_manifest.json"
    real_replace = os.replace

    def unsupported_link(source: Path, destination: Path) -> None:
        raise OSError(errno.EOPNOTSUPP, "hard links unsupported")

    def failing_sidecar(source: Path, destination: Path) -> None:
        if destination == _sidecar(output):
            assert output.read_bytes() == _serialize(manifest)
            raise OSError(errno.EIO, "sidecar publication failed")
        real_replace(source, destination)

    monkeypatch.setattr(os, "link", unsupported_link)
    monkeypatch.setattr(os, "replace", failing_sidecar)
    with pytest.raises(OSError, match="sidecar publication failed") as error:
        write_manifest(manifest, output)
    assert error.value.errno == errno.EIO
    assert not output.exists()
    assert not _sidecar(output).exists()
    assert not list(output.parent.iterdir())


@pytest.mark.parametrize("existing", ["manifest", "sidecar", "dangling_symlink"])
def test_write_preserves_preexisting_destination(
    fixture: Path, tmp_path: Path, existing: str
) -> None:
    output = tmp_path / "freeze_manifest.json"
    target = output if existing != "sidecar" else _sidecar(output)
    if existing == "dangling_symlink":
        target.symlink_to(tmp_path / "absent")
    else:
        target.write_bytes(b"preserve these bytes")
    with pytest.raises(FileExistsError):
        write_manifest(_build(fixture), output)
    if existing == "dangling_symlink":
        assert target.is_symlink()
    else:
        assert target.read_bytes() == b"preserve these bytes"
    assert not (output if existing == "sidecar" else _sidecar(output)).exists()


def test_write_publication_race_preserves_sidecar(
    fixture: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "freeze_manifest.json"
    real_link = os.link

    def competing_sidecar(source: Path, destination: Path) -> None:
        if destination == _sidecar(output):
            destination.write_bytes(b"concurrent sidecar")
        real_link(source, destination)

    monkeypatch.setattr(os, "link", competing_sidecar)
    with pytest.raises(FileExistsError):
        write_manifest(_build(fixture), output)
    assert not output.exists()
    assert _sidecar(output).read_bytes() == b"concurrent sidecar"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "fixture",
        "freeze_manifest.json.sha256",
    ]


def test_build_is_deterministic(fixture: Path) -> None:
    assert _serialize(_build(fixture)) == _serialize(_build(fixture))


def test_output_covers_all_fifteen_firewall_fields(fixture: Path) -> None:
    assert len(MANIFEST_FIELDS) == 15
    assert set(MANIFEST_FIELDS) <= _build(fixture).keys()


def test_firewall_unsigned_edited_and_sealed(fixture: Path, tmp_path: Path) -> None:
    manifest = _build(fixture)
    output = write_manifest(manifest, tmp_path / "freeze_manifest.json")
    authorized = {FLAG_NAME: "1"}
    with pytest.raises(ExternalEvaluationNotAuthorized, match="not signed"):
        assert_external_eval_authorized(
            "ucsf_pdgm", environ=authorized, manifest_path=output
        )
    stale_sidecar = _sidecar(output).read_bytes()
    manifest["authorizing_signature"].update(name="Research Lead", date="2026-01-02")
    output.write_bytes(_serialize(manifest))
    with pytest.raises(ExternalEvaluationNotAuthorized, match="does not match"):
        assert_external_eval_authorized(
            "ucsf_pdgm", environ=authorized, manifest_path=output
        )
    assert _sidecar(output).read_bytes() == stale_sidecar
    before = output.read_bytes()
    assert seal_manifest(output) == hashlib.sha256(before).hexdigest()
    assert output.read_bytes() == before
    assert_external_eval_authorized(
        "ucsf_pdgm", environ=authorized, manifest_path=output
    )


def test_changed_checkpoint_bytes_refused(fixture: Path) -> None:
    checkpoint = _record_path(fixture).parent / "checkpoints" / "weights.fixture"
    checkpoint.write_bytes(checkpoint.read_bytes() + b"changed")
    with pytest.raises(ManifestError, match="checkpoint_hash"):
        _build(fixture)


def test_changed_split_hash_refused(fixture: Path) -> None:
    _change_record(fixture, "split_manifest_hash", "0" * 64)
    with pytest.raises(ManifestError, match="split_manifest_hash"):
        _build(fixture)


def test_changed_exclusion_hash_refused(fixture: Path) -> None:
    _change_record(fixture, "exclusion_list_hash", "0" * 64)
    with pytest.raises(ManifestError, match="exclusion_list_hash"):
        _build(fixture)


def test_changed_normalization_hash_refused(fixture: Path) -> None:
    record = json.loads(_record_path(fixture).read_bytes())
    version = record["preprocessing_version"]
    version["normalization_stats_sha256"] = "0" * 64
    _change_record(fixture, "preprocessing_version", version)
    with pytest.raises(ManifestError, match="normalization_stats_sha256"):
        _build(fixture)


def test_wrong_preregistration_sidecar_refused(fixture: Path) -> None:
    (fixture / "repo" / "docs" / "PREREGISTRATION.md.sha256").write_bytes(b"0" * 64)
    with pytest.raises(ManifestError, match="preregistration.sha256"):
        _build(fixture)


def test_missing_record_file_refused(fixture: Path) -> None:
    _record_path(fixture).unlink()
    with pytest.raises(ManifestError, match="record"):
        _build(fixture)


@pytest.mark.parametrize(
    "key",
    [
        "checkpoint_hash",
        "split_manifest_hash",
        "exclusion_list_hash",
        "preprocessing_version",
        "preprocessing_version.version",
        "preprocessing_version.parameter_hash",
        "preprocessing_version.normalization_stats_sha256",
    ],
)
def test_missing_record_key_refused(fixture: Path, key: str) -> None:
    path = _record_path(fixture)
    record = json.loads(path.read_bytes())
    if "." in key:
        parent, child = key.split(".")
        del record[parent][child]
    else:
        del record[key]
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ManifestError, match=re.escape(key)):
        _build(fixture)


def test_preprocessing_only_run_is_cross_checked(fixture: Path) -> None:
    source = _record_path(fixture)
    target = _record_path(fixture, "PREPROC")
    target.parent.mkdir()
    shutil.copyfile(source, target)
    spec = _spec(fixture)
    spec["preprocessing"]["run_id"] = "PREPROC"
    _save_spec(fixture, spec)
    assert _build(fixture)["preprocessing"]["version"] == "fixture-preproc-v1"
    _change_record(fixture, "split_manifest_hash", "0" * 64, run="PREPROC")
    with pytest.raises(ManifestError, match="preprocessing.record.split_manifest_hash"):
        _build(fixture)


def test_missing_literal_key_refused(fixture: Path) -> None:
    spec = _spec(fixture)
    del spec["literal"]["conformal"]
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="literal.conformal"):
        _build(fixture)


def test_extra_literal_key_refused(fixture: Path) -> None:
    spec = _spec(fixture)
    spec["literal"]["unexpected"] = "value"
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="literal.unexpected"):
        _build(fixture)


@pytest.mark.parametrize("empty", [None, "", {}, []])
def test_empty_literal_value_refused(fixture: Path, empty: Any) -> None:
    spec = _spec(fixture)
    spec["literal"]["conformal"] = empty
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="literal.conformal"):
        _build(fixture)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("checkpoints", [], "checkpoints"),
        ("checkpoints", {}, "checkpoints"),
        ("preprocessing", [], "preprocessing"),
        ("statistical_analysis_plan", "bad", "statistical_analysis_plan"),
        ("literal", [], "literal"),
        ("normalization_statistics", 1, "normalization_statistics"),
    ],
)
def test_wrong_spec_type_refused(
    fixture: Path, field: str, value: Any, message: str
) -> None:
    spec = _spec(fixture)
    spec[field] = value
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match=message):
        _build(fixture)


@pytest.mark.parametrize(
    "field", ["preprocessing", "statistical_analysis_plan", "spec"]
)
@pytest.mark.parametrize("change", ["missing", "extra"])
def test_exact_spec_keys_refused(fixture: Path, field: str, change: str) -> None:
    spec = _spec(fixture)
    target = spec if field == "spec" else spec[field]
    key = "unexpected" if change == "extra" else next(iter(target))
    if change == "missing":
        del target[key]
    else:
        target[key] = "value"
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match=re.escape(f"{field}.{key}")):
        _build(fixture)


def test_duplicate_checkpoint_role_refused(fixture: Path) -> None:
    spec = _spec(fixture)
    spec["checkpoints"][1]["role"] = spec["checkpoints"][0]["role"]
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="role"):
        _build(fixture)


def test_parent_traversal_refused(fixture: Path) -> None:
    spec = _spec(fixture)
    spec["normalization_statistics"] = "repo:../spec.json"
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="normalization_statistics"):
        _build(fixture)


@pytest.mark.parametrize(
    "relative", ["EGD/file", "safe/ucsf.fixture", "archive_pdgm/file"]
)
def test_external_path_component_refused(fixture: Path, relative: str) -> None:
    spec = _spec(fixture)
    spec["normalization_statistics"] = f"repo:{relative}"
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="normalization_statistics: forbidden path"):
        _build(fixture)


@pytest.mark.parametrize("external", [False, True])
def test_resolved_symlink_guard(fixture: Path, tmp_path: Path, external: bool) -> None:
    target = fixture / "data" / "external" if external else tmp_path / "outside"
    target.mkdir(parents=True)
    (fixture / "repo" / "alias").symlink_to(target, target_is_directory=True)
    spec = _spec(fixture)
    spec["normalization_statistics"] = "repo:alias/never_read"
    _save_spec(fixture, spec)
    with pytest.raises(
        ManifestError, match="normalization_statistics: forbidden resolved"
    ):
        _build(fixture)


@pytest.mark.parametrize(
    "reference", ["unknown:file", "file", "repo:", "repo:/absolute"]
)
def test_invalid_path_reference_refused(fixture: Path, reference: str) -> None:
    spec = _spec(fixture)
    spec["normalization_statistics"] = reference
    _save_spec(fixture, spec)
    with pytest.raises(ManifestError, match="normalization_statistics"):
        _build(fixture)


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_referenced_file_must_be_regular(fixture: Path, kind: str) -> None:
    file = fixture / "repo" / "configs" / "preprocessing" / "base.yaml"
    file.unlink()
    if kind == "directory":
        file.mkdir()
    with pytest.raises(ManifestError, match="preprocessing.config"):
        _build(fixture)


def test_dirty_tree_refused(fixture: Path) -> None:
    with pytest.raises(ManifestError, match="git_tree_clean"):
        _build(fixture, tree_clean=False)


@pytest.mark.parametrize("sha", ["", "abc", "A" * 40, "g" * 40, "0" * 41, None])
def test_bad_code_commit_sha_refused(fixture: Path, sha: Any) -> None:
    with pytest.raises(ManifestError, match="code_commit_sha"):
        _build(fixture, code_commit_sha=sha)


def _temporary_repo(repo: Path) -> str:
    """Prepare a one-file Git fixture without running any Git write commands.

    Loose objects and a v2 index are written only below tmp_path. git_state then
    exercises the real read-only Git commands, including ignore handling.
    """
    metadata = repo / ".git"
    (metadata / "objects").mkdir(parents=True)
    (metadata / "refs" / "heads").mkdir(parents=True)
    (metadata / "info").mkdir()
    (metadata / "info" / "exclude").write_text("ignored.txt\n", encoding="ascii")
    (metadata / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (metadata / "config").write_text(
        "[core]\nrepositoryformatversion = 0\nbare = false\n", encoding="ascii"
    )

    def object_id(kind: str, content: bytes) -> str:
        raw = f"{kind} {len(content)}\0".encode() + content
        digest = hashlib.sha1(raw).hexdigest()
        path = metadata / "objects" / digest[:2] / digest[2:]
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(zlib.compress(raw))
        return digest

    content = b"tracked fixture\n"
    (repo / "tracked.txt").write_bytes(content)
    blob = bytes.fromhex(object_id("blob", content))
    tree = object_id("tree", b"100644 tracked.txt\0" + blob)
    commit = object_id(
        "commit",
        (
            f"tree {tree}\nauthor Test <test@example.invalid> 0 +0000\n"
            "committer Test <test@example.invalid> 0 +0000\n\nfixture\n"
        ).encode(),
    )
    (metadata / "refs" / "heads" / "main").write_text(commit + "\n", encoding="ascii")
    entry = (
        struct.pack(
            ">10I20sH", 0, 0, 0, 0, 0, 0, 0o100644, 0, 0, len(content), blob, 11
        )
        + b"tracked.txt\0"
    )
    entry += b"\0" * (-len(entry) % 8)
    index = struct.pack(">4sII", b"DIRC", 2, 1) + entry
    (metadata / "index").write_bytes(index + hashlib.sha1(index).digest())
    return commit


def test_git_state_clean_modified_untracked_and_ignored(tmp_path: Path) -> None:
    commit = _temporary_repo(tmp_path)
    assert git_state(tmp_path) == (commit, True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_bytes(b"modified\n")
    assert git_state(tmp_path) == (commit, False)
    tracked.write_bytes(b"tracked fixture\n")
    untracked = tmp_path / "untracked.txt"
    untracked.write_bytes(b"untracked\n")
    assert git_state(tmp_path) == (commit, False)
    untracked.unlink()
    (tmp_path / "ignored.txt").write_bytes(b"ignored\n")
    assert git_state(tmp_path) == (commit, True)


def test_git_state_bad_repository_refused(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="git_state"):
        git_state(tmp_path)


@pytest.mark.parametrize("mode", ["--spec", "--seal"])
def test_script_flag_refuses_before_any_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    monkeypatch.setenv(FLAG_NAME, "1")

    def forbidden_read(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("the CLI must check the flag before reading or resolving inputs")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    monkeypatch.setattr(Path, "resolve", forbidden_read)
    assert cli.main([mode, str(tmp_path / "missing")]) == 1
    assert not list(tmp_path.iterdir())


def test_script_flag_subprocess_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(FLAG_NAME, "1")
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO / "scripts" / "generate_freeze_manifest.py"),
            "--spec",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "output.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert FLAG_NAME in result.stderr
    assert result.stdout == ""
    assert not list(tmp_path.iterdir())


def test_script_seal_preserves_content(
    fixture: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(FLAG_NAME, "0")
    output = tmp_path / "freeze_manifest.json"
    original = b"hand edited bytes\n"
    output.write_bytes(original)
    _sidecar(output).write_bytes(b"stale\n")
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO / "scripts" / "generate_freeze_manifest.py"),
            "--seal",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    digest = hashlib.sha256(original).hexdigest()
    assert result.returncode == 0, result.stderr
    assert result.stdout == digest + "\n"
    assert output.read_bytes() == original
    assert _sidecar(output).read_bytes() == f"{digest}  {output.name}\n".encode()


@pytest.mark.parametrize("default_output", [False, True])
def test_script_generate_uses_repo_roots_and_utc(
    fixture: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    default_output: bool,
) -> None:
    monkeypatch.setenv(FLAG_NAME, "0")
    monkeypatch.setattr(paths, "data_root", lambda: fixture / "data")
    monkeypatch.setattr(paths, "artifact_root", lambda: fixture / "artifacts")
    monkeypatch.setattr(
        paths, "experiments_dir", lambda: fixture / "artifacts" / "experiments"
    )
    _temporary_repo(fixture / "repo")
    # The synthetic spec inputs predate this one-file Git fixture; ignore them.
    (fixture / "repo" / ".git" / "info" / "exclude").write_text(
        "configs/\ndocs/\n", encoding="ascii"
    )
    argv = ["--spec", str(fixture / "spec.json"), "--repo", str(fixture / "repo")]
    output = fixture / "artifacts" / "experiments" / "gate_e" / "freeze_manifest.json"
    if not default_output:
        output = fixture / "output.json"
        argv.extend(["--output", str(output)])
    assert cli.main(argv) == 0
    manifest = json.loads(output.read_bytes())
    assert manifest["code_commit_sha"] == git_state(fixture / "repo")[0]
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", manifest["created_utc"]
    )
    assert manifest["authorizing_signature"] == {
        "name": None,
        "date": None,
        "status": "unsigned",
    }
    assert capsys.readouterr().out.splitlines() == [
        str(output),
        hashlib.sha256(output.read_bytes()).hexdigest(),
    ]


def test_script_errors_report_exit_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(FLAG_NAME, "0")
    assert cli.main(["--seal", str(tmp_path / "missing")]) == 1
    assert "manifest" in capsys.readouterr().err
