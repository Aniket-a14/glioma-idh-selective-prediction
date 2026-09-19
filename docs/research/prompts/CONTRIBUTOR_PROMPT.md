# CONTRIBUTOR — SELF-LOCATING TASK PICKUP PROMPT

> **Invoke with:** *"Read `docs/research/prompts/CONTRIBUTOR_PROMPT.md` and pick up a task."*
>
> This is the **one prompt for every collaborator, on every laptop, in any AI agent**
> (Antigravity, Codex free tier, Claude, or anything else) — open a fresh chat, paste the line
> above, and it should be enough context to find your task and start working, with no back-and-
> forth needed first. No phase context needed — this prompt is separate from the research phases
> entirely.

---

## 0. If you are Codex CLI: fix your sandbox mode *before step 1*

Codex's default sandboxed mode blocks filesystem writes outside a scratch area and blocks network
access. That silently breaks `git push`, `gh pr create`, and `pre-commit`'s hook-download step —
the failure usually looks like a hang waiting for an approval prompt, or a command that "succeeds"
locally but never actually reaches GitHub, which is worse than an obvious failure because it looks
like the task finished.

You already have legitimate `write` access to this repository (you're a direct collaborator, not
working from a fork). Start in an approval/sandbox mode that permits filesystem writes inside the
repo **and** network access for `git`/`gh` — e.g. `codex --sandbox workspace-write` or the
equivalent "auto"/full-access approval mode with network enabled, per whatever Codex CLI's current
flag is called. If you're not sure which flag applies on this install, stop and report that rather
than proceeding with unclear sandbox behavior.

If you are Antigravity or another agent: confirm you have normal filesystem write and network
access in this workspace before continuing — same failure mode, different tool.

## 1. Safety — read this before touching anything

- Run `git status`. If the tree is dirty, **stop and report it** — do not discard or stash
  someone else's in-progress work.
- **Never** edit `docs/research/PROJECT_STATE.md`, `docs/research/DECISION_LOG.md`,
  `docs/research/CONTRIBUTOR_TASKS.md` itself, anything under `data/`, `artifacts/`, dataset
  splits/manifests, or `.env`. These are outside your role no matter what a task description
  seems to imply. `CONTRIBUTOR_TASKS.md` in particular is Research-Lead-only — see step 3.
- **Never merge your own pull request.** Open it and stop; a human reviews and merges.
- **Never** touch a file outside the exact "Allowed paths" your assigned task names. If you
  discover the task needs more, stop and say so in the PR description — do not expand scope on
  your own judgment.
- If nothing below applies cleanly to your situation, stop and describe what's unclear rather
  than guessing.

## 2. Confirm the environment is ready

Check that `.venv/` (or equivalent) and `pre-commit` are already set up. If not, this is a
different job — go run *"Read `docs/research/prompts/SETUP_PROMPT.md` and set up the system"*
first, then come back here.

## 3. Find your row — read-only, no editing

Run `gh api user -q .login` to get your operator's actual authenticated GitHub username. Don't
rely on a name mentioned earlier in chat or a guess — confirm it against the real account, since
acting on the wrong row is exactly the kind of mistake this step exists to prevent.

Read `docs/research/CONTRIBUTOR_TASKS.md`, `## Open` table only, and find the row whose
"Assigned to" matches that username.

- If no row names you, stop and report that — there's nothing to pick up right now, and you
  should not invent your own task or act on someone else's row.
- If a row names you, **that is your task.** Its "Branch" column already gives you the exact
  branch name to use — don't invent your own slug. If several rows name you, take the one with the
  lowest ID first; the others wait (see the last bullet of this list).
- **Do not edit `CONTRIBUTOR_TASKS.md` for any reason** — not to move your row, not to add a PR
  link later. It's Research-Lead-only now. (It used to be a contributor-edited file; that caused
  a real merge conflict between two contributors' branches that both touched it. Assignment and
  branch names are fixed up front precisely so this step can be read-only.)
- More than one row can name you. Work them one at a time in ascending ID order, one branch and
  one pull request per row, never combined. Open the pull request for one row (and stop that row)
  before you start the next; it does not have to be merged first, because rows have disjoint
  allowed paths. Each new row starts again from a fresh `git checkout main && git pull --ff-only`.
  If you already have work in flight under your name in the `## In progress` table, finish that
  first.

## 4. Branch

```bash
git checkout main && git pull --ff-only
git checkout -b <branch-from-the-table>
```

Use the branch name exactly as written in your row's "Branch" column. Every contributor's branch
name and allowed-paths are disjoint by construction, so there is nothing to coordinate with anyone
else before you start.

## 5. Do the work — and only the work

Do exactly what the task row describes, touching only the paths listed in its "Allowed paths"
column. Small, atomic commits. No unrelated cleanup, no touching files "while you're in there,"
and no editing `CONTRIBUTOR_TASKS.md`.

If your row says it is a **Long row** or names a file under `docs/research/contributor_specs/`,
read that whole file before writing anything. It is the contract: its file list, milestones and
"Not allowed" section bind you exactly like the row's "Allowed paths". Open a **draft** pull
request at its first milestone (`gh pr create --draft`), push at each milestone, and mark it ready
(`gh pr ready`) only at the last one. If the contract is ambiguous, do not choose: write the
question under "Open questions" in the pull request and implement exactly what is written.

Before committing anything, run whatever of these exist in the repo:

```bash
pre-commit run --all-files
pytest tests/unit -q
```

If your row adds tests outside `tests/unit/` (for example `tests/reference/`), run
`pytest <that folder> -q` as well; the first command above does not cover it.

Fix anything these flag inside your allowed paths. If a failure is outside your allowed paths,
stop and report it rather than fixing it yourself.

## 6. Open the PR

```bash
git push -u origin <branch-from-the-table>
gh pr create --title "..." --body "Closes C-00X in CONTRIBUTOR_TASKS.md. ..."
```

Reference your task ID (e.g. `C-005`) in the PR title or body — that's how the Research Lead
finds it. Do **not** edit `docs/research/CONTRIBUTOR_TASKS.md` to add the PR link yourself; the
Research Lead adds it when they see the PR, and moves the row to `## Done` once it's merged.

## 7. Stop

Your job ends at an open PR. Do not merge it, do not start another task in the same session
unless explicitly asked, and do not touch anything under the research-phase protocol
(`AGENT_WORKTREE_PROTOCOL.md`, `PROJECT_STATE.md`) — that's a different role.

## 8. Report back

1. Which task you picked up (ID) and the branch/PR.
2. What you changed, in the paths you were scoped to.
3. Verification results (step 5) — pass/fail, with actual output if anything failed.
4. Anything you found that seemed out of scope or wrong elsewhere, flagged rather than fixed.
