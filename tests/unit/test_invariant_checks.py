from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_checker():
    checker_path = Path(__file__).parents[2] / "scripts" / "check_invariants.py"
    spec = importlib.util.spec_from_file_location("check_invariants", checker_path)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load invariant checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_tree_passes(tmp_path: Path) -> None:
    (tmp_path / "src" / "glioma_selective" / "evaluation").mkdir(parents=True)
    (tmp_path / "src" / "glioma_selective" / "evaluation" / "metrics.py").write_text(
        "from collections.abc import Sequence\n", encoding="utf-8"
    )

    checker = _load_checker()

    assert checker.check_invariants(tmp_path) == []


def test_planted_violations_fail(tmp_path: Path) -> None:
    evaluation = tmp_path / "src" / "glioma_selective" / "evaluation" / "submodule"
    evaluation.mkdir(parents=True)
    forbidden_endpoint = "MG" + "MT"
    forbidden_root = "/" + "Volumes/research/data"
    (evaluation / "metrics.py").write_text(
        f"PRIMARY_ENDPOINT = '{forbidden_endpoint}'\n"
        f"DATA_ROOT = '{forbidden_root}'\n"
        "from .visualization import plot\n",
        encoding="utf-8",
    )

    checker = _load_checker()
    violations = checker.check_invariants(tmp_path)

    assert len(violations) == 3
    assert any("MGMT cannot be an endpoint" in violation for violation in violations)
    assert any("hard-coded filesystem root" in violation for violation in violations)
    assert any("cannot import visualization" in violation for violation in violations)
