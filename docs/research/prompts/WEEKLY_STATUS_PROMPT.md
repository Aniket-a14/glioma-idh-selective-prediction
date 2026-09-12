# WEEKLY STATUS — SELF-LOCATING CAPSTONE DEMO REPORT

> **Invoke with:** *"Read `docs/research/prompts/WEEKLY_STATUS_PROMPT.md` and generate this
> week's update."*
>
> Produces a short, dated summary of what happened this week, per contributor, for the Friday
> capstone discussion class. Read-only against the repository except for writing the one report
> file — never touches `PROJECT_STATE.md`, `DECISION_LOG.md`, or any other operational file.

---

## 1. Determine the window

Use git's own date parser — no OS-specific date arithmetic needed, this is identical on macOS and
Linux/WSL2:

```bash
git log --since="last friday" --all --pretty="%an|%ae|%ad|%s" --date=short
```

If today itself is Friday, this correctly returns the last 7 days (git resolves "last friday" to
the most recent Friday strictly before today, or today if invoked before any commits landed
today — treat an empty result as "nothing new," not an error).

## 2. Gather the material

1. The commit list from step 1, grouped by author.
2. `gh pr list --state all --search "updated:>=<window-start-date>"` if `gh` is available and
   authenticated — adds PR titles/links/state (open, merged, draft) the commit list alone won't
   show. Skip this silently if `gh` isn't available; don't block the report on it.
3. Read `docs/research/PROJECT_STATE.md`'s progress log — any rows dated within the window.
4. Read `docs/research/CONTRIBUTOR_TASKS.md` — any rows that moved between `Open` → `Claimed` →
   `Done` within the window (you won't have exact dates for these; use the PR/commit dates from
   steps 1–2 as a proxy).

## 3. Write the report

Create `docs/research/status/<YYYY-MM-DD>.md` (today's date). Create the `docs/research/status/`
directory if it doesn't exist yet. Structure:

```markdown
# Status — week ending <today's date>

## Research phase
<one paragraph: current_phase, status, what moved, pulled from PROJECT_STATE.md's progress log
for this window — or "no phase-file activity this week" if the log has no new rows>

## Contributors
### <github username or commit author name>
- <bullet per meaningful commit/PR, plain language, not a commit-message dump>
- Task: <C-00X from CONTRIBUTOR_TASKS.md if applicable> — <Open/Claimed/Done>

### <next contributor>
...

## Nothing to report
<list anyone with zero activity this window, plainly — this is a capstone class, the point of
the report is visibility, not flattery>
```

One bullet list per person who has any commit, PR, or task-claim activity in the window —
including you (Research Lead) and Claude/Codex activity if relevant, not just the 5 teammates.
Keep each bullet to what a classmate/instructor needs to follow, not raw commit messages.

## 4. Report back

Print the path to the file you just wrote and paste its contents into the chat so it's ready to
read from directly in the Friday class. Do not modify any file besides the new dated report.
