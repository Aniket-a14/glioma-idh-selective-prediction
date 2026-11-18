"""T13.7: independently regenerated figures/tables must match byte for byte."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.unit import test_paper_tables as support

frozen_run = support.frozen_run


def test_paper_artifacts_regenerate_identically(
    frozen_run: Path, tmp_path: Path
) -> None:
    repository = Path(__file__).resolve().parents[2]
    directories = [tmp_path / "first", tmp_path / "second"]
    for hash_seed, output in zip(("7", "93"), directories, strict=True):
        env = {
            **os.environ,
            "GLIOMA_STORAGE_ROOT": str(frozen_run.parents[2]),
            "GLIOMA_EXTERNAL_EVAL_AUTHORIZED": "0",
            "PYTHONPATH": str(repository / "src"),
            "PYTHONHASHSEED": hash_seed,
        }
        env.pop("GLIOMA_ARTIFACT_ROOT", None)
        env.pop("GLIOMA_DATA_ROOT", None)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "glioma_selective.cli.build_paper_artifacts",
                "--run-id",
                "R2",
                "--out-dir",
                str(output),
            ],
            env=env,
            cwd=repository,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
    first, second = directories
    assert sorted(path.name for path in first.iterdir()) == sorted(
        path.name for path in second.iterdir()
    )
    for path in sorted(first.iterdir()):
        if path.name == "REGISTRY_ROWS.md":
            # Exact regenerate commands must name their respective output dirs.
            assert path.read_text().replace(str(first), "OUTPUT") == (
                second / path.name
            ).read_text().replace(str(second), "OUTPUT")
        else:
            assert path.read_bytes() == (second / path.name).read_bytes(), path.name
