# Phase 11 — External-Evaluation Freeze and Authorization

**Duration:** ~3 days · **Gate:** **E — the strictest gate in the project** · **Compute:** none

> Passed **exactly once**. Everything the paper claims about cross-institutional generalization depends on this gate being honest. A single earlier peek at external performance voids C4 outright.

## Scientific purpose
Freeze the entire method — code, weights, preprocessing, normalization, exclusions, splits, calibration, conformal procedure, operating points, metrics, and the statistical plan — so that external results cannot influence any of them. This converts external validation from a check into an **out-of-sample test** with pre-committed criteria.

## Engineering purpose
Generate and hash the freeze manifest; obtain the Research Lead signature; flip `GLIOMA_EXTERNAL_EVAL_AUTHORIZED`.

## Specification requirements satisfied
SPEC §4.5 (external cohorts held out completely; used once, at the end), §4.11 (tuning on the external test set kills the project), §9 step 8 and the closing "what should NOT be done yet" paragraph.

## RQs / claims addressed
Precondition for the external half of RQ1, RQ2, RQ3; **C3 and the external half of C4.**

## Entry criteria — every one must hold

1. Phases 00–10 complete; all prior gates passed.
2. **All internal results final.** No outstanding internal analysis.
3. Working tree clean; everything merged to `main`.
4. Leakage regression test passing on the final manifests.
5. **`UCSF-PDGM ∩ BraTS-2021 = ∅` verified and hashed** (Phase 03 T03.5).
6. **D-002, D-003, D-004 resolved and pre-registered** — conformal method, abstention definition, tolerance band all frozen before external data can speak.
7. Statistical analysis plan complete, including exact BH family membership.
8. External cohorts preprocessed through the identical frozen pipeline (operational access, Phase 04).
9. EGD status resolved — arrived, or the single-cohort contingency invoked and recorded.
10. **Research Lead has read and signed the freeze manifest.**

## Inputs
All frozen artifacts; the pre-registration; internal results; external cohorts (preprocessed, labels untouched).

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T11.1 | Verify every entry criterion; produce an evidence checklist | A | — | Claude | none | no | T11.2 |
| T11.2 | Generate the freeze manifest (15 fields) | A | — | Codex | none | no | T11.3 |
| T11.3 | Hash and commit the freeze manifest | A | — | Human | none | no | T11.4 |
| T11.4 | **Research Lead signature; log the authorization event** | A | — | Human | none | no | T11.5 |
| T11.5 | Flip `GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1` | A | — | Human | none | no | Phase 12 |
| T11.6 | Verify the firewall now permits exactly the intended paths and nothing more | A | — | Codex | none | no | Phase 12 |
| T11.7 | Independent pre-flight audit: could external results have leaked already? | C | A (+2d) **DEGRADED** | Claude | none | no | T11.4 |

**T11.7 is the hostile self-check**, and it is deliberately assigned to someone other than the person who wrote the code. Questions: has any external metric ever been computed, printed, logged, or plotted? Does any test fixture contain an external label? Was the pipeline ever "verified end-to-end" on external data? Did any checkpoint selection, threshold, or normalization statistic reference external results? Search git history and logs, not just memory. **A discovered peek is disclosed, not concealed** — an undisclosed peek found later by a reviewer is far more damaging than an admitted one.

**The freeze manifest — all fifteen fields:** code commit SHA (clean tree) · model checkpoints with SHA-256 · preprocessing configuration and version · normalization statistics file and hash · exclusion manifest and hash · UTSW split manifest and hash · calibration parameters (temperature, procedure) · conformal method, α grid, nonconformity score (**D-002**) · abstention definition (**D-003**) · operating points · missing-modality conditions · primary metrics · **C4 tolerance band** (**D-004**) · statistical analysis plan · authorizing signature and date.

## Human allocation
**A:** owns Gate E entirely — this authority is not delegable. **C:** independent pre-flight audit. **B:** none.

## Claude tasks
T11.1 (criterion verification), T11.7 (hostile audit).

## Codex tasks
T11.2 (manifest generation), T11.6 (firewall verification).

## Parallelization map
```
T11.1 ─> T11.2 ─> T11.3 ─┐
T11.7 (independent) ─────┴─> T11.4 ─> T11.5 ─> T11.6
```
Deliberately sequential. **Nothing here is parallelized for speed** — this gate is not a bottleneck worth optimizing.

## Worktrees / branches
```
agent/codex/p11-freeze-manifest
```
Minimal code changes. This phase is mostly verification and signature.

## Files / modules expected
`src/glioma_selective/evaluation/firewall.py` (**already exists from Phase 00**; verified here), `scripts/generate_freeze_manifest.py`, `artifacts/experiments/gate_e/freeze_manifest.json` + `.sha256`, `docs/research/protocols/GATE_E_LOG.md`.

## Data required
None read. External cohorts are already preprocessed and waiting.

## Compute required
None.

## Outputs / artifacts
Entry-criterion evidence checklist · **signed, hashed freeze manifest** · pre-flight audit report · dated authorization log entry · firewall verification report.

## Tests
`test_firewall.py`: raises by default with the flag at 0; raises when the flag is set but no valid freeze manifest exists; permits access when both hold; **CI runs with the flag at 0**, so any test that accidentally evaluates externally fails in CI.

## Quality gates
**GATE E.** No external performance access until it passes. Every entry criterion is evidenced, not asserted.

## Scientific validation
The freeze manifest's git SHA and hashes must be **verifiable after the fact** — anyone can check that the reported external results came from exactly the frozen method. The pre-registration hash must predate the first training commit, which is checkable from git history.

## Acceptance criteria
1. All ten entry criteria verified with evidence, not assertion.
2. Freeze manifest complete (15 fields), hashed, committed.
3. Research Lead signature recorded with a date.
4. Authorization event logged in `GATE_E_LOG.md`.
5. Pre-flight audit complete; any prior external exposure disclosed rather than concealed.
6. Firewall tested: raises before authorization, permits after, and permits **nothing beyond** the intended paths.
7. `GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1` set on the evaluation machine only.
8. Pre-registration hash provably predates the first training commit (verified from git history).
9. EGD status resolved and recorded.

## Failure conditions
Any entry criterion unmet → **the gate does not pass**; return to the outstanding phase · pre-flight audit finds prior external exposure → disclose in the decision log and the manuscript; assess whether C4 survives, and if it does not, **say so** · internal results not final → complete Phase 10 first.

## Rollback / recovery
**There is no rollback from Gate E.** Once external results are seen, they cannot be unseen. This is why the gate is sequential, evidenced, and signed. If a bug is found afterward, the correction is disclosed under the post-external change categories in `EXTERNAL_VALIDATION_PROTOCOL.md` §4 — the original result is retained alongside.

## Risks
**R-C03 (external peeking — the entire reason this gate exists)** · R-H01 (EGD absent → single-cohort contingency) · R-C09 (post-hoc manipulation — prevented by freezing before the flag flips).

## Decisions requiring Research Lead approval
**Everything in this phase.** Specifically: whether all entry criteria are genuinely met · whether to proceed with UCSF-PDGM alone if EGD has not arrived · the signature itself, which is a scientific commitment and not a formality.

## Exit criteria
Gate E passed; freeze manifest signed, hashed, and committed; authorization logged; firewall verified.

## Dependencies for next phase
Phase 12 cannot begin without the signed manifest and the flag set.
