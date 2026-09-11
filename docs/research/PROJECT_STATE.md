# PROJECT STATE

**The single source of truth for "where are we."** Agents read this first and update it last.
Do not hand-edit the status block during an agent run — let the agent own it.

```yaml
current_phase: 00
status: not-started        # not-started | in-progress | blocked | awaiting-integration | complete
claude_tasks: not-started  # not-started | in-progress | done
codex_tasks: done          # not-started | in-progress | done | none-this-phase
integration_mode: research-lead   # research-lead | agent
blocked_on: null
last_updated: 2026-09-11
last_agent: codex
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
| 2026-09-07 | — | — | Plan approved. Corpus committed. Phase 00 not started. |
| 2026-09-11 | Codex | 00 | Completed T00.2, T00.3, T00.4, T00.6, T00.8, and T00.10 on `agent/codex/p00-tooling`; commits `6d3ebac` and `a7feb37` are ready for Research Lead integration. |
