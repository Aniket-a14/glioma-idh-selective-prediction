# C-021 — `scripts/check_doc_links.py`: find broken Markdown links and anchors automatically

Assigned to udaypratapchauhan. Branch `contrib/udaypratapchauhan/doc-link-checker`. Read-only for you; the Research
Lead edits this file.

## Why this exists

Two finished contributor rows (C-002, C-004) and one open row (C-007) are documentation proofreads done by hand,
including for broken internal links. A script finds those in seconds, on every commit, and never gets tired. The Research Lead will wire it
into pre-commit or CI after review; you only write and test the script.

## Files (nothing else may be touched)

- `scripts/check_doc_links.py` (new)
- `tests/unit/test_check_doc_links.py` (new)

## Behaviour

`python scripts/check_doc_links.py [--repo PATH] [--paths] [--json] [FILE_OR_DIR ...]`. With no positional arguments it
scans `README.md`, `CLAUDE.md`, `docs/**/*.md` and `paper/**/*.md` under `--repo` (default: the repository that
contains the script). Prints `path:line: message` for each problem, sorted by path then line, then a summary line.
Exit code 0 when no broken link is found, 1 otherwise, 2 for bad arguments. Standard library only. It must be
read-only and must finish in under 5 seconds on this repository.

What counts as a link: inline `[text](target)` and `![alt](target)` (with an optional `"title"`), reference links
`[text][ref]` and `[ref]` with a matching `[ref]: target` definition (a use with no definition is a problem), and
`<target>` in angle brackets inside a link. Ignore: text inside fenced code blocks (` ``` ` and `~~~`), inline code
spans, and HTML comments; targets with a scheme (`http:`, `https:`, `mailto:`, `tel:`), which are not checked.

For every other target:

1. Split off `#fragment` and `?query`; percent-decode the path part.
2. A path starting with `/` is relative to the repository root; any other path is relative to the linking file's
   directory. It must exist (file or directory) and must stay inside the repository (a target that escapes the repo
   root is a problem).
3. If there is a fragment: for a target that is a Markdown file (or the same file when the target is just `#frag`), the
   fragment must equal one of that file's heading slugs. For any other existing file, accept `#L<n>` and `#L<n>-L<m>`
   and report anything else. Slugs follow GitHub's rule: take the heading text after removing the leading `#`s and
   surrounding spaces; strip inline Markdown (backticks, `*`, `_` emphasis, and a link `[text](url)` becomes `text`);
   lower-case it; delete every character that is not a letter, digit, space, hyphen or underscore; replace each space
   with a hyphen; a repeated slug in the same file gets `-1`, `-2`, ... appended in order of appearance. Headings inside
   fenced code do not count.

`--paths` adds a second kind of finding, reported as `WARN` and never affecting the exit code: a backticked
repo-relative path that starts with `src/`, `docs/`, `scripts/`, `tests/`, `configs/` or `paper/` and does not exist.
Skip anything containing `*`, `<`, `>`, `{`, `}`, or `...`, and skip lines that say the path is planned (contain the
word `planned`, `will be`, or `not yet`).

## Tests required

Use `tmp_path` trees only. Cover: an existing and a missing file link; a directory link; `/`-rooted links; `../`
links; a link that escapes the repo; percent-encoded names (`My%20File.md`); a query string; an anchor that exists and
one that does not; a same-file `#anchor`; duplicate headings (`-1`, `-2`); headings with backticks, emphasis, a link
inside, punctuation, digits, and an underscore; a heading inside a fenced block that must not count; `#L10` and
`#L10-L20` on a `.py` file; a link inside a fenced block and inside inline code that must be ignored; a reference link
with and without a definition; an image; angle-bracket target; external URLs ignored; `--paths` warnings and their
skips; exit codes 0, 1, 2; `--json` parses. For every rule above, add a test that fails if that rule is removed.

## Real run required in the pull request

Run the script on the real repository (`python scripts/check_doc_links.py --paths`) and paste the full output into the
PR description. **Do not fix any documentation.** For the first five reported problems, open the file yourself and
say whether the script is right; if you find a false positive, that is a bug in your script and must be fixed and
covered by a test. Also pick five anchor links that already exist in the docs and pass, and confirm on GitHub (open the
rendered file in the browser) that each anchor really jumps to the heading. That is the check that your slug rule
matches GitHub's.

## Milestones

The dates are deadlines, not start dates; starting this weekend is fine. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-09-23, open a **draft** pull request) path and directory links, code-fence and code-span skipping.
2. (by Thu 2026-09-24) anchors and slugs.
3. (by Fri 2026-09-25, mark ready) reference links, `--paths`, `--json`, exit codes, the real-repo run in the PR text.

## Not allowed

Editing any `.md` file, `.pre-commit-config.yaml`, `.github/`, `pyproject.toml`, or any file not listed. No new
dependency. If something here is ambiguous, list it under "Open questions" in the pull request and implement it exactly
as written.
