"""Collect and hash Gate E inputs without choosing values or signing them.

Implements ``docs/research/protocols/PHASE11_MANIFEST_CONTRACT.md``. Run
records and referenced files are checked before an unsigned manifest is returned.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from glioma_selective.utils import paths

_LITERAL_KEYS = {
    "calibration_parameters",
    "conformal",
    "abstention_definition",
    "operating_points",
    "missing_modality_conditions",
    "primary_metrics",
    "c4_tolerance_band",
}
_SPEC_KEYS = {
    "checkpoints",
    "preprocessing",
    "normalization_statistics",
    "exclusion_manifest",
    "utsw_split_manifest",
    "statistical_analysis_plan",
    "literal",
}
_COMMIT = re.compile(r"[0-9a-f]{40}")
_EXTERNAL = re.compile(r"ucsf|pdgm|egd", re.IGNORECASE)


class ManifestError(ValueError):
    """An input fails the freeze-manifest contract; messages name fields only."""


def git_state(repo: Path) -> tuple[str, bool]:
    """Return (40-character lowercase HEAD SHA, clean including untracked files)."""
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(repo), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ManifestError("git_state: cannot read HEAD or tree status") from error
    if _COMMIT.fullmatch(commit) is None:
        raise ManifestError("code_commit_sha: invalid HEAD")
    return commit, status == ""


def _object(value: Any, keys: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field}: expected an object")
    for key in sorted(keys - value.keys()):
        raise ManifestError(f"{field}.{key}: missing key")
    for key in sorted(value.keys() - keys):
        raise ManifestError(f"{field}.{key}: extra key")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{field}: expected a non-empty string")
    return value


def _read_bytes(path: Path, field: str) -> bytes:
    try:
        if not path.is_file():
            raise ManifestError(f"{field}: missing or non-regular file")
        return path.read_bytes()
    except OSError as error:
        raise ManifestError(f"{field}: cannot read file") from error


def _json_object(content: bytes, field: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except (ValueError, UnicodeError) as error:
        raise ManifestError(f"{field}: invalid JSON") from error
    if not isinstance(value, dict):
        raise ManifestError(f"{field}: expected an object")
    return value


def _resolve(value: Any, roots: Mapping[str, Path], external: Path, field: str) -> Path:
    reference = _string(value, field)
    root_name, separator, relative = reference.partition(":")
    if not separator or root_name not in roots or not relative:
        raise ManifestError(f"{field}: expected root:relative path")
    suffix = Path(relative)
    if suffix.is_absolute() or any(_EXTERNAL.search(part) for part in suffix.parts):
        raise ManifestError(f"{field}: forbidden path")
    try:
        root = roots[root_name].resolve()
        resolved = (root / suffix).resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise ManifestError(f"{field}: cannot resolve path") from error
    if not resolved.is_relative_to(root) or resolved.is_relative_to(external):
        raise ManifestError(f"{field}: forbidden resolved path")
    return resolved


def _file_entry(
    value: Any, roots: Mapping[str, Path], external: Path, field: str
) -> dict[str, str]:
    path = _resolve(value, roots, external, field)
    return {
        "path": value,
        "sha256": hashlib.sha256(_read_bytes(path, field)).hexdigest(),
    }


def _record(
    run_id: str,
    roots: Mapping[str, Path],
    external: Path,
    hashes: Mapping[str, str],
    field: str,
) -> dict[str, Any]:
    record_field = f"{field}.record"
    record_path = _resolve(
        f"artifacts:experiments/{run_id}/record.json", roots, external, record_field
    )
    record = _json_object(_read_bytes(record_path, record_field), record_field)
    for key in ("split_manifest_hash", "exclusion_list_hash"):
        if record.get(key) != hashes[key]:
            raise ManifestError(f"{record_field}.{key}: missing or mismatched hash")
    version = record.get("preprocessing_version")
    if not isinstance(version, dict):
        raise ManifestError(
            f"{record_field}.preprocessing_version: missing or wrong type"
        )
    if (
        version.get("normalization_stats_sha256")
        != hashes["normalization_stats_sha256"]
    ):
        raise ManifestError(
            f"{record_field}.preprocessing_version.normalization_stats_sha256: "
            "missing or mismatched hash"
        )
    # Run records can contain other tracking fields, but none of these may default.
    for key in ("version", "parameter_hash"):
        _string(version.get(key), f"{record_field}.preprocessing_version.{key}")
    return record


def build_manifest(
    spec_path: Path,
    *,
    roots: Mapping[str, Path],
    code_commit_sha: str,
    created_utc: str,
    tree_clean: bool = True,
) -> dict[str, Any]:
    """Validate the contract and return an unsigned, root-relative manifest.

    Reads only the spec, its referenced files/sidecar, and the named run records.
    The library does not inspect the Gate E flag; the command line guards it.
    """
    if tree_clean is not True:
        raise ManifestError("git_tree_clean: dirty tree refused")
    if (
        not isinstance(code_commit_sha, str)
        or _COMMIT.fullmatch(code_commit_sha) is None
    ):
        raise ManifestError("code_commit_sha: expected 40 lowercase hex characters")
    _string(created_utc, "created_utc")
    if set(roots) != {"repo", "data", "artifacts"} or any(
        not isinstance(root, Path) for root in roots.values()
    ):
        raise ManifestError("roots: expected repo, data, artifacts paths")
    try:
        external = paths.external_data_dir().resolve()
        if spec_path.resolve().is_relative_to(external):
            raise ManifestError("spec: forbidden external path")
    except (paths.PathResolutionError, OSError, RuntimeError, ValueError) as error:
        raise ManifestError("spec: cannot resolve external-directory guard") from error
    content = _read_bytes(spec_path, "spec")
    spec = _object(_json_object(content, "spec"), _SPEC_KEYS, "spec")
    literal = _object(spec["literal"], _LITERAL_KEYS, "literal")
    for key, value in literal.items():
        if value is None or value == "" or value == {} or value == []:
            raise ManifestError(f"literal.{key}: empty value")
    preprocessing = _object(
        spec["preprocessing"], {"config", "run_id"}, "preprocessing"
    )
    preprocessing_run = _string(preprocessing["run_id"], "preprocessing.run_id")
    plan = _object(
        spec["statistical_analysis_plan"],
        {"path", "preregistration"},
        "statistical_analysis_plan",
    )
    checkpoints = spec["checkpoints"]
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ManifestError("checkpoints: expected a non-empty list")
    roles: set[str] = set()
    for index, checkpoint in enumerate(checkpoints):
        field = f"checkpoints[{index}]"
        _object(checkpoint, {"role", "run_id", "path"}, field)
        role = _string(checkpoint["role"], f"{field}.role")
        _string(checkpoint["run_id"], f"{field}.run_id")
        if role in roles:
            raise ManifestError(f"{field}.role: duplicate role")
        roles.add(role)

    entries = {
        key: _file_entry(spec[key], roots, external, key)
        for key in (
            "normalization_statistics",
            "exclusion_manifest",
            "utsw_split_manifest",
        )
    }
    hashes = {
        "split_manifest_hash": entries["utsw_split_manifest"]["sha256"],
        "exclusion_list_hash": entries["exclusion_manifest"]["sha256"],
        "normalization_stats_sha256": entries["normalization_statistics"]["sha256"],
    }
    model_checkpoints = []
    for index, checkpoint in enumerate(checkpoints):
        field = f"checkpoints[{index}]"
        entry = _file_entry(checkpoint["path"], roots, external, f"{field}.path")
        record = _record(checkpoint["run_id"], roots, external, hashes, field)
        if record.get("checkpoint_hash") != entry["sha256"]:
            raise ManifestError(
                f"{field}.record.checkpoint_hash: missing or mismatched hash"
            )
        model_checkpoints.append(
            {"role": checkpoint["role"], "run_id": checkpoint["run_id"], **entry}
        )

    config = _file_entry(
        preprocessing["config"], roots, external, "preprocessing.config"
    )
    preprocessing_record = _record(
        preprocessing_run, roots, external, hashes, "preprocessing"
    )
    version = preprocessing_record["preprocessing_version"]
    plan_entry = _file_entry(
        plan["path"], roots, external, "statistical_analysis_plan.path"
    )
    prereg_field = "statistical_analysis_plan.preregistration"
    prereg = _file_entry(plan["preregistration"], roots, external, prereg_field)
    sidecar_path = _resolve(
        plan["preregistration"] + ".sha256", roots, external, f"{prereg_field}.sha256"
    )
    tokens = _read_bytes(sidecar_path, f"{prereg_field}.sha256").split()
    if not tokens or tokens[0] != prereg["sha256"].encode("ascii"):
        raise ManifestError(f"{prereg_field}.sha256: mismatched hash")
    return {
        "schema": "freeze_manifest.v1",
        "created_utc": created_utc,
        "spec_sha256": hashlib.sha256(content).hexdigest(),
        "code_commit_sha": code_commit_sha,
        "git_tree_clean": True,
        "model_checkpoints": model_checkpoints,
        "preprocessing": {
            "config_path": config["path"],
            "config_sha256": config["sha256"],
            "version": version["version"],
            "parameter_hash": version["parameter_hash"],
        },
        **entries,
        "statistical_analysis_plan": {**plan_entry, "preregistration": prereg},
        **literal,
        "authorizing_signature": {"name": None, "date": None, "status": "unsigned"},
    }


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".sha256")


def _stage(content: bytes, destination: Path) -> Path:
    """Prepare complete bytes on the destination filesystem before publishing."""
    descriptor, name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _sidecar_bytes(digest: str, path: Path) -> bytes:
    return f"{digest}  {path.name}\n".encode()


def _publish_once(temporary: Path, destination: Path) -> None:
    """Publish staged bytes, using a lock when hard links are unsupported."""
    try:
        os.link(temporary, destination)
    except OSError as error:
        if error.errno not in {errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}:
            raise
        lock = destination.with_name(f".{destination.name}.manifest-lock")
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            if os.path.lexists(destination):
                raise FileExistsError(f"{destination.name}: already exists")
            os.replace(temporary, destination)
        finally:
            os.close(descriptor)
            lock.unlink()


def write_manifest(manifest: Mapping[str, Any], output: Path) -> Path:
    """Publish complete files atomically, without overwriting either destination.

    Hard links provide an atomic no-clobber publication on the same filesystem.
    Filesystems without hard links use exclusive-create locks and atomic replace.
    The pair cannot appear simultaneously: until the sidecar appears, the firewall
    refuses the manifest. A failed sidecar publication rolls back our manifest.
    """
    sidecar = _sidecar(output)
    for path in (output, sidecar):
        if os.path.lexists(path):
            raise FileExistsError(f"{path.name}: already exists")
    content = (
        json.dumps(dict(manifest), indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = _stage(content, output)
    try:
        temporary_sidecar = _stage(_sidecar_bytes(digest, output), sidecar)
        try:
            _publish_once(temporary, output)
            try:
                _publish_once(temporary_sidecar, sidecar)
            except BaseException:
                output.unlink()
                raise
        finally:
            temporary_sidecar.unlink(missing_ok=True)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def seal_manifest(path: Path) -> str:
    """Rewrite only the sidecar to match the manifest's current, unchanged bytes."""
    digest = hashlib.sha256(_read_bytes(path, "manifest")).hexdigest()
    sidecar = _sidecar(path)
    temporary = _stage(_sidecar_bytes(digest, path), sidecar)
    try:
        os.replace(temporary, sidecar)
    finally:
        temporary.unlink(missing_ok=True)
    return digest
