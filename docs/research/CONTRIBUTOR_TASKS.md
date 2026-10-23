# CONTRIBUTOR TASKS

A standing backlog of small, bounded, off-critical-path work for the team's five other
collaborators — Akshita1395, priyaagrawal2, ShantanuTripathi2745, solankisuryansh,
udaypratapchauhan — and whichever AI agent they're running (Antigravity, Codex free tier, or
anything else). The critical research path (phases in `docs/research/phases/`) stays owned by
the Research Lead, Claude, and Codex per `AGENT_WORKTREE_PROTOCOL.md`. This file is the *only*
sanctioned exception to that protocol's directory-ownership table — a task listed here may touch
exactly the paths it names, nothing else.

**Agents: start at `docs/research/prompts/CONTRIBUTOR_PROMPT.md`, not here.** That prompt tells
you how to pick up your row safely. Reading this file alone is not enough context to act on.

**This file is edited only by the Research Lead — never by a contributor or a contributor's
agent, not even to claim a row or add a PR link.** That used to be a contributor step, and it was
the actual cause of a real merge conflict (PR #4 and PR #5 both touched this file's table and
collided). Every row below is now pre-assigned — person, branch name, and allowed paths are all
fixed before any agent starts — so there is nothing left for a contributor to write here. If your
agent thinks it needs to edit this file, it has misread its instructions; it should stop and say
so instead.

**Humans: this file is curated by the Research Lead, weekly**, ahead of the Friday capstone
discussion. Add rows here only when you (Research Lead) have picked a bounded, safe piece of
work off the critical path, picked the exact person, and filled in an exact branch name — never
let a contributor agent invent its own scope or its own branch name.

---

## Open

**Every row is pre-assigned to a specific person and a specific branch name.** There is no
first-come claiming and nothing to edit to "claim" a row — an agent claims a task simply by
reading it and starting work on the named branch. This removes two failure modes at once: two
agents racing for the same row, and two agents' edits to this file colliding with each other.

**Agents: only act on the row whose "Assigned to" is your operator's GitHub username** (confirm
it with `gh api user -q .login` — don't trust an assumption or a name in chat, confirm it against
the actual authenticated account). If no remaining row names your operator, stop and report that
rather than acting on someone else's row or inventing a new task.

| ID | Task | Allowed paths | Assigned to | Branch | Notes |
|---|---|---|---|---|---|
| C-009 | Add edge-case tests for `utils/paths.py` covering a real, currently-untested interaction: whether `GLIOMA_DATA_ROOT`/`GLIOMA_ARTIFACT_ROOT` overrides correctly propagate to the *subdirectory* accessors (`raw_data_dir()`, `external_data_dir()`, `manifests_dir()`, `cache_dir()`, etc.), not just to `data_root()`/`artifact_root()` themselves (which are already tested). Read the existing `test_subdirectory_accessors` parametrized test in `tests/unit/test_paths.py` first — it only ever sets `GLIOMA_STORAGE_ROOT`, never the two override variables, so this is a genuine gap, not a rewrite of existing coverage. | `tests/unit/test_paths.py` | udaypratapchauhan | `contrib/udaypratapchauhan/paths-override-tests` | Tests-only carve-out of a Codex-owned directory, same pattern as C-001. |
| C-012 | Draft the **Methods subsection on preprocessing and quality control** for the paper, as `paper/METHODS_PREPROCESSING_DRAFT.md`, about 600 to 900 words of prose plus a claims table. Sources you may use, and nothing else: `docs/research/protocols/PHASE_04_QC_REPORT.md`, `docs/research/phases/PHASE_04_PREPROCESSING.md`, `DECISION_LOG.md` entries D-023 to D-032 (read only), and the committed files `docs/research/manifests/cohort_manifest_post_qc.json`, `preprocessing_qc_report.json`, `preprocessing_output_audit.json`. Cover: what the source data already was (D-026), what was actually done to it (N4 bias correction, RAS reorientation, mask remapping), the automated verification, the human visual QC design and results, the recalibration of the automated screen and why its agreement is in-sample, and the 6 exclusions. Every number and every factual claim gets a row in a table at the end: claim, value, source file, and the line or section it comes from. Do not add any claim you cannot point to; if two sources disagree or something is unclear, list it under "Open questions" instead of choosing. Do not include patient IDs, label counts for UCSF-PDGM, or anything about model performance. Do not edit `paper/LIMITATIONS.md` (a Limitations paragraph is already drafted in section 5 of the QC report; you may quote it, not rewrite it). | `paper/METHODS_PREPROCESSING_DRAFT.md` (new file) | ShantanuTripathi2745 | `contrib/ShantanuTripathi2745/methods-preprocessing-draft` | `paper/` is human-owned and agents draft into it only when asked; this row is that ask. Claude checks every table row against its source before merge, like PR #9. |
| C-014 | Independent reference test for the exact binomial upper confidence bound used in the QC report: `_clopper_pearson_upper(failures, n)` in `src/glioma_selective/preprocessing/qc_report.py`. Read its docstring and code only for the signature and the contract (one-sided 95% Clopper-Pearson upper bound; `None` when `n == 0`; `1.0` when `failures == n`). Then write your **own** reference in the test file using only the Python standard library: the upper bound is the value `p` in (0, 1) where the binomial CDF `P(X <= failures)` for `n` trials equals 0.05, found by bisection on `math.comb` sums. Compare the two for every `(failures, n)` with `n` in `{1, 2, 5, 10, 20, 40, 62, 100}` and `failures` from 0 to `n`, to within `1e-9`. Add property tests (result in [0, 1]; non-decreasing in `failures` for fixed `n`; non-increasing in `n` for fixed `failures`) and the invalid-input cases (`failures > n`, negative values raise `QCReportError`). Sanity values to check your reference against: (0 of 40) is about 0.0722, (0 of 62) about 0.0472, (1 of 10) about 0.3942. Mutation-check as in PR #8 (for example: change 0.95 to 0.90 in the source, or swap `failures + 1` and `n - failures`, in a scratch copy) and list each break in the PR description. **Do not edit any source file.** | `tests/unit/test_clopper_pearson_reference.py` (new file) | solankisuryansh | `contrib/solankisuryansh/clopper-pearson-reference-test` | This is the repo's independent-implementation pattern for a mathematically checkable component: write the reference from the definition above, not by reading the source's method. Standard library only for the reference; the test may import the function under test. |
| C-015 | Add mutation-checked edge-case tests for `PreprocessingStatusManifest` (`src/glioma_selective/preprocessing/status.py`), the per-case status file that records Phase 04 verification, stages and human QC verdicts. Read `tests/unit/test_preprocessing_status.py` first (14 tests) and cover the gaps you find, for example: save then load returns an equal manifest and a second save is byte-identical; a failed save leaves no temporary file and the old file intact; `load` rejects a wrong `schema_version`, a duplicate case, an unknown cohort and an unknown stage state; `merge_verification` keeps a human verdict when the verification outcome is unchanged and clears it when the outcome changes; `record_visual_qc_verdict` rejects a failed verdict without a category and a passed verdict with one; `summary()` counts and the 10% stop flag at exactly 10% and just above it. Same standard as PR #8: every new test must fail against a deliberate break you make in a scratch copy of the source, and each break is listed in the PR description. **Do not edit any source file**; if a test exposes what looks like a real bug, describe it in the PR and mark the test `xfail` with the reason. | `tests/unit/test_preprocessing_status_edge_cases.py` (new file) | udaypratapchauhan | `contrib/udaypratapchauhan/preprocessing-status-edge-tests` | Synthetic data only; no real IDs and nothing under `data/` or `artifacts/`. |
| C-018 | **Long row (about a week).** Selective-prediction metrics reference implementation: risk-coverage points, selective risk at a coverage, AURC (two definitions), monotonicity violations, rejected-but-correct rate, standard library only, with hand-worked fixtures, a wrong-variant catalogue and property tests. The contract is `docs/research/contributor_specs/C-018_SELECTIVE_PREDICTION_REFERENCE.md`: read it in full before starting, and read `DECISION_LOG.md` D-033. | `tests/reference/selective_reference.py`, `tests/reference/test_selective_reference.py`, `tests/reference/fixtures/selective_cases.json` (all new) | solankisuryansh | `contrib/solankisuryansh/selective-reference` | Independent-implementation pattern for Phase 09 T09.8, built before the real code. Nothing about conformal sets or the D-003 abstention rule. Claude re-derives every fixture by hand before merge. Draft PR by Wed 2026-09-23, ready by Fri 2026-09-25. After C-006 and C-014. |
| C-019 | **Long row (about a week).** Publication figure helpers in `src/glioma_selective/visualization/`: shared style module, a reliability diagram and a risk-coverage plot that take precomputed numbers, and a `save_figure` that writes PNG, PDF and a JSON sidecar of the plotted numbers, byte-reproducible. The contract is `docs/research/contributor_specs/C-019_FIGURE_HELPERS.md`: read it in full before starting. | `src/glioma_selective/visualization/style.py`, `reliability.py`, `risk_coverage.py` (new), `src/glioma_selective/visualization/__init__.py` (edit), `tests/unit/test_visualization_helpers.py` (new) | ShantanuTripathi2745 | `contrib/ShantanuTripathi2745/figure-helpers` | Real source code: must pass mypy, ruff, radon and the invariants check. Phase 07 and Phase 09 sessions will be told to use these helpers. Claude reviews the code and the sample images before merge. Draft PR by Wed 2026-09-23, ready by Fri 2026-09-25. After C-012. |
| C-021 | **Long row (about a week).** `scripts/check_doc_links.py`: a read-only checker for broken Markdown links and heading anchors (GitHub slug rules), with an optional warning for backticked repo paths that do not exist. The contract is `docs/research/contributor_specs/C-021_DOC_LINK_CHECKER.md`: read it in full before starting. | `scripts/check_doc_links.py`, `tests/unit/test_check_doc_links.py` (both new) | udaypratapchauhan | `contrib/udaypratapchauhan/doc-link-checker` | Do not fix any documentation the script finds: paste the output in the PR. Claude reviews the code and checks the reported problems by hand. Draft PR by Wed 2026-09-23, ready by Fri 2026-09-25. After C-009 and C-015. |
| C-022 | **Long row (about a week).** Benjamini-Hochberg reference implementation: adjusted p-values, the step-up reject rule, and Holm as a wrong-variant entry, standard library only, with hand-worked fixtures, a wrong-variant catalogue and property tests. The contract is `docs/research/contributor_specs/C-022_BH_REFERENCE.md`: read it in full before starting. | `tests/reference/bh_reference.py`, `tests/reference/test_bh_reference.py`, `tests/reference/fixtures/bh_cases.json` (all new) | Akshita1395 | `contrib/Akshita1395/bh-reference` | Independent-implementation pattern for the Phase 10 BH correction (SAP section 6), built before the real code. Touches no source file. Claude re-derives every fixture by hand before merge. Draft PR by Wed 2026-10-07, ready by Fri 2026-10-09. After C-016 and C-017 are merged. |
| C-024 | Add mutation-checked edge-case tests for the evaluation-conditions grid: `src/glioma_selective/evaluation/conditions.py` and the frozen `configs/evaluation/conditions.yaml` (6 modality conditions x 3 cohorts x 6 mechanisms = 108 cells, EGD marked unavailable). Read `tests/unit/test_conditions.py` first (8 tests) and the two public functions `load_condition_grid` and `enumerate_cells` and cover the gaps you find, for example: every cell id is unique and stable in order; the counts per cohort and per mechanism; that no cell of an unavailable cohort is marked available; that a zeroed-channel condition names exactly the channels it should (T1, T1ce, T2, FLAIR), including the "only T1ce + FLAIR" condition; that `load_condition_grid` on a config with a duplicate id, overlapping or incomplete present/zeroed modalities, a wrong entry count or no primary mechanism raises `ValueError` (write those configs to `tmp_path`); that `enumerate_cells` returns the same cells in the same order on every call. Same standard as PR #8: every new test must fail against a deliberate break you make in a scratch copy of the source, and each break is listed in the PR description. **Do not edit any source file and do not edit the YAML** (it is frozen; its SHA-256 is in the pre-registration). If a test exposes what looks like a real bug, describe it in the PR (input, expected, actual) and mark the test `xfail` with the reason. | `tests/unit/test_conditions_edge_cases.py` (new file) | udaypratapchauhan | `contrib/udaypratapchauhan/conditions-edge-tests` | Tests only. Synthetic configs written to `tmp_path` for the error cases; the real YAML is read, never written. After C-009, C-015 and C-021. |
| C-025 | Draft a **related-work section on missing-modality robustness in MRI** (modality dropout, hallucination or synthesis, and shared-latent-space methods) for `paper/RELATED_WORK_DRAFT.md`, as a new section after the existing ones, same standard as C-008: 5 to 8 references, each claim checked against the full text of the paper (not the abstract), and a table at the end with reference, the claim you make about it, and the page or section where it appears. Prefer peer-reviewed venues and label preprints as preprints. Say plainly what each method does **not** do (none of them, as far as you can verify, measures whether the model's confidence stays reliable when a sequence is missing) only if you checked it in the text; otherwise leave the sentence out. Do not edit any existing section or any other file. This re-queues the old C-005, which was closed without a PR. | `paper/RELATED_WORK_DRAFT.md` (add one section at the end only) | ShantanuTripathi2745 | `contrib/ShantanuTripathi2745/related-work-missing-modality` | Claude checks every table row against its source before merge, like PR #9. You are the only contributor editing this file, so no conflict is expected. After C-012 and C-019. |

### Status, week of 2026-10-23

- 16 contributor PRs opened since #1: 14 merged (#1, #2, #4, #5, #8, #9, #10, #11, #12, #13, #14, #16, #17, #18), 1 closed unmerged (#3), and #15 still open. PRs #6 and #7 were the Research Lead's own.
- Merged on 2026-10-23: #14 (C-013, approved 2026-10-09), #17 (C-020) and #18 (C-023), after a re-check of the authors' 2026-10-11 revisions. Left over from #17: the real-machine output has no `/proc/version` line (Windows host, no WSL) and per-status test coverage was not measured. Left over from #18: one table row says "a half-width" without naming the quantity.
- #15 (C-006) stays open: the cross-label rejection and test requested on 2026-09-30 are not in it, and the author has not pushed since 2026-09-25.
- Nine Open rows have no branch pushed: C-009, C-015, C-021, C-024 (udaypratapchauhan), C-012, C-019, C-025 (ShantanuTripathi2745), C-014, C-018 (solankisuryansh). The draft-PR dates in C-018, C-019 and C-021 (Wed 2026-09-23) have passed.
- Merged since the last report (2026-09-18): C-008, C-010 (2026-09-19), C-007, C-011 (2026-09-30), C-016, C-017 (2026-10-01), C-022 (2026-10-11), and the three above.

## In progress

| ID | Task | Assigned to | Branch | PR |
|---|---|---|---|---|
| C-006 | TCGA barcode normalizer fix (`leakage/`): cohort-free barcode form adopted; author to make the GBM/LGG normalizers reject cross-labelled input and add a test | solankisuryansh | `contrib/solankisuryansh/tcga-id-normalizer-fix` | [#15](../../../pull/15), changes requested 2026-09-30; waiting on the author, no commit since 2026-09-25 |

## Done

| ID | Task | Closed by | PR | Merged |
|---|---|---|---|---|
| C-001 | Add edge-case unit tests for `utils/paths.py` | solankisuryansh | [#1](../../../pull/1) | 2026-09-15 |
| C-002 | Proofread top-level docs for typos, broken internal links, and inconsistent terminology | priyaagrawal2 | [#2](../../../pull/2) | 2026-09-17 |
| C-004 | Proofread the protocol docs for typos, broken internal links, and inconsistent terminology | Akshita1395 | [#4](../../../pull/4) | 2026-09-18 |
| C-003 | Draft a related-work paragraph summarizing 3–5 recent papers on selective prediction / conformal prediction in medical imaging | ShantanuTripathi2745 | [#5](../../../pull/5) | 2026-09-18 |
| C-005 | Draft a related-work paragraph on missing-modality robustness | udaypratapchauhan | — (no PR) | closed 2026-09-18 by Research Lead decision, not completed — round closed out to start Phase 01; re-queue as a fresh row if this content is still wanted later |
| C-008 | Add a cross-dataset patient overlap / leakage section to `paper/RELATED_WORK_DRAFT.md` (5 references, claims checked against full text) | ShantanuTripathi2745 | [#9](../../../pull/9) | 2026-09-19 |
| C-007 | Proofread Phase 03's new documentation for typos, broken links and terminology | priyaagrawal2 | [#13](../../../pull/13) | 2026-09-30 |
| C-011 | Add mutation-checked edge-case tests for `append_qc_exclusions` (11 deliberate source breaks, all caught) | Akshita1395 | [#10](../../../pull/10) | 2026-09-30 |
| C-010 | Add failure-path and edge-case unit tests for `leakage/cohort_manifest.py` (mutation-checked against 7 deliberate source breaks) | Akshita1395 | [#8](../../../pull/8) | 2026-09-19 |
| C-016 | Phase 04 runbook: stale D-023 note and missing overwrite warnings fixed | Akshita1395 | [#11](../../../pull/11) | 2026-10-01 |
| C-017 | Independent calibration metric reference: four behaviours no test pinned before | Akshita1395 | [#12](../../../pull/12) | 2026-10-01 |
| C-022 | Benjamini-Hochberg reference implementation (11 cases; Codex's `statistics/multiplicity.py` matches it on all 11) | Akshita1395 | [#16](../../../pull/16) | 2026-10-11 |
| C-013 | Phase 04 numbers audit (`protocols/PHASE_04_NUMBERS_AUDIT.md`); numbers correct, audit-trail references fixed | priyaagrawal2 | [#14](../../../pull/14) | 2026-10-23 |
| C-020 | `scripts/check_setup.py` contributor setup checker (the Gate E flag check verified against `export` and repeated assignments) | priyaagrawal2 | [#17](../../../pull/17) | 2026-10-23 |
| C-023 | Methods draft on data splitting and intensity normalization (`paper/METHODS_SPLITS_NORMALIZATION_DRAFT.md`) | priyaagrawal2 | [#18](../../../pull/18) | 2026-10-23 |

---

## Hard rules (same as every other agent role in this repo)

- **Never edit this file.** Assignment, branch naming, and PR-link tracking are Research-Lead-only
  — see the note at the top. This is the one rule in this list that's new relative to how the
  first round worked, and it exists specifically to stop contributor branches from conflicting
  with each other on this table.
- Never touch `PROJECT_STATE.md`, `DECISION_LOG.md`, dataset splits/manifests, `.env`, or anything
  under `data/`/`artifacts/`.
- Never merge your own PR. Every PR here goes through the same branch protection as everyone
  else's: 1 review, conversation resolution, Research Lead decides.
- Never work outside the "Allowed paths" column of your assigned task. If the task turns out to
  need more, stop and say so in the PR description rather than expanding scope silently.
- A person may have more than one row (Research Lead decision, 2026-09-19). Do them one at a time
  in ascending ID order, one branch and one pull request per row, never combined; open the pull
  request for one row before starting the next (it does not need to be merged first, because paths
  are disjoint). If you finish all your rows and want more, ask the Research Lead for a new row
  rather than picking your own.
- A row marked **Long row** has a contract file under `docs/research/contributor_specs/`. That file, not the
  table, is the definition of done. Open a **draft** pull request at its first milestone so progress is visible,
  push at each milestone, mark it ready at the last. Still one branch and one pull request per row.
- Use the exact branch name in the "Branch" column — don't invent your own slug. This, plus each
  row's disjoint "Allowed paths", is what guarantees no two contributors' work can collide at
  merge time: different branch, different files, and (per the rule above) nobody but the Research
  Lead ever writes to this table.
