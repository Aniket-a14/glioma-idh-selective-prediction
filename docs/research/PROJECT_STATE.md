# PROJECT STATE

**The single source of truth for "where are we."** Agents read this first and update it last.
Do not hand-edit the status block during an agent run — let the agent own it.

```yaml
current_phase: 02
status: not-started       # not-started | in-progress | blocked | awaiting-integration | complete
claude_tasks: not-started  # not-started | in-progress | done
codex_tasks: not-started   # not-started | in-progress | done | none-this-phase
integration_mode: research-lead   # research-lead | agent
blocked_on: null
last_updated: 2026-09-18
last_agent: claude
```

## Field meanings

| Field | Meaning |
|---|---|
| `current_phase` | The phase being worked. Advanced **only** by Claude, and only when the previous phase genuinely exited. |
| `status` | `blocked` means a human must act before any further work is possible. |
| `integration_mode` | `research-lead` (default): agents leave branches ready and you merge. `agent`: Claude merges and tags itself once gates pass. |
| `blocked_on` | What the human must resolve. Null when not blocked. |

Contributor (non-Claude/Codex) activity is tracked separately in `docs/research/CONTRIBUTOR_TASKS.md` and never changes any field on this page.

## Human-gated phases — `integration_mode: agent` never applies

**Phases 05, 11, and 12 always require the Research Lead**, regardless of the setting above:

- **Phase 05** freezes the splits and the pre-registration. Once frozen, C4's tolerance band and the
  abstention definition can no longer move — that is the whole point, and it needs a human signature.
- **Phase 11** is Gate E. Authorizing external evaluation is a scientific commitment, not a merge.
- **Phase 12** is the single external run. It cannot be rolled back.

An agent reaching one of these prepares everything, sets `status: awaiting-integration`, and stops.

## Progress log

Append one line per agent run. Newest at the bottom.

| Date | Agent | Phase | What happened |
|---|---|---|---|
| 2026-09-11 | claude | 00 | All three Claude tasks done, each on its own branch: T00.5 `agent/claude/p00-path-abstraction` (`utils/paths.py` + 26 passing unit tests), T00.7 `agent/claude/p00-config-system` (D-013 logged: Hydra chosen over OmegaConf/pydantic-settings; `configs/` skeleton + 4 passing composition tests), T00.9 `agent/claude/p00-paper-skeleton` (`paper/{NEGATIVE_RESULTS,LIMITATIONS,REGISTRY}.md`, LIMITATIONS pre-seeded from D-001/D-008/D-012). Also fixed an unrelated `.gitignore` bug (unanchored `data/`/`artifacts/`/`cache/` patterns were silently excluding `configs/data/` and `src/glioma_selective/data/` from Git entirely) on the config-system branch. |
| 2026-09-11 | codex | 00 | Completed T00.2, T00.3, T00.4, T00.6, T00.8, and T00.10 on `agent/codex/p00-tooling` (`pyproject.toml`, pre-commit config, Gate A/B workflows, `scripts/check_invariants.py` + tests, `experiments/REGISTRY.md`). |
| 2026-09-11 | claude | 00 | Merged all four Phase 00 branches into `main` (order: codex tooling → path abstraction → config system → paper skeleton), resolving one conflict in this file. Fixed post-merge integration gaps: added `hydra-core`/`omegaconf` as runtime dependencies to `pyproject.toml` (D-013 needs them to actually import), fixed 4 ruff `E501` violations surfaced once linting was available, ignored packaging build artifacts in `.gitignore`. Verified on the merged tree: `pre-commit run --all-files`, `pytest tests -q -m "not gpu"` (32 passed), `mypy`, `radon cc`/`mi`, and `scripts/check_invariants.py` (incl. its own planted-violation test) all pass. Pushed to `origin/main`; Gate A ran on GitHub Actions and passed (46s, run 34582021365). Gate B is configured `on: pull_request` and this integration used direct local merges per `AGENT_WORKTREE_PROTOCOL.md` §2, so its GitHub check did not fire — the equivalent full-CPU-suite command from that protocol's own template was run locally instead and passed. All 8 Phase 00 acceptance criteria met. Tagged `phase-00-complete`; advancing to Phase 01. |
| 2026-09-18 | claude | — | Off-phase docs fix, not phase-file work: found that `CONTRIBUTOR_TASKS.md`'s contributor-edited claim/PR-link workflow was the actual cause of a real merge conflict between two contributor branches (PR #4 vs PR #5). Made the file Research-Lead-only (contributors read, never write), rewrote `CONTRIBUTOR_PROMPT.md` as the single unified pickup prompt with `gh api user -q .login` self-identification and Codex sandbox-mode fix as step 0, and documented the conflict region in `AGENT_WORKTREE_PROTOCOL.md` §6. PR #6, merged directly per Research Lead authorization (`--admin`, this specific request). First contributor round closed out: C-001/C-002/C-003/C-004 merged (PRs #1/#2/#4/#5); C-005 closed without a PR by Research Lead decision to proceed straight to Phase 01. All 5 collaborators confirmed to have working `git`/`gh` setups (each pushed at least one PR). Phase 01 not yet started. |
| 2026-09-18 | codex | 01 | Completed T01.1 and T01.8 on `agent/codex/p01-bootstrap-storage` (`95c94c5`): idempotent `data/` and `artifacts/` symlink bootstrap with safe refusal/reporting, including preservation and validation of a separately managed `data/external` symlink; added integration coverage. Gate A and the required unit/integration suites passed using the repository `.venv`. T01.3 was not touched. |
| 2026-09-18 | codex | 01 | Completed T01.3 on `agent/codex/p01-env-capture`: added the fourteen-field JSON environment fingerprint, explicit CPU-only/GPU-absent states, both dependency-lock states, and focused tests. Gate A passed with 40 unit tests, invariant scan, and pre-commit. |
| 2026-09-18 | claude | 01 | Orchestrated both Codex sessions above via `codex exec` (T01.3's first attempt correctly stopped on an undefined lock format — logged D-016, uv/`requirements.lock.txt`, then re-ran). Merged both branches into `main` after independently re-running their tests. Ran `bootstrap_storage.py` for real on this machine (T01.2): `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`, `data/external` symlinked to `/Volumes/Research_1` per D-014's two-drive accommodation; idempotent on a second run. Confirmed SSH to the home GPU server (`home-gpu`, Tailscale-authenticated). Wrote T01.9's `RECOVERY_RUNBOOK.md` (D-015: six failure modes, not the five named in the task row). T01.5/T01.7 still blocked on T01.4 (env capture run on the GPU server). |
| 2026-09-18 | claude | 01 | Completed Phase 01. T01.4: captured environment on the GPU server — found and fixed a full root filesystem (28GB runaway log, unrelated project directory, both removed with sign-off), set up a scoped read-only GitHub deploy key, cloned the repo to `/data/glioma-idh/`. Measured VRAM 8GB / RAM 15.48GB vs. SPEC's 16-24GB/≥32GB targets — logged D-017 (OPEN, blocking Phase 06 on timeline only); Research Lead clarified the real Phase 06 training environment is upcoming NVIDIA Labs A100 access, not this machine. T01.5: pinned `torch>=2.4,<3`/`monai>=1.4,<2`, generated `requirements.lock.txt` via `uv pip compile --universal` (torch 2.14.0, monai 1.6.0). T01.6: installed the lock on both machines, confirmed identical hash and `torch.cuda.is_available()`/capability match on the server. T01.7: SegResNet forward+backward benchmark on the actual 8GB card — all four {96,128}³ × {1,2} cells fit comfortably (peak 4.66GB), framed explicitly as a smoke test, not the A100 sizing decision. All 8 acceptance criteria met (criterion 3, free space ≥500GB, met via D-014's logged deviation, not literally). Gate A/B verified on the merged tree: pre-commit, 40 unit tests, mypy, radon cc/mi, check_invariants.py all pass. Advancing to Phase 02. |
