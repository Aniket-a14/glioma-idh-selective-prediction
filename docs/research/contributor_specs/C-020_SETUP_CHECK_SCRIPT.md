# C-020 — `scripts/check_setup.py`: one command that says whether a machine is ready to contribute

Assigned to priyaagrawal2. Branch `contrib/priyaagrawal2/setup-check-script`. Read-only for you; the Research Lead
edits this file.

## Why this exists

Onboarding five machines cost real time: PR #2 reported that pre-commit and pytest could not run in the Windows shell
because the WSL environment was unavailable, and PRs #3, #4 and #5 each reported end-of-file-fixer changes to
`AGENTS.md` and `GEMINI.md` that were left out of the PR (the cause was not established). `docs/research/prompts/SETUP_PROMPT.md`
lists the setup steps but nothing checks the result. This script checks it, read-only, and tells the person what to
fix. It also collects the line-ending facts needed to find the cause of that hook noise.

## Files (nothing else may be touched)

- `scripts/check_setup.py` (new)
- `tests/unit/test_check_setup.py` (new)

## Behaviour

`python scripts/check_setup.py [--repo PATH] [--json]`. `--repo` defaults to the repository containing the script.
Prints one line per check, `STATUS  name  message  (fix: ...)` with STATUS one of `PASS`, `WARN`, `FAIL`, `INFO`, then
a summary line. Exit code 0 when there is no `FAIL`, 1 otherwise, 2 for bad arguments. `--json` prints the same
results as one JSON object instead.

**The script is strictly read-only.** It changes no file, installs nothing, does not run `pre-commit` or `pytest`, never
reads or lists anything under `data/` or `artifacts/`, never prints the contents of `.env`, and never prints an
environment variable's value except for the one named below. Run external programs only with a fixed argument list,
never `shell=True`, always with a timeout of 20 seconds.

Checks (name, status rule):

1. `python-version`: FAIL if the running Python is older than the `requires-python` floor in `pyproject.toml` (read it
   with `tomllib`; do not hard-code 3.12).
2. `virtualenv`: WARN if `sys.prefix == sys.base_prefix`.
3. `package-import`: FAIL if `import glioma_selective` fails, or if the module file is not inside `<repo>/src`
   (an editable install of a different checkout).
4. `git`: FAIL if `git` is not on PATH. `git-identity`: WARN if `user.name` or `user.email` is unset.
5. `git-hooks`: WARN if the pre-commit hook is not installed in the hooks directory that
   `git rev-parse --git-path hooks` reports (this also works inside a worktree, where `.git` is a file).
6. `pre-commit-tool`: WARN if the `pre-commit` executable is not on PATH.
7. `gh-auth`: WARN if `gh` is missing or `gh auth status` exits non-zero (needed to open pull requests).
8. `env-file`: FAIL if `.env` is tracked by git (`git ls-files --error-unmatch .env` succeeds); INFO if it does not
   exist; PASS otherwise.
9. `external-eval-flag`: FAIL if `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` is set to anything other than `0` in the process
   environment or in a `KEY=VALUE` line of `.env` (parse only that key; ignore comments; strip quotes). Print only
   `0`, `unset`, or `NOT ZERO`. PASS otherwise. This flag must stay 0 until the Research Lead flips it once at Gate E.
10. `wsl`: INFO reporting `WSL2`, `WSL (version not determined)` or `not WSL`. Read `/proc/version` when the file
    exists: no `microsoft` (case-insensitive) means `not WSL`; `microsoft` and `wsl2` (case-insensitive) means `WSL2`;
    `microsoft` alone means `WSL (version not determined)`. The Research Lead works on a Mac and could not check
    the real text of that file, so the pull request must quote your machine's `/proc/version` line (home directory
    and username removed) next to the script's answer. WARN when running under WSL and the repository path starts with
    `/mnt/` (slow, and file permissions differ; the repo belongs in the Linux file system).
11. `line-endings`: INFO with the values of `core.autocrlf` and `core.eol` (or `unset`), and WARN if any of the first 50
    tracked files (from `git ls-files`, sorted) with suffix `.md`, `.py`, `.toml` or `.yaml` contains a `\r\n` byte pair.
    Reason: to gather the facts behind the end-of-file-fixer noise, not to claim a cause.
12. `storage-root`: INFO whether `GLIOMA_STORAGE_ROOT` is set and whether that directory exists (print `set, exists`,
    `set, missing`, or `unset`; never the path itself). Never FAIL: most contributors have no data drive.
13. `branch`: INFO current branch name; WARN if it is `main` with uncommitted changes.

Structure it so the checks are testable without touching the real machine: a `Check` result dataclass, one small
function per check taking the inputs it needs (repo path, an `env` mapping, a `run(args) -> (returncode, stdout)`
callable), and a `main()` that wires the real ones. mypy is not run on `scripts/`, but ruff and pre-commit are; keep
every function under cyclomatic complexity 10.

## Tests required

For each of the 13 checks, at least one test for each status it can return, using a temporary git repository built with
`git init` in `tmp_path` and fake `env`/`run` arguments. In particular: `.env` tracked, `.env` untracked, the flag at `0`,
at `1`, unset and set in `.env` only; `main` with a dirty tree; a worktree (`git worktree add` inside the temp repo) for
the hooks check; CRLF file present; `--json` output parses and contains every check name; exit codes 0, 1 and 2.
The tests must not depend on `gh` or `pre-commit` being installed, and must pass on macOS and on Linux/WSL2.

## Real run required in the pull request

Run `python scripts/check_setup.py` on **your own machine, inside WSL2** if that is where you work, and again if you
have a second setup, and paste each output into the PR description. Replace your home directory with `~` and your
username with `<user>` first. Do not fix anything the script reports: quote it and say what you think each WARN or
FAIL means. That output is data the Research Lead needs.

## Milestones

The dates are deadlines, not start dates; starting this weekend is fine. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-09-23, open a **draft** pull request) checks 1 to 7 with tests.
2. (by Thu 2026-09-24) checks 8 to 13 with tests.
3. (by Fri 2026-09-25, mark ready) `--json`, exit codes, the real-machine output in the PR text.

## Not allowed

Editing `SETUP_PROMPT.md`, `.pre-commit-config.yaml`, `pyproject.toml`, `.env`, `.github/`, or any file not listed.
No new dependency (standard library only). If something here is ambiguous, list it under "Open questions" in the
pull request and implement it exactly as written.
