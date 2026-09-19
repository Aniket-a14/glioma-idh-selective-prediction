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
| C-006 | Fix the TCGA-GBM/TCGA-LGG ID normalizer double-prefix bug: real GDC barcodes (`TCGA-12-0819` format, confirmed live during Phase 03 T03.4) already start with `TCGA-`, but `normalize_tcga_gbm_id`/`normalize_tcga_lgg_id` only skip re-prefixing when a value starts with the full cohort prefix (`TCGA-GBM-`/`TCGA-LGG-`), so a real barcode gets double-prefixed to e.g. `TCGA-GBM-TCGA-12-0819`. See `docs/research/PROJECT_STATE.md`'s T03.4 review entry (2026-09-18) for the original finding. Read `src/glioma_selective/leakage/id_normalization.py`'s module docstring first — it explains why these two cohorts use a deliberately conservative normalizer (no real inventory was in hand when it was written; now one is). Propose a fix, but if the *right* canonical target form isn't obvious from the existing conservative-normalizer pattern, say so explicitly in the PR description and let the Research Lead decide rather than picking one unilaterally. | `src/glioma_selective/leakage/id_normalization.py`, `tests/unit/test_id_normalization.py` | solankisuryansh | `contrib/solankisuryansh/tcga-id-normalizer-fix` | Touches `leakage/` — mandatory Claude review before merge, same rule as every Codex change to this directory. |
| C-007 | Proofread Phase 03's new documentation for typos, broken internal links, and inconsistent terminology (same task type as C-002/C-004, scoped to files written since that round). Content/data changes are out of scope — flag anything that looks factually wrong in a PR comment rather than editing the numbers yourself. | `docs/research/protocols/LABEL_DEFINITIONS.md`, `docs/research/protocols/SPEC_VS_VERIFIED_COUNTS.md`, `docs/research/protocols/POST_EXCLUSION_CLASS_COUNTS.md`, `docs/research/protocols/DATA_ACCESS_LOG.md` | priyaagrawal2 | `contrib/priyaagrawal2/phase03-docs-proofread` | Does **not** include `DECISION_LOG.md` or `PROJECT_STATE.md` — those are Research-Lead-only per the hard rules below, proofreading or not. |
| C-008 | Add a new section to `paper/RELATED_WORK_DRAFT.md` (append, don't rewrite the existing selective-prediction/conformal-prediction section) summarizing 3–5 recent papers on cross-dataset patient overlap / leakage in public glioma or brain-tumor imaging benchmarks (e.g. BraTS's known TCGA/CPTAC/IvyGAP provenance, de-duplication practices across TCIA collections). This is directly motivated by what Phase 03 actually found — the UCSF-PDGM/BraTS-2021 overlap this project had to detect and exclude (`docs/research/DECISION_LOG.md` D-020, for context only — don't edit that file). Same citation-quality bar as the existing section: real papers, real DOIs/arXiv IDs, in the same reference-list format already used in the file. | `paper/RELATED_WORK_DRAFT.md` | ShantanuTripathi2745 | `contrib/ShantanuTripathi2745/related-work-cross-dataset-overlap` | Draft only — flagged in the file's own header as requiring Research Lead review before it moves into the manuscript. |
| C-009 | Add edge-case tests for `utils/paths.py` covering a real, currently-untested interaction: whether `GLIOMA_DATA_ROOT`/`GLIOMA_ARTIFACT_ROOT` overrides correctly propagate to the *subdirectory* accessors (`raw_data_dir()`, `external_data_dir()`, `manifests_dir()`, `cache_dir()`, etc.), not just to `data_root()`/`artifact_root()` themselves (which are already tested). Read the existing `test_subdirectory_accessors` parametrized test in `tests/unit/test_paths.py` first — it only ever sets `GLIOMA_STORAGE_ROOT`, never the two override variables, so this is a genuine gap, not a rewrite of existing coverage. | `tests/unit/test_paths.py` | udaypratapchauhan | `contrib/udaypratapchauhan/paths-override-tests` | Tests-only carve-out of a Codex-owned directory, same pattern as C-001. |
| C-010 | Add failure-path and edge-case unit tests for `src/glioma_selective/leakage/cohort_manifest.py` (the T03.11 roster-hash + committed-manifest module). Read that file and `tests/unit/test_cohort_manifest.py` first — the existing file has only 3 tests (happy path, sort/normalize, changed roster), and none of the module's `CohortManifestError` branches are exercised. Cover, with **synthetic IDs only** (`BT0001`, `UCSF-PDGM-001` style — never a real patient ID): (1) `compute_roster_sha256` returns the same digest for any input order; (2) a duplicate ID inside one roster, including two spellings that normalize to the same ID (`bt-0001` and `UTSW_BT_0001`), raises `CohortManifestError` matching "duplicate"; (3) an un-normalizable ID raises `CohortManifestError` matching "entry .* is invalid"; (4) an unsupported cohort string raises `CohortManifestError` matching "unsupported manifest cohort"; (5) `build_cohort_manifest` raises when a cohort's roster is missing, and when the roster's length differs from the exclusion manifest's `retained_patient_count`; (6) `verify_roster_digest` raises on a malformed `roster_sha256` (wrong length / non-string), on a count mismatch, and on a `roster_construction` mismatch. Tests only: if a test exposes what looks like a bug in `cohort_manifest.py`, do **not** fix the source — describe the failing input in the PR description and let the Research Lead decide. | `tests/unit/test_cohort_manifest.py` | Akshita1395 | `contrib/Akshita1395/cohort-manifest-edge-tests` | Touches `leakage/`-adjacent tests — mandatory Claude review before merge, same rule as C-006. Does not overlap C-006 (`test_id_normalization.py`) or C-009 (`test_paths.py`). Needs no SSD or `GLIOMA_STORAGE_ROOT`. |

## In progress

| ID | Task | Assigned to | Branch | PR |
|---|---|---|---|---|
| — | — | — | — | — |

## Done

| ID | Task | Closed by | PR | Merged |
|---|---|---|---|---|
| C-001 | Add edge-case unit tests for `utils/paths.py` | solankisuryansh | [#1](../../../pull/1) | 2026-09-15 |
| C-002 | Proofread top-level docs for typos, broken internal links, and inconsistent terminology | priyaagrawal2 | [#2](../../../pull/2) | 2026-09-17 |
| C-004 | Proofread the protocol docs for typos, broken internal links, and inconsistent terminology | Akshita1395 | [#4](../../../pull/4) | 2026-09-18 |
| C-003 | Draft a related-work paragraph summarizing 3–5 recent papers on selective prediction / conformal prediction in medical imaging | ShantanuTripathi2745 | [#5](../../../pull/5) | 2026-09-18 |
| C-005 | Draft a related-work paragraph on missing-modality robustness | udaypratapchauhan | — (no PR) | closed 2026-09-18 by Research Lead decision, not completed — round closed out to start Phase 01; re-queue as a fresh row if this content is still wanted later |

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
- One assigned task at a time per person. If you finish early and want more, ask the Research
  Lead for a new row rather than picking your own.
- Use the exact branch name in the "Branch" column — don't invent your own slug. This, plus each
  row's disjoint "Allowed paths", is what guarantees no two contributors' work can collide at
  merge time: different branch, different files, and (per the rule above) nobody but the Research
  Lead ever writes to this table.
