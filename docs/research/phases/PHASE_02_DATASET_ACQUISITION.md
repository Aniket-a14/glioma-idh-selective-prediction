# Phase 02 — Dataset Acquisition and Access

**Duration:** ~5 days active; **EGD DUA runs 4–8 weeks underneath everything** · **Gate:** D · **Compute:** none (network-bound)

> **DAY-1 ACTION: submit the EGD data-use agreement.** It is the longest-latency item in the entire project and the only dependency that cannot be compressed by working harder. Everything else in this phase can wait a day; this cannot.

## Scientific purpose
Obtain the cohorts under terms that permit the planned use, with verifiable integrity, so that every downstream number traces to a specific, dated, checksummed download.

## Engineering purpose
Populate `data/raw/` and `data/external/`; establish the access log; verify integrity before any preprocessing consumes a corrupted volume.

## Specification requirements satisfied
SPEC §2.2 (UTSW primary), §2.3 (UCSF-PDGM and EGD external), §2.7 (access mechanisms and lead times), §9 step 1 (acquire and independently verify).

## RQs / claims addressed
None directly. Supplies the data for all.

## Entry criteria
Phase 01 T01.2 complete (SSD tree exists with sufficient space). Phase 00 need not be finished — **the EGD DUA submission does not wait on anything.**

## Inputs
TCIA access; Health-RI contact (`servicedesk@health-ri.nl`); institutional details for the DUA.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| **T02.1** | **Submit EGD DUA via Health-RI — DAY 1** | B | A (+0d) | Human | none | yes | Phase 11 |
| T02.2 | Weekly EGD status check, logged | B | A (+0d) | Human | none | yes | — |
| T02.3 | Download UTSW-Glioma from TCIA (DOI 10.7937/dfae-1b86) | B | A (+2d) | Human | network | yes | Phase 03 |
| T02.4 | Download UCSF-PDGM from TCIA | B | A (+2d) | Human | network | yes | Phase 03 |
| T02.5 | Obtain the UCSF-PDGM ⇄ BraTS-2021 ID-mapping file | B | A (+1d) | Human | network | yes | **Phase 03** |
| T02.6 | Integrity verification: checksums, file counts, per-patient sequence inventory | B | A+Codex (+2d) | Codex | CPU | no | Phase 03 |
| T02.7 | Record licence/DUA terms per cohort — what each permits, incl. transfer to the GPU server | B | A (+1d) | Human | none | yes | Phase 06 |
| T02.8 | `data/adapters/` skeletons: file discovery + sequence identification per cohort | A | — | Codex | CPU | yes | Phase 03 |
| T02.9 | Populate `DATA_ACCESS_LOG.md` | B | A (+1d) | Human | none | no | Gate D |

**T02.5 is not optional and not deferrable.** UCSF-PDGM ships this file *specifically* because a subset of its cases is also in BraTS-2021. Without it, Phase 03 cannot resolve R-C02 and UCSF-PDGM cannot be called external.

**T02.7 matters before any data moves.** EGD is DUA-governed. Its terms must be read and recorded *before* EGD touches a second machine — casually rsyncing DUA-governed data to a GPU server is a compliance breach, not merely untidy.

## Human allocation
**B:** owns acquisition, verification, and the access log — this is the phase B exists for. **A:** adapters, oversight, DUA counter-signature. **C:** none. **D–F:** may assist with download monitoring (non-critical-path).

## Claude tasks
None substantive. Reviews the access log for completeness against the governance protocol.

## Codex tasks
T02.6 (integrity verification tooling), T02.8 (cohort adapter skeletons — bounded, per-cohort, testable).

## Parallelization map
```
T02.1 (DAY 1) ────────────────────────────────> [4–8 weeks external latency] ──> Phase 11
T02.2 weekly ────────────────────────────────────────────────────────────────>
T02.3 ─┬─> T02.6 ─> T02.9 ─> Gate D
T02.4 ─┤
T02.5 ─┘
T02.7, T02.8 in parallel
```
UTSW and UCSF downloads run concurrently. **Nothing waits on EGD.**

## Worktrees / branches
```
agent/codex/p02-integrity-verification
agent/codex/p02-cohort-adapters
```

## Files / modules expected
`src/glioma_selective/data/adapters/{utsw,ucsf_pdgm,egd}.py`, `scripts/verify_download_integrity.py`, `docs/research/protocols/DATA_ACCESS_LOG.md`, `data/raw/{utsw}/`, `data/external/{ucsf_pdgm}/` (on SSD, not in Git).

## Data required
This phase *produces* the data. Storage: SPEC §3.2 estimates tens to ~150 GB raw.

## Compute required
None. Network- and IO-bound.

## Outputs / artifacts
Raw cohorts on the SSD, read-only after verification · integrity report (checksums, counts, per-patient sequence inventory) · UCSF-PDGM/BraTS-2021 ID-mapping file · licence and DUA terms record · dated access log · EGD DUA submission receipt.

## Tests
Adapter tests: file discovery returns the expected patient count; sequence identification maps correctly on a hand-labelled sample of ≥10 patients per cohort. Integrity: verification detects a deliberately truncated file.

## Quality gates
Gate D at phase end. **No Gate E implications** — downloading external data is *operational* access and explicitly permitted (`EXTERNAL_VALIDATION_PROTOCOL.md` §1).

## Scientific validation
The per-patient sequence inventory is compared against the specification's claimed cohort structure. Discrepancies are recorded, not reconciled by assumption. **No label counting or label-file parsing happens here** — that is Phase 03, deliberately separated so that acquisition and verification are distinct auditable steps.

## Acceptance criteria
1. **EGD DUA submitted, with a dated receipt in the access log.** (This alone is the phase's most important output.)
2. UTSW-Glioma downloaded; file count and per-patient sequence inventory recorded.
3. UCSF-PDGM downloaded; same.
4. UCSF-PDGM ⇄ BraTS-2021 ID-mapping file obtained and hashed.
5. Integrity verification passes, or every failure is recorded with a disposition.
6. Licence/DUA terms recorded per cohort, explicitly stating whether transfer to the GPU server is permitted.
7. `DATA_ACCESS_LOG.md` complete for every acquired cohort: version, download date, method, checksum, inventory, terms, operator.
8. Adapters discover files and identify sequences correctly on a hand-labelled sample.
9. `data/raw/` is not tracked by Git (`git status` clean).

## Failure conditions
EGD DUA refused or unanswered by week 6 → escalate, then invoke the single-external-cohort contingency · TCIA download corrupted beyond re-download · a cohort's terms prohibit the planned use (would require a specification-level rethink) · sequence identification ambiguous for a large fraction of patients.

## Rollback / recovery
Downloads are re-runnable. Raw data is never modified in place, so a corrupted download is discarded and re-fetched rather than repaired.

## Risks
**R-H01 (EGD delay — the dominant risk of this phase)**, R-H02 (corrupted downloads), R-C05 (wrong modality mapping — begins here with sequence identification), R-C02 (needs T02.5).

## Decisions requiring Research Lead approval
Whether to acquire the optional supplementary cohorts (LGG-1p19qDeletion, UPENN-GBM) — **recommendation: not now**, they add scope without serving RQ1–RQ3 · whether any cohort may be copied to the GPU server, per its recorded terms.

## Exit criteria
All acceptance criteria met; Gate D passed; access log committed and reviewed by A.

## Dependencies for next phase
Phase 03 needs UTSW + UCSF-PDGM downloaded and verified, plus the BraTS ID-mapping file. **Phase 03 does not wait for EGD** — EGD joins the audit whenever it arrives, and if it arrives after Phase 05 it gets its own audit and freeze.
