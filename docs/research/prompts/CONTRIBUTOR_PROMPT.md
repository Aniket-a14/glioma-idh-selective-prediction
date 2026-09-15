# CONTRIBUTOR — SELF-LOCATING TASK PICKUP PROMPT

> **Invoke with:** *"Read `docs/research/prompts/CONTRIBUTOR_PROMPT.md` and pick up a task."*
>
> For any of the project's collaborators, using any AI agent (Antigravity, Codex free tier,
> Claude, or anything else). No phase context needed — this prompt is separate from the research
> phases entirely.

---

You are picking up **one small, bounded, pre-approved piece of side-work** from a curated
backlog. You are not doing research-phase work — that is owned by the Research Lead and two
other agents on a stricter protocol you don't need to read. Your job is: claim → do exactly what
was scoped → PR → stop.

## 0. Safety — read this before touching anything

- Run `git status`. If the tree is dirty, **stop and report it** — do not discard or stash
  someone else's in-progress work.
- **Never** edit `docs/research/PROJECT_STATE.md`, `docs/research/DECISION_LOG.md`, anything
  under `data/`, `artifacts/`, dataset splits/manifests, or `.env`. These are outside your role
  no matter what a task description seems to imply.
- **Never merge your own pull request.** Open it and stop; a human reviews and merges.
- **Never** touch a file outside the exact "Allowed paths" your claimed task names. If you
  discover the task needs more, stop and say so in the PR description — do not expand scope on
  your own judgment.
- If nothing below applies cleanly to your situation, stop and describe what's unclear rather
  than guessing.

## 1. Confirm the environment is ready

Check that `.venv/` (or equivalent) and `pre-commit` are already set up. If not, this is a
different job — go run *"Read `docs/research/prompts/SETUP_PROMPT.md` and set up the system"*
first, then come back here.

**If you are Codex CLI specifically: do not run this in its default sandboxed mode.** Codex's
sandbox blocks filesystem writes outside a scratch area and blocks network access by default,
which silently breaks `git push`, `gh pr create`, and `pre-commit`'s hook-download step — the
failure usually looks like a hang waiting for an approval prompt, or a command that "succeeds"
but never actually reaches GitHub. This operator already has legitimate `write` access to this
repository (it's a direct collaborator, not a fork), so run Codex in an approval/sandbox mode
that permits filesystem writes inside the repo and network access for `git`/`gh` — e.g.
`codex --sandbox workspace-write` or the equivalent "auto" approval mode with network enabled,
per whatever Codex CLI's current flag/setting is. If unsure which flag applies, stop and report
that rather than proceeding with unclear sandbox behavior — a task that silently didn't actually
push is worse than one that didn't run at all.

## 2. Read the backlog

Read `docs/research/CONTRIBUTOR_TASKS.md` in full. Look at the `## Open` table only.

- If it's empty, report that and stop — there's nothing to claim right now, and you should not
  invent your own task.
- **If the table has an "Assigned to" column, only claim the row that names your own GitHub
  username.** Do not claim a row assigned to someone else, even if it looks easier or is first in
  the table — every row in that model is pre-assigned specifically to avoid multiple agents
  landing on the same row at once. If no row names you, stop and report that.
- If the table has no "Assigned to" column (a fully open round), pick exactly **one** row —
  but `git pull --ff-only` first (see step 3) since this is where two agents can race.
- Do not claim a second task while one is still open under your name in `## Claimed`.

## 3. Claim it

```bash
git checkout main && git pull --ff-only
```

Edit `docs/research/CONTRIBUTOR_TASKS.md`: move your chosen row from `## Open` to `## Claimed`,
filling in your GitHub username and the branch name you're about to create. Commit this edit by
itself first (`docs: claim C-00X`), on `main`, and push it directly — this is bookkeeping, not
code, and prevents two people claiming the same task.

If `git push` is rejected as non-fast-forward, **do not force-push.** Someone else pushed to
`main` in between — `git pull --ff-only` again, re-read the table, and check whether your task
row still exists and is still unclaimed (or, under the assignment model, still names you) before
retrying the same edit.

## 4. Branch

```bash
git checkout main && git pull --ff-only
git checkout -b contrib/<your-github-username>/<short-task-slug>
```

## 5. Do the work — and only the work

Do exactly what the task row describes, touching only the paths listed in its "Allowed paths"
column. Small, atomic commits. No unrelated cleanup, no touching files "while you're in there."

Before committing anything, run whatever of these exist in the repo:

```bash
pre-commit run --all-files
pytest tests/unit -q
```

Fix anything these flag inside your allowed paths. If a failure is outside your allowed paths,
stop and report it rather than fixing it yourself.

## 6. Open the PR

```bash
git push -u origin contrib/<your-github-username>/<short-task-slug>
gh pr create --title "..." --body "Closes C-00X in CONTRIBUTOR_TASKS.md. ..."
```

Then edit `docs/research/CONTRIBUTOR_TASKS.md` again: fill in the PR link on your `## Claimed`
row. Do **not** move it to `## Done` yourself — that happens once the PR is actually merged, by
whoever merges it.

## 7. Stop

Your job ends at an open PR. Do not merge it, do not start another task in the same session
unless explicitly asked, and do not touch anything under the research-phase protocol
(`AGENT_WORKTREE_PROTOCOL.md`, `PROJECT_STATE.md`) — that's a different role.

## 8. Report back

1. Which task you claimed (ID) and the branch/PR.
2. What you changed, in the paths you were scoped to.
3. Verification results (step 5) — pass/fail, with actual output if anything failed.
4. Anything you found that seemed out of scope or wrong elsewhere, flagged rather than fixed.
