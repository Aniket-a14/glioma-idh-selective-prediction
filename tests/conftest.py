"""Shared pytest configuration.

Makes ``src/`` importable as ``glioma_selective`` and the repository root
importable for script tests without requiring an editable install, so tests run
before Phase 00's packaging tasks (T00.2) land. Once ``pyproject.toml``
declares the src layout and the package is installed editable, this remains a
harmless no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
