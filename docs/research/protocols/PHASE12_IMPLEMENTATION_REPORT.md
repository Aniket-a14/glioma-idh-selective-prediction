# Phase 12 external harness implementation report

Status: **DONE_WITH_CONCERNS**. Implementation is ready for Research Lead review;
full-tree hooks and Git writes have environment limitations described below.
This is T12.3 harness preparation under `PHASE12_EXTERNAL_RUN_CONTRACT.md`,
not completion of Phase 12 or authorization to evaluate real external patients.

Branch: `agent/codex/p12-external-inference`. Starting `main` commit:
`3a6356dbc1c486ce765bc0e451bb66ccaaa73815`.

## Files

| File | Change |
|---|---|
| `scripts/run_external_evaluation.py` | Firewall-first driver, frozen-input verification, existing condition scorer, immutable output directory, provenance report and post-run SHA assertion. |
| `src/glioma_selective/data/adapters/ucsf_pdgm.py` | Guarded IDH label reader using the published `LABEL_DEFINITIONS.md` section 4 mapping. Unknown categories and duplicate canonical IDs fail. |
| `src/glioma_selective/data/dataset.py` | Optional cohort selection for identifiers, label reader and preprocessing-index selection; UTSW remains the default. |
| `src/glioma_selective/tracking/predictions.py` | Optional freeze-manifest hash metadata; exclusive artifact and sidecar creation on the external path. Existing internal serialization remains unchanged. |
| `tests/unit/test_external_evaluation.py` | Synthetic operational assertions, published label mapping, parser refusals, leak audit and standalone CLI check. |
| `tests/regression/test_external_internal_digest.py` | Byte comparison of both existing internal freezing drivers against the pre-change baseline. |
| `tests/fixtures/phase12_internal_digests.json` | Nine digests generated before production source changes. |
| `docs/research/protocols/PHASE12_INTERNAL_BASELINE.md` | Baseline provenance and verification command. |
| `docs/research/protocols/PHASE12_IMPLEMENTATION_REPORT.md` | This handoff. |

## Contract verification

1. Unset/zero authorization rejects before any file opens. Direct adapter calls
   also pass through the existing firewall. Unsigned and unsealed synthetic
   manifests are rejected by that firewall without duplicating its checks.
2. Each checkpoint, normalization file, preprocessing config, conditions config
   and exclusion manifest is hashed before inference or output creation. The
   existing `build_real_retained_rosters()` receives the verified exclusions;
   its directory-only adapters read no label columns. Count and digest are
   checked by the existing verifier against the committed post-QC cohort entry.
   Separate mismatch tests cover each file, count, digest, commit SHA, dirty
   working tree and a false `git_tree_clean` manifest field.
3. The full synthetic run uses the real dataset constructor and label parser,
   model-weight loader, condition scorer, 30-pass MC-dropout and Parquet writer.
   Only the image-loading method supplies small synthetic arrays instead of
   cached MRI volumes. It writes 36 artifacts: six conditions for the five
   ensemble checkpoints and the separately frozen comparator checkpoint.
   Temperature and conformal quantiles are copied unchanged to the report;
   raw outputs remain the substrate for subsequent analysis. Both fitting
   functions are patched to raise throughout the successful test.
4. Every Parquet metadata block includes the evaluation run ID, Git SHA,
   checkpoint hash and signed-manifest SHA-256. Artifacts and the report have
   hash sidecars. An existing run directory is rejected without modification.
5. Captured stdout equals six expected cohort/condition count lines exactly;
   stderr is empty. No metric or per-patient value is printed.
6. The post-run SHA must equal the signed commit, and the report records both
   that SHA and `git_sha_unchanged=true`. A changed SHA raises instead of
   producing a success report.
7. Both internal drivers still match all nine stored output digests exactly.
8. `scripts/audit_external_leak.py` reports **0 blocking findings**, with 11
   existing review findings. No allowlist change was needed: label loading
   lives in the already-allowed cohort adapter.

No scientific function was added or changed. The existing condition scorer and
normalization/image processing code are reused. No real UCSF-PDGM or EGD data
was accessed, no package was installed, and the real authorization flag was
not changed. Tests patch the flag only inside their own temporary environments.
The protected files named in the request were not edited.

## Gates and limits

Final local verification (using the requested existing interpreter and
`PYTHONPATH=src`):

| Check | Measured result |
|---|---|
| `pytest tests/unit tests/regression -q` | **1,134 passed, 9 skipped**, one upstream Torch deprecation warning; 73.35 seconds. |
| `mypy src/glioma_selective scripts/run_external_evaluation.py` | Passed, 91 source files. The repository-default `mypy` also passed (90 files). |
| `ruff check .` | Passed. |
| `ruff format --check .` | Passed, 332 files already formatted. |
| `scripts/check_invariants.py` | Passed. |
| Changed-file pre-commit, all nine deliverable files | All applicable hooks passed. |
| Full-tree pre-commit | Environment-blocked, detailed below; Gate A is not claimed fully passed. |
| External-leak audit | 0 blocking findings; 11 review findings. |

The final suite explicitly unset `GLIOMA_STORAGE_ROOT`, `GLIOMA_DATA_ROOT` and
`GLIOMA_ARTIFACT_ROOT` in the test process to prevent real-data access. Of the
nine skips, five are SSD cohort/leakage checks, one is the absent frozen split,
one is the deferred EGD check, one is a real-storage dataset check and one is
sandbox-blocked PyTorch worker shared memory. These were not verified against
the SSD. The standalone `--help` invocation succeeds with `PYTHONPATH=src`;
its subprocess regression covers the repository-root import path required by
`tracking/run_record.py`.

The standalone script-only mypy invocation initially could not resolve the
local package. Including `src/glioma_selective` explicitly, as in the passing
command above, type-checks both the package and driver without changing the
environment or suppressing errors.

Gate B was not claimed: no integration or merge was attempted. Gates C/E were
not exercised on real inputs. Real SSD leakage checks, full-volume external
inference, GPU execution and independent Research Lead review remain outside
this synthetic implementation validation.

The full-tree `pre-commit run --all-files` attempt failed only in
`end-of-file-fixer`: it opens files for writing, and the sandbox denies that
operation on mounted `.agents/skills/` files. The other hook groups passed.
All changed-file hooks passed. The protected mounts and hook configuration
were left unchanged; this is not a waiver of the full-tree gate.

A later `git add` and `git commit` attempt both failed creating
`/Users/aniketsaha/4th_Year/Glioma/.git/worktrees/codex-p12-external-inference/index.lock`
with `Operation not permitted`. No commit or merge was created. Two baseline
files had been staged by an earlier successful add; the regression file's
formatted working copy is newer than that staged copy. The Research Lead must
stage the final working files before committing.

Suggested atomic handoff: first commit the baseline regression, digest fixture
and baseline note; then commit the driver, adapter/dataset seam, writer metadata,
operational tests and this report. Run the normal hooks on both commits.

Next action: Research Lead review, stage the final files, and create the two
commits in an environment with writable Git metadata and skill mounts.
