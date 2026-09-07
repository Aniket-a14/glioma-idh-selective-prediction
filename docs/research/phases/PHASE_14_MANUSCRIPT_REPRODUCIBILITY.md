# Phase 14 — Manuscript and Reproducibility Package

**Duration:** ~21 days · **Gate:** F (continued) · **Compute:** none

## Scientific purpose
Communicate the findings — including and especially the negative ones — with the framing the specification fixed: an empirical trustworthiness study, not an architecture paper.

## Engineering purpose
Produce a reproducibility package that a stranger can actually re-run.

## Specification requirements satisfied
SPEC §5.7 (document per-cohort label methodology), §5.8 (TRIPOD+AI, CLAIM 2024; CONSORT-AI/SPIRIT-AI not applicable; re-check for updates), §6 and §8.2 (differentiate against the five named works), §8.3 (the frozen framing sentence), §9 step 10.

## RQs / claims addressed
All — reported.

## Entry criteria
Gate F passed; results frozen and tagged.

## Inputs
Frozen results, figures, tables; per-phase method notes; decision log; negative-results log; limitation log; bibliography.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T14.1 | Methods, assembled from per-phase notes | A | — | Claude | none | no | T14.5 |
| T14.2 | Results, **from frozen files only — no hand-transcribed numbers** | A | — | Claude | none | no | T14.5 |
| T14.3 | Discussion, including every refuted claim stated plainly | A | — | Claude | none | no | T14.5 |
| T14.4 | Related Work: differentiate against all five named competitors | A | — | Claude | none | yes | T14.5 |
| T14.5 | Introduction and Abstract, anchored on the SPEC §8.3 sentence | A | — | Claude | none | no | T14.9 |
| T14.6 | **Limitations** — simulated missingness, 1p/19q power, internal n, single-institution training, any DEGRADED solo step | A | — | Claude | none | yes | T14.5 |
| T14.7 | TRIPOD+AI checklist | C | A (+4d) | Human+Claude | none | yes | T14.9 |
| T14.8 | CLAIM 2024 checklist | C | A (+3d) | Human+Claude | none | yes | T14.9 |
| T14.9 | **Freshness re-check: TRIPOD+AI / CLAIM updates** | C | A (+1d) | Human | none | no | Phase 15 |
| T14.10 | **Verify-before-cite pass over the whole bibliography** (**D-010**) | C | A+Codex (+4d) | Human | none | yes | T14.11 |
| T14.11 | **Fresh novelty check; adjust or drop the "first" claim** | A | — | Human+Claude | none | no | T14.5 |
| T14.12 | Reproducibility package | A | — | Codex | CPU | yes | T14.13 |
| T14.13 | **Package acceptance test by someone not on the project** | A | — | Human | CPU | no | Gate F |
| T14.14 | Internal technical review | A+C | A (+5d) **DEGRADED** | Human | none | no | Phase 15 |

**T14.2 — no number is typed by hand.** Results text references table cells; tables come from frozen files. Transcription is where errors enter a manuscript, and it is entirely avoidable.

**T14.11 — the "first" claim.** SPEC §8.3 says "first." Per the master prompt, that word does not ship without a fresh literature check dated close to submission. If a competing paper has appeared, **the framing changes and the experiment does not** — the empirical characterization remains valuable regardless of who published first.

**T14.6 — Limitations must include:** simulated rather than natural missingness (**D-008**) · 1p/19q underpowering (63 positives pre-exclusion) · internal test set in the low hundreds with wide CIs at coverage extremes · single-institution training cohort · label heterogeneity across cohorts and eras · any solo-DEGRADED QC or verification step (**D-001**) · single-external-cohort result if EGD did not arrive · any disclosed protocol deviation.

## Human allocation
**A:** owns the manuscript. **C:** checklists, bibliography verification, table verification, technical review. **D–F:** proofreading (non-critical-path).

## Claude tasks
T14.1–T14.6 — drafting and manuscript-facing interpretation.

## Codex tasks
T14.12 — packaging and the regeneration entry point.

## Parallelization map
```
T14.1 ─> T14.2 ─> T14.3 ─┬─> T14.5 ─> T14.14
T14.4, T14.6 ────────────┤
T14.7, T14.8 ─> T14.9 ───┤
T14.10 ─> T14.11 ────────┘
T14.12 ─> T14.13 (parallel)
```

## Files / modules expected
`paper/manuscript/`, `paper/checklists/{tripod_ai,claim_2024}.md`, `paper/bibliography/refs.bib`, `paper/LIMITATIONS.md`, `paper/NEGATIVE_RESULTS.md`, `release/` (reproducibility package).

## Data required
None beyond frozen results.

## Compute required
CPU for the package acceptance test only.

## Outputs / artifacts
Complete manuscript · completed TRIPOD+AI and CLAIM 2024 checklists · freshness-check record · verified bibliography · novelty-check record · reproducibility package · package acceptance-test report · internal technical review record.

## Tests
Package acceptance: a person not on the project clones the release, follows the README, and regenerates every figure and table. **Any failure is a package defect, not a user error.**

## Quality gates
Gate F continues. Manuscript-specific: every number traces to a frozen artifact; every claim traces to evidence; every checklist item is answered.

## Scientific validation
1. Internal technical review by A and C against the traceability matrix.
2. Every RQ answered; every claim adjudicated; every refutation reported.
3. Framing check: does the manuscript claim architectural novelty anywhere? (**It must not.**)
4. Differentiation check: are all five competitors explicitly addressed?

## Acceptance criteria
1. Manuscript complete, all sections drafted.
2. Every number traces to a frozen artifact; **zero hand-transcribed numbers.**
3. Every refuted claim reported plainly, in the abstract if primary.
4. All five competitors explicitly differentiated (GMMAS, Elyassirad, Yogananda, RISEN, FoundBioNet).
5. Framing matches SPEC §8.3; **no architectural-novelty claim anywhere.**
6. TRIPOD+AI checklist complete.
7. CLAIM 2024 checklist complete.
8. **Freshness re-check performed and dated** — both guidelines confirmed current or the newer version adopted.
9. **CONSORT-AI/SPIRIT-AI not cited** (they do not apply to a retrospective non-interventional study).
10. Every reference verified; unverifiable references dropped (**D-010**).
11. Fresh novelty check performed and dated; the "first" claim supported or removed.
12. Limitations complete, including simulated missingness and any DEGRADED step.
13. Reproducibility package complete; **acceptance test passed by someone not on the project.**
14. Internal technical review complete; every finding resolved.

## Failure conditions
A number cannot be traced → remove it or find its provenance · the novelty check finds a competing paper → **re-frame honestly; do not conceal it** · the package acceptance test fails → the package is incomplete · a checklist item cannot be answered → the study has a gap that must be disclosed.

## Rollback / recovery
Manuscript drafts are versioned in Git. Results are frozen and do not change; only the writing does.

## Risks
R-M03 (unverifiable citations) · R-M04 (guideline updates) · R-M05 (a competitor closing the gap) · R-M06 (simulated-missingness challenge — pre-empted in Limitations) · R-M02 (solo-DEGRADED review, disclosed).

## Decisions requiring Research Lead approval
Final venue · authorship order and CRediT contributions · whether the "first" claim survives the novelty check · what is main text vs. supplementary · AI-tool disclosure wording per the venue's policy.

## Exit criteria
All acceptance criteria met; manuscript ready; package released and independently verified.

## Dependencies for next phase
Phase 15 needs the completed manuscript and submission package.
