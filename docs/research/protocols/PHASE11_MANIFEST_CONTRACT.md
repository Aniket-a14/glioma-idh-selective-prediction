# Phase 11 freeze-manifest contract (T11.2; independent-implementation pattern)

Status: written 2026-11-17. Fixtures: `tests/fixtures/phase11_manifest/` (`spec.json`, the files it names, and
`expected_manifest.json`). Implementer: Codex, from this text and the fixtures alone. Consumer: the firewall,
`src/glioma_selective/evaluation/firewall.py` (`MANIFEST_FIELDS`, `_check_manifest`), already merged.

The generator collects what Gate E freezes into one JSON file and hashes it. It chooses no scientific value: every
number, grid, rule and metric comes from the spec file, which the Research Lead and Claude write from the frozen
pre-registration and decision log. It never signs, never reads an external cohort, and never runs with the Gate E flag set.

## Files

- `src/glioma_selective/evaluation/freeze_manifest.py`: the library below.
- `scripts/generate_freeze_manifest.py`: command line wrapper, two modes (generate, seal).
- `tests/unit/test_freeze_manifest.py`: the tests listed at the end.

## Library

```python
class ManifestError(ValueError): ...

def git_state(repo: Path) -> tuple[str, bool]:
    """(HEAD commit sha as 40 lowercase hex, tree_clean). Clean means `git status --porcelain` prints nothing
    (untracked files count as dirty; ignored files do not)."""

def build_manifest(spec_path: Path, *, roots: Mapping[str, Path], code_commit_sha: str,
                   created_utc: str, tree_clean: bool = True) -> dict[str, Any]: ...

def write_manifest(manifest: Mapping[str, Any], output: Path) -> Path:
    """Write once, atomically, with the sidecar. FileExistsError if output or its sidecar exists."""

def seal_manifest(path: Path) -> str:
    """Rewrite the sidecar of an existing manifest to match its current bytes; return the digest. Content untouched."""
```

`roots` has the keys `repo`, `data`, `artifacts`. The script fills them with the repository root,
`utils.paths.data_root()` and `utils.paths.artifact_root()`. Library code does not call `utils.paths` except for the
external-directory guard (rule G3), so the tests can pass fixture roots.

### Spec file

JSON object. A path value is `"<root>:<relative path>"` with `<root>` one of `repo`, `data`, `artifacts`.

```
checkpoints                list of {role, run_id, path}; at least one; roles unique
preprocessing              {config: <path>, run_id: <run id>}
normalization_statistics   <path>
exclusion_manifest         <path>
utsw_split_manifest        <path>
statistical_analysis_plan  {path: <path>, preregistration: <path>}
literal                    object with exactly the seven keys: calibration_parameters, conformal,
                           abstention_definition, operating_points, missing_modality_conditions,
                           primary_metrics, c4_tolerance_band
```

A missing key, an extra key, a wrong type, or an empty `literal` value (`null`, `""`, `{}`, `[]`) is `ManifestError`
naming the key.

### Output document

`build_manifest` returns a dict; `write_manifest` serializes it with
`json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=True) + "\n"` (UTF-8, no other whitespace). The sidecar is
`<sha256 hex of the manifest bytes>  <file name>\n`, written at `<output>.sha256`. The expected result for the fixture is
`tests/fixtures/phase11_manifest/expected_manifest.json`, byte for byte, with `code_commit_sha`
`0123456789abcdef0123456789abcdef01234567` and `created_utc` `2026-01-01T00:00:00Z`.

| Key | Value |
|---|---|
| `schema` | `"freeze_manifest.v1"` |
| `created_utc` | the argument, unchanged |
| `spec_sha256` | SHA-256 of the spec file's bytes |
| `code_commit_sha` | the argument; must match `^[0-9a-f]{40}$` |
| `git_tree_clean` | `true` (a dirty tree is refused, rule G2) |
| `model_checkpoints` | one entry per spec checkpoint, spec order: `{role, run_id, path, sha256}`; `path` is the spec string, `sha256` of the file bytes |
| `preprocessing` | `{config_path, config_sha256, version, parameter_hash}`; `version` and `parameter_hash` from `preprocessing_version` in `<artifacts>/experiments/<run_id>/record.json` |
| `normalization_statistics`, `exclusion_manifest`, `utsw_split_manifest` | `{path, sha256}` |
| `statistical_analysis_plan` | `{path, sha256, preregistration: {path, sha256}}`; the preregistration `sha256` is the first token of `<preregistration path>.sha256` (rule C5) |
| the seven `literal` keys | copied verbatim from the spec `literal` object |
| `authorizing_signature` | `{"name": null, "date": null, "status": "unsigned"}` always |

Paths stay in the `root:relative` form; no absolute path appears in the output.

### Cross-checks (every failure is `ManifestError`, message names the field, never a label or metric value)

- C1: every referenced file exists, is a regular file, and is read in binary form.
- C2: each checkpoint's `sha256` equals `checkpoint_hash` in its run's `record.json`.
- C3: for every run listed under `checkpoints` and for the `preprocessing.run_id` run: `split_manifest_hash` equals the
  split manifest's SHA-256, `exclusion_list_hash` equals the exclusion manifest's, and
  `preprocessing_version.normalization_stats_sha256` equals the normalization statistics file's.
- C4: a missing `record.json` or a missing record key is an error (no default).
- C5: the preregistration sidecar exists, its first whitespace-separated token equals the SHA-256 of the preregistration file.

### Guards

- G1: `FLAG_NAME` (`GLIOMA_EXTERNAL_EVAL_AUTHORIZED`) equal to `"1"` in the environment makes the script exit non-zero
  before reading anything. The library has no environment check.
- G2: `tree_clean=False` makes `build_manifest` raise. The script passes the value from `git_state`.
- G3: a resolved path under `utils.paths.external_data_dir()`, or any component of the relative part of a spec path matching
  `ucsf|pdgm|egd` (case-insensitive, as a substring), is refused. A path that resolves outside its root (for example
  with `..` or a symlink) is refused.
- G4: `write_manifest` never overwrites. The default output is `experiments_dir()/gate_e/freeze_manifest.json`.

### Signing and sealing

Signing is not done by the generator. After the Research Lead reads the manifest, they set `authorizing_signature.name`
and `.date` by hand and run `generate_freeze_manifest.py --seal <manifest>`, which calls `seal_manifest`. Until then the
firewall rejects the file, either as unsigned or, after a hand edit without sealing, as a sidecar mismatch. A stale
sidecar must therefore stay stale: `seal_manifest` is the only function that rewrites a sidecar.

### Command line

```
python scripts/generate_freeze_manifest.py --spec SPEC.json [--output PATH] [--repo PATH]
python scripts/generate_freeze_manifest.py --seal MANIFEST
```

Generate mode: G1, then `git_state(repo)`, `build_manifest` with `created_utc` the current UTC time as
`%Y-%m-%dT%H:%M:%SZ`, then `write_manifest`. It prints the output path and the digest. Seal mode prints the digest.
Exit 1 on `ManifestError` or `FileExistsError`, message on stderr.

## Tests required (`tests/unit/test_freeze_manifest.py`, CPU only, no network)

1. Golden: `build_manifest` on the fixture, serialized as above, equals `expected_manifest.json`.
2. `write_manifest` output hashes to the sidecar value; a second write to the same path raises `FileExistsError`.
3. Determinism: two builds with the same arguments give identical bytes.
4. All fifteen `firewall.MANIFEST_FIELDS` are keys of the output.
5. Firewall, with `assert_external_eval_authorized("ucsf_pdgm", environ={FLAG: "1"}, manifest_path=...)`: unsigned output
   is rejected; after editing the signature without sealing it is rejected; after `seal_manifest` it is accepted.
   (Use a temporary copy; nothing here touches external data.)
6. Refusals, one test each: checkpoint bytes changed (C2); `split_manifest_hash` changed in the record (C3); exclusion
   and normalization likewise; preregistration sidecar wrong (C5); record file missing (C4); a `literal` key missing,
   extra, and empty; spec path with `..`; path containing `egd` or `ucsf`; `tree_clean=False`; bad `code_commit_sha`.
7. `git_state` on a temporary git repository: clean, modified file, untracked file, ignored file (clean).
8. Script: the flag set to `"1"` exits non-zero and writes nothing; `--seal` leaves content bytes unchanged.

Fixtures are copied to a temporary directory before any test that edits them. Pre-existing fixture files are never edited
in place.

## What this does not decide

Which runs are in the ensemble, the operating points, the conformal grid and the C4 band are written by Claude and the
Research Lead into the real `freeze_spec.json` (T11.1 evidence, separate from this task) from `PREREGISTRATION.md` and the
decision log. The generator checks that the files exist and agree with their run records; it does not check that the
chosen values are right.
