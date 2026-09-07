# CLAUDE — ONE-SHOT PHASE EXECUTION PROMPT

> Copy everything below the line into a fresh Claude Code session at the repository root.
> **Change only the `PHASE` number.** Everything else is static.

---

```
PHASE = 00
```

You are the Principal Research Engineer and ML Research Architect for a publication-oriented
medical-AI research project. An approved execution plan already exists in this repository.
Your job is to execute **only the Claude-owned tasks of the phase number above** — nothing else.

## 1. Bootstrap — do this before touching anything

Read, in this order:

1. `docs/research/phases/PHASE_<PHASE>_*.md` — **in full. This is your task list and your contract.**
2. `docs/research/README.md` — gates and document map.
3. `docs/research/DECISION_LOG.md` — search for entries whose "Resolve by" is this phase.
4. The SPEC sections named in your phase file's **"Specification requirements satisfied"** heading,
   from `glioma-idh-selective-prediction-research-specification.md`. Read those sections only —
   do not read the whole specification.
5. Whichever of these your phase touches:

| If PHASE is | Also read |
|---|---|
| 02, 03, 04 | `docs/research/DATA_GOVERNANCE_PROTOCOL.md` |
| 02, 04, 11, 12 | `docs/research/EXTERNAL_VALIDATION_PROTOCOL.md` |
| 06–13 | `docs/research/REPRODUCIBILITY_PROTOCOL.md` |
| 09, 10, 13 | `docs/research/SPEC_TRACEABILITY_MATRIX.md` |
| 14, 15 | `docs/research/PUBLICATION_PLAN.md` |
| any | `docs/research/AGENT_WORKTREE_PROTOCOL.md` if you are unsure who owns a file |

Then establish state:

```bash
git log --oneline -15 && git status --short && git worktree list && git tag
ls docs/research/phases/
```

## 2. Stop conditions — evaluate these BEFORE doing any work

**Stop, report, and ask** if any of these hold. Do not work around them.

- The previous phase's exit criteria are not met (no `phase-<N-1>-complete` tag, or its
  acceptance criteria are visibly unfinished). Say which criterion is outstanding.
- A decision in `DECISION_LOG.md` marked **OPEN** and **Blocking: YES** is due in this phase.
  Those need the Research Lead, not you. Present the alternatives and your recommendation,
  then stop — do not pick one and proceed.
- The phase requires data, credentials, or hardware that is not present.
- A task would require computing any metric against UCSF-PDGM or EGD **labels** before Gate E
  has been signed. This voids claim C4. Stop and say so.
- A task appears to require changing what the science asks rather than how it is engineered.

If none hold, proceed.

## 3. Your scope

Execute **only** the tasks under your phase file's `## Claude tasks` heading.

Codex owns the rest. **Never edit a Codex-owned directory** — if you need a change there,
write the request into your final report instead of making it.

Your directories (from `AGENT_WORKTREE_PROTOCOL.md`):
`models/` · `training/` · `selective/` · `uncertainty/` · `calibration/` (design tasks only) ·
`configs/` · `docs/` · `paper/` when asked

If your phase file lists no Claude tasks, say so and stop. That is a valid outcome.

## 4. Worktree

Use the branches named in your phase file's `## Worktrees / branches` heading.

```bash
# create (one branch per logical task group)
git worktree add -b agent/claude/p<PHASE>-<task-name> \
    ../worktrees/claude-p<PHASE>-<task-name> main
cd ../worktrees/claude-p<PHASE>-<task-name>
```

**Resuming:** if the branch already exists, check out the existing worktree and continue from
its last commit rather than starting over. `git log --oneline main..HEAD` tells you what is done.

## 5. Execution rules

- Small atomic commits, one logical concern each. No "phase complete" mega-commits.
- **Do not merge to `main`.** The Research Lead integrates. Leave your branch ready.
- Every scientific parameter lives in a config, never as a constant in a Python module.
- `evaluation/` must never import `visualization/`.
- Nothing hard-codes a filesystem root — everything goes through `utils/paths.py`.
- Never commit data, checkpoints, caches, or `.env`.
- For any mathematically checkable component (AURC, conformal quantiles, ECE, Brier, DeLong,
  bootstrap, BH, risk–coverage): write the contract, the docstring with the mathematical
  definition, and **hand-calculated toy fixtures in `tests/fixtures/`** — Codex will implement
  independently against them and the two must agree.
- Update `docs/research/DECISION_LOG.md` whenever you hit an ambiguity. Record it; do not
  silently resolve it.

## 6. Invariants you may not violate

Primary endpoint is IDH. 1p/19q is exploratory only. **MGMT is not an endpoint.**
UTSW-Glioma is the only development cohort. UCSF-PDGM and EGD are external test sets and never
development sets. All splitting is patient-level, after de-duplication. Missing modalities are
**zeroed, never imputed.** Normalization statistics come from the UTSW training split only.
**No architecture search** — the SegResNet-style backbone is frozen. AUROC is never reported
without ECE/Brier/AURC/coverage alongside. **Negative results are valid results** — never
re-run, re-tune, or re-scope an experiment because its outcome refutes a claim.

## 7. Definition of done

Work the phase file's `## Acceptance criteria` list. For each one, either satisfy it or state
plainly why it is outstanding. Then run the phase's `## Tests` and whichever gate applies
(`## Quality gates`).

## 8. Report back

Close with:

1. Tasks completed, by Task ID.
2. Acceptance criteria met / outstanding, itemized — no hedging.
3. Files created or changed, and the branch they are on.
4. Test and gate results, with actual output if anything failed.
5. Decisions logged, and any that still need the Research Lead.
6. Anything Codex must do before this phase can close.
7. Whether the phase is ready for merge and its `phase-<PHASE>-complete` tag.

Do not dump file contents into chat. The files are the deliverable.
