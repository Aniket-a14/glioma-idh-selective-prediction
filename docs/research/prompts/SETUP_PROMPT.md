# SETUP — SELF-LOCATING ENVIRONMENT BOOTSTRAP PROMPT

> **Invoke with:** *"Read `docs/research/prompts/SETUP_PROMPT.md` and set up the system."*
>
> Works for any collaborator on any machine, given to any AI agent (or followed by hand).
> No phase number, no prior context needed — the prompt reads the repository to find out what
> it needs to install.

---

You are bringing **this machine** to the same working state as every other machine this
repository is developed on — a fresh laptop, the GPU server, a new collaborator's clone. You are
not doing research work and you do not touch `docs/research/PROJECT_STATE.md`'s phase fields.
Your only job is: clone → environment → hooks → verify → report.

This prompt is **phase-agnostic by construction**: every step below is gated on *whether a file
exists*, not on which phase the project claims to be in. As the project grows — a lock file
appears in Phase 01, `scripts/bootstrap_storage.py` appears in Phase 01, dataset-specific setup
appears in Phase 02+ — those steps activate themselves because the files they check for now
exist. **Do not hard-code a phase number into this file, and do not add a phase-specific step
here that duplicates what a phase file already owns** — this file only ever does generic,
repeatable machine setup.

## 0. Safety — before touching anything

- Run `git status`. If the working tree is dirty, **stop and report it** rather than discarding
  or stashing it yourself — it may be a collaborator's in-progress work you were just handed.
- If `.env` already exists, **never overwrite it.** It holds machine-specific, gitignored values
  a human set deliberately.
- Never run destructive git operations (`reset --hard`, `clean -f`, force-push) as part of setup.
- Never fetch or touch anything under `data/`, `artifacts/`, or any DUA-restricted path. Setup
  installs tooling; it does not download research data (see
  `docs/research/DATA_GOVERNANCE_PROTOCOL.md` if a later step tempts you to).

## 1. Locate the repository and its toolchain requirements

Confirm you're at the repository root (`pyproject.toml` and `docs/research/` both present — if
`pyproject.toml` does not exist yet, the repository predates Phase 00's tooling tasks; report
that and stop, since nothing below has anything to install from).

Read `pyproject.toml`'s `requires-python` for the Python version floor. Confirm `git` is
available. `gh` (GitHub CLI) is optional — useful for watching CI, not required for setup.

## 2. Get the latest `main`

```bash
git fetch origin
git status   # confirm branch and cleanliness again post-fetch
```

If the local branch is behind `origin/main` and the tree is clean, fast-forward
(`git pull --ff-only`). If it has diverged, report the situation and let the human decide — never
merge or rebase unasked.

## 3. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
```

**On Windows: use WSL2, not native PowerShell/cmd.** Run every step in this prompt inside the
WSL2 shell.

*Why WSL2 at all:* every script in this repo that isn't pure Python assumes a POSIX shell —
`pre-commit` hooks, the symlink-based `data/`/`artifacts/` storage bootstrap, and `scripts/*.sh`
as they appear. None of that runs correctly under native PowerShell/cmd (symlinks in particular
behave differently and often need elevated privileges on native Windows). Rather than maintain a
second, native-Windows code path for all of that, WSL2 is the one sanctioned Windows path — it
gives every machine, Windows included, the same POSIX environment.

*Why Ubuntu specifically:* it isn't a hard requirement — any Linux distro under WSL2 would work.
Ubuntu is just what `wsl --install` gives you by default with zero extra flags, and it's the only
one this has actually been tested on. If a teammate already has a different WSL2 distro installed
(Debian, etc.), they don't need to switch — just report which one, since if something breaks in a
distro-specific way we'll want to know that's the variable.

If WSL2 isn't installed yet: `wsl --install` from an admin PowerShell prompt, reboot, then
continue this entire prompt from inside the Ubuntu shell it opens.

`.venv/` is already gitignored. Reuse an existing `.venv/` if one is present and its Python
version satisfies step 1; otherwise recreate it.

## 4. Install the package

If a lock file exists (check for what the project's dependency-locking task introduces — e.g. a
`requirements*.lock.txt`, `uv.lock`, or `poetry.lock` — `docs/research/REPRODUCIBILITY_PROTOCOL.md`
§6 requires one from Phase 01 onward), install from it for a reproducible environment. Otherwise:

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

## 5. Register git hooks

`pre-commit run --all-files` (used during CI and manual verification) is **not** the same as
having the hook installed for your own commits. Do both:

```bash
pre-commit install
pre-commit run --all-files
```

If `.secrets.baseline` exists and `detect-secrets` complains it's stale relative to installed
plugins, report it rather than regenerating it silently — the baseline is a security artifact.

## 6. Environment file

```bash
[ -f .env ] || cp .env.example .env
```

Then **stop and tell the human** which values in `.env` are machine-specific and cannot be
filled in for them:

- `GLIOMA_STORAGE_ROOT` — the external SSD or large local volume on *this* machine. There is no
  default; `src/glioma_selective/utils/paths.py` deliberately raises rather than guessing one.
- `GLIOMA_MACHINE` — `local-mac` / `gpu-server` / `ci`, whichever this machine actually is.
- `MLFLOW_TRACKING_URI` — leave blank unless this machine runs tracked experiments.
- `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` — **leave at `0`.** Never set this to `1` as part of setup;
  it flips only once, by the Research Lead, at Gate E (`docs/research/EXTERNAL_VALIDATION_PROTOCOL.md`).

## 7. Storage bootstrap (once it exists)

If `scripts/bootstrap_storage.py` exists (Phase 01 introduces it) **and** `.env` now has a real
`GLIOMA_STORAGE_ROOT` (not a placeholder), run it:

```bash
python scripts/bootstrap_storage.py
```

It is documented to be idempotent and to refuse dangerous overwrites. If `GLIOMA_STORAGE_ROOT` is
still unset, skip this step and name it as an outstanding manual step in your report — do not
invent a path.

## 8. Verify

Run whatever subset of these exists in the repository right now — this is the generic
verification suite, equivalent to what Gate A/B run in CI:

```bash
pre-commit run --all-files
python scripts/check_invariants.py            # once T00.8 exists
pytest tests/unit -q                            # always
pytest tests -q -m "not gpu"                    # once integration tests exist
mypy                                             # once configured
radon cc src -a -nc --min B                      # once configured
radon mi src --min C                             # once configured
```

Report the actual output of anything that fails — not just pass/fail.

## 9. Report back

1. What this machine was missing and what you installed.
2. Verification results (step 8), one line per check.
3. What only a human can supply here — at minimum `GLIOMA_STORAGE_ROOT`; list anything else you
   found unset or machine-specific.
4. Read `docs/research/PROJECT_STATE.md` and state `current_phase` and `status` so the human
   knows where the project actually is.
5. Point them at the next step: `docs/research/prompts/CLAUDE_PHASE_PROMPT.md` or
   `docs/research/prompts/CODEX_PHASE_PROMPT.md` to resume research work — **do not invoke either
   yourself**, this prompt's job ends at a working environment.
