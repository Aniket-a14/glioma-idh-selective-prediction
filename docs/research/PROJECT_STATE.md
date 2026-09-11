# PROJECT STATE

**The single source of truth for "where are we."** Agents read this first and update it last.
Do not hand-edit the status block during an agent run — let the agent own it.

```yaml
current_phase: 00
status: awaiting-integration   # not-started | in-progress | blocked | awaiting-integration | complete
claude_tasks: done         # not-started | in-progress | done
codex_tasks: done          # not-started | in-progress | done | none-this-phase
integration_mode: research-lead   # research-lead | agent
blocked_on: null
last_updated: 2026-09-11
last_agent: claude
```

## Field meanings

| Field | Meaning |
|---|---|
| `current_phase` | The phase being worked. Advanced **only** by Claude, and only when the previous phase genuinely exited. |
| `status` | `blocked` means a human must act before any further work is possible. |
| `integration_mode` | `research-lead` (default): agents leave branches ready and you merge. `agent`: Claude merges and tags itself once gates pass. |
| `blocked_on` | What the human must resolve. Null when not blocked. |

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
| 2026-09-11 | claude | 00 | Merging all four Phase 00 branches into `main` at the Research Lead's request. See below for the merge/Gate B report. |
