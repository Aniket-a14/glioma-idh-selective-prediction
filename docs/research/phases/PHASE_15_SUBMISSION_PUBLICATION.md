# Phase 15 — Submission, Reviewer Revisions, and Publication

**Duration:** contingent (months) · **Gate:** F (maintained) · **Compute:** contingent

## Scientific purpose
Get the finding — positive, negative, or mixed — into the peer-reviewed record, with its pre-registered commitments intact through the review cycle.

## Engineering purpose
Maintain reproducibility through revisions; execute any legitimately requested additional analysis under governance that keeps it distinguishable from the pre-registered result.

## Specification requirements satisfied
SPEC §3.9 months 8–12 (writing, revision, reviewer-requested runs), §5.8 (reporting standards), §8.2 (reviewer objections anticipated and answered).

## RQs / claims addressed
All — defended.

## Entry criteria
Phase 14 complete; manuscript ready; package released.

## Inputs
Manuscript; submission package; frozen results; the anticipated-objection responses from SPEC §8.2.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T15.1 | Finalize venue; format to its requirements | A | — | Human | none | no | T15.2 |
| T15.2 | Assemble the submission package | A | — | Human | none | no | T15.3 |
| T15.3 | **Submit; tag the repository at the submission SHA** | A | — | Human | none | no | T15.4 |
| T15.4 | Reviewer-response cycle | A | — | Human+Claude | none | no | T15.5 |
| T15.5 | Additional analyses if legitimately requested (REVIEWER class) | A | — | Human | contingent | no | T15.6 |
| T15.6 | Revision and response letter | A+C | A (+7d) | Human+Claude | none | no | T15.7 |
| T15.7 | Camera-ready | A | — | Human | none | no | T15.8 |
| T15.8 | Code release at the publication tag | A | — | Codex | none | no | T15.9 |
| T15.9 | Archival DOI (Zenodo or equivalent) if terms permit | A | — | Human | none | no | Done |
| T15.10 | Final provenance audit: every published claim traces to a raw patient ID | A+C | A (+3d) | Claude | CPU | no | Done |

**T15.5 — REVIEWER-class governance.** Additional runs requested by reviewers are:
- labelled **post-hoc** in the manuscript,
- reported **separately** from the pre-registered primary result,
- **never** used to replace a pre-registered result that a reviewer found disappointing,
- recorded in the decision log with the request that prompted them.

If a reviewer asks for something that would compromise the pre-registration — refitting the conformal threshold on external data, say — the correct response is to **explain why it would invalidate C4**, not to comply. That explanation is itself a contribution to the review.

**Anticipated objections and prepared responses** (SPEC §8.2, to be adapted to the actual results):

| Objection | Response |
|---|---|
| *"Elyassirad et al. already did conformal IDH abstention externally."* | Single operating point; no risk–coverage sweep, no AURC, no missing-modality axis, no ECE/Brier. Our contribution is the systematic characterization on both failure axes jointly. |
| *"GMMAS already combines uncertainty, missing-modality, and calibration."* | Verified from full text: GMMAS's uncertainty gates training-time pseudo-label selection only. It never gates an inference-time prediction. No abstention, no risk–coverage, no coverage test. |
| *"Selective prediction under shift is mature; new-domain application isn't novel."* | The technique is mature; the domain-specific empirical finding is not — including the possibility that it fails here, which is actionable for anyone building a deployable glioma-genotyping tool. |
| *"Why not predict MGMT and 1p/19q too?"* | MGMT excluded on documented chance-level external evidence (Kim et al. 2022, 337/420 variants indistinguishable from chance). 1p/19q retained as explicitly exploratory given 63 positives. Adding either would weaken the paper. |
| *"Missingness is simulated, not real."* | Acknowledged in Limitations. All three cohorts are curated four-sequence by construction; naturally-missing cases are reported separately. The information-loss mechanism is simulated faithfully; the selection mechanism is not, and we say so. |

## Human allocation
**A:** owns submission and responses. **C:** response-letter support, checklist maintenance through revision. **D–F:** proofreading.

## Claude tasks
T15.4, T15.6 (drafting responses), T15.10 (provenance audit).

## Codex tasks
T15.8 (release packaging).

## Parallelization map
Largely sequential and externally paced by the venue.

## Files / modules expected
`paper/submission/`, `paper/response/`, `release/`, repository tags `submitted-vN`, `published`.

## Data required
None beyond frozen results, unless a reviewer legitimately requests new analysis.

## Compute required
None unless T15.5 requires it. Run R9 (the reserve) is available for exactly this.

## Outputs / artifacts
Submitted manuscript · reviewer responses · revised manuscript · camera-ready · released code at the publication tag · archival DOI · final provenance audit.

## Tests
Release: the published tag's package passes the acceptance test again — reviewers or readers may run it.

## Quality gates
Gate F maintained throughout. **Any post-submission change to a result requires re-verifying the provenance chain.**

## Scientific validation
Final audit (T15.10): every claim in the published paper traces through the provenance chain to a raw patient ID. This is the project's Definition of Done item 4 and item 11.

## Acceptance criteria
1. Manuscript submitted; submission SHA tagged.
2. Reviewer responses complete and evidence-based.
3. Any additional analysis run under REVIEWER governance, labelled post-hoc, reported separately.
4. **No pre-registered primary result replaced by a post-hoc one.**
5. Revision and camera-ready complete.
6. Code released at the publication tag; acceptance test passes.
7. Archival DOI obtained if terms permit.
8. Final provenance audit passes.
9. Negative results present in the published version, not removed during revision.

## Failure conditions
Rejection → revise and resubmit to the next venue; **the results do not change** · a reviewer request that would compromise the pre-registration → explain and decline, in writing · a provenance gap found late → resolve or retract the affected claim.

## Rollback / recovery
Results are frozen. Only writing changes. Every submission version is tagged.

## Risks
R-M04 (guideline updates during review) · R-M05 (a competitor publishing first — the empirical characterization retains value) · **the pressure to soften negative results during revision, which is the risk this whole plan's pre-registration machinery exists to resist.**

## Decisions requiring Research Lead approval
Venue changes after rejection · whether a reviewer request is legitimate or would compromise the pre-registration · whether to release prediction artifacts, subject to dataset terms · when to stop.

## Exit criteria
**Published** — or a documented decision to stop, with the reasoning recorded.

## Dependencies for next phase
None. **The project is complete** when the Definition of Done in `MASTER_RESEARCH_EXECUTION_PLAN.md` §28 is fully satisfied.
