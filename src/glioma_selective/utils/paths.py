"""The canonical filesystem-root abstraction.

This is the **only** module in ``glioma_selective`` permitted to read
``GLIOMA_STORAGE_ROOT``, ``GLIOMA_DATA_ROOT``, or ``GLIOMA_ARTIFACT_ROOT`` from
the environment, and the only place a filesystem root may be resolved. Every
other module receives paths by calling functions here — never by constructing
a path from a hard-coded string.

Frozen after Phase 01 (see docs/research/AGENT_WORKTREE_PROTOCOL.md section 6):
changing this module's public interface after that point requires Research
Lead approval, since every downstream module depends on it.

Layout resolved by this module (docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md
section 11)::

    $GLIOMA_STORAGE_ROOT/
    |-- data/
    |   |-- raw/        external/    interim/     processed/
    |   |-- manifests/  private/
    `-- artifacts/
        |-- cache/       checkpoints/  experiments/  predictions/
        |-- figures/     logs/         mlflow/
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "PathResolutionError",
    "storage_root",
    "data_root",
    "artifact_root",
    "raw_data_dir",
    "external_data_dir",
    "interim_data_dir",
    "processed_data_dir",
    "manifests_dir",
    "private_data_dir",
    "cache_dir",
    "checkpoints_dir",
    "experiments_dir",
    "predictions_dir",
    "figures_dir",
    "logs_dir",
    "mlflow_dir",
]


class PathResolutionError(RuntimeError):
    """A required filesystem-root environment variable is missing or empty."""


def _env_path(var_name: str) -> Path | None:
    """Return ``$var_name`` as a ``Path``, or ``None`` if unset/empty."""
    value = os.environ.get(var_name)
    if not value:
        return None
    return Path(value).expanduser()


def storage_root() -> Path:
    """Root of the external storage volume (``GLIOMA_STORAGE_ROOT``).

    Raises:
        PathResolutionError: if the variable is unset or empty. There is no
            default — a silent fallback (e.g. to the current directory) would
            let a script write into the repository, which is exactly what
            this module exists to prevent.
    """
    root = _env_path("GLIOMA_STORAGE_ROOT")
    if root is None:
        raise PathResolutionError(
            "GLIOMA_STORAGE_ROOT is not set. Copy .env.example to .env and set "
            "GLIOMA_STORAGE_ROOT to the external storage volume "
            "(see docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md, section 11)."
        )
    return root


def data_root() -> Path:
    """Root of the data tree: ``$GLIOMA_DATA_ROOT`` or ``storage_root()/data``."""
    override = _env_path("GLIOMA_DATA_ROOT")
    if override is not None:
        return override
    return storage_root() / "data"


def artifact_root() -> Path:
    """Root of the artifact tree: ``$GLIOMA_ARTIFACT_ROOT`` or ``storage_root()/artifacts``."""
    override = _env_path("GLIOMA_ARTIFACT_ROOT")
    if override is not None:
        return override
    return storage_root() / "artifacts"


# --- data/ subdirectories --------------------------------------------------


def raw_data_dir() -> Path:
    """As-downloaded data, read-only after checksum. Never modified."""
    return data_root() / "raw"


def external_data_dir() -> Path:
    """UCSF-PDGM and EGD data, behind the external-validation firewall."""
    return data_root() / "external"


def interim_data_dir() -> Path:
    """Partial preprocessing output. Resumable, safe to delete and redo."""
    return data_root() / "interim"


def processed_data_dir() -> Path:
    """Deterministic, content-addressed preprocessing output."""
    return data_root() / "processed"


def manifests_dir() -> Path:
    """Cohort/exclusion/split manifests and their hashes (also tracked in Git)."""
    return data_root() / "manifests"


def private_data_dir() -> Path:
    """DUA-restricted metadata. Never committed, never synced."""
    return data_root() / "private"


# --- artifacts/ subdirectories ----------------------------------------------


def cache_dir() -> Path:
    """Regenerable cache. Safe to delete."""
    return artifact_root() / "cache"


def checkpoints_dir() -> Path:
    """Model weights."""
    return artifact_root() / "checkpoints"


def experiments_dir() -> Path:
    """Run records (paired with ``experiments/REGISTRY.md`` in the repo)."""
    return artifact_root() / "experiments"


def predictions_dir() -> Path:
    """Frozen per-patient prediction outputs — the analysis substrate."""
    return artifact_root() / "predictions"


def figures_dir() -> Path:
    """Generated figures."""
    return artifact_root() / "figures"


def logs_dir() -> Path:
    """Run logs."""
    return artifact_root() / "logs"


def mlflow_dir() -> Path:
    """Local MLflow tracking store, when file-backed."""
    return artifact_root() / "mlflow"
