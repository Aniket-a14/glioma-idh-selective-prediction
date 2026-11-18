# Phase 12 internal byte baseline

Source baseline: `3a6356dbc1c486ce765bc0e451bb66ccaaa73815` (`main` and the
starting commit of `agent/codex/p12-external-inference`).

Before changing production source, the synthetic setup in
`tests/regression/test_external_internal_digest.py` ran both `freeze_run` and
`freeze_conditions`. Its nine output files supplied the SHA-256 values in
`tests/fixtures/phase12_internal_digests.json`. No real cohort was read.
The test compares the complete Parquet and JSON bytes, including metadata,
rather than only prediction values. Fixture generation is deliberately absent
from the regression test, so it cannot silently bless new outputs.

Captured with the Research Lead's existing Python environment (Python 3.14,
CPU, one Torch thread). The stored Parquet bytes also depend on the installed
serializer; a different dependency environment may require investigation.

Verified after the cohort seam with:

```sh
PYTHONPATH=src /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/regression/test_external_internal_digest.py -q
```

Next action: retain this fixture unchanged while reviewing the external harness.
