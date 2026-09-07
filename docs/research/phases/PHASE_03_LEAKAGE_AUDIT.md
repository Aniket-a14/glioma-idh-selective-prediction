# Phase 03 — Metadata Verification and Patient-Level Overlap / Leakage Audit

**Duration:** ~7 days · **Gate:** D · **Compute:** CPU

> The highest-risk phase in the project. SPEC §4.11 names patient-level leakage and invalid external validation as the two things that "will kill this project." Everything here exists to prevent them.

## Scientific purpose
Establish, with evidence rather than assumption, exactly which patients exist, what their labels are, and which patients appear in more than one cohort. Until this phase completes, **no count in the specification may be trusted** (SPEC §9 step 1 says so explicitly) and no split may be computed.

## Engineering purpose
Build the ID-normalization, overlap-detection, and exclusion-manifest machinery, and produce the first hashed, versioned manifests.

## Specification requirements satisfied
SPEC §2.1 and §2.3 (UCSF-PDGM BraTS overlap must be resolved), §5.1 (patient-level splitting mandatory; quantifies the leakage problem), §5.4 (ambiguous labels excluded not imputed), §5.7 (label-definition harmonization), §9 step 1–2 (verify counts from files; build a versioned exclusion list before modeling).

## RQs / claims addressed
Precondition for all. **C3 in particular is void without a clean external cohort.**

## Entry criteria
Phase 02 acceptance criteria met for UTSW and UCSF-PDGM; BraTS-2021 ID-mapping file in hand.

## Inputs
Raw cohorts; clinical-metadata files; UCSF-PDGM/BraTS-2021 ID map; BraTS-2021, TCGA-GBM, TCGA-LGG subject-ID lists.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T03.1 | ID normalization: case, padding, prefixes, separators — per cohort | A | — | Codex | CPU | no | T03.4 |
| T03.2 | **Parse clinical metadata; count IDH / 1p19q per cohort from files** (**D-009**) | B | A+Codex (+3d) | Codex | CPU | yes | T03.3 |
| T03.3 | SPEC-claimed vs. file-verified count table; explain every discrepancy | B | A (+2d) | Claude | CPU | no | Phase 05 |
| T03.4 | **Full overlap matrix** — every cell, including expected-empty | B | A+Codex (+5d) | Codex | CPU | no | T03.5 |
| T03.5 | **UCSF-PDGM ⇄ BraTS-2021 exclusion via the shipped ID map** | A | — | Codex | CPU | no | Phase 11 |
| T03.6 | Label-definition harmonization across cohorts (**SPEC §5.7**) | B | A (+3d) **DEGRADED** | Claude | none | yes | T03.7 |
| T03.7 | Ambiguous / conflicting labels: exclude, count, document | B | A (+2d) | Human+Claude | CPU | no | Phase 05 |
| T03.8 | Duplicate-scan detection within cohorts; retention rule | B | A+Codex (+2d) | Codex | CPU | yes | T03.9 |
| T03.9 | Naturally-missing sequence inventory (**D-012**) | B | A+Codex (+1d) | Codex | CPU | yes | Phase 05 |
| T03.10 | Exclusion manifest with a machine-readable reason per patient | A | — | Codex | CPU | no | Phase 05 |
| T03.11 | Final cohort manifest, SHA-256, committed | A | — | Codex | CPU | no | Phase 05 |
| T03.12 | **Leakage regression test** wired into CI | A | — | Codex | CPU | no | all |

**T03.4 — the overlap matrix.** Every cell computed and recorded even when empty; "we checked and found nothing" must be evidenced, not assumed:

```
                BraTS-2021   TCGA-GBM   TCGA-LGG   UCSF-PDGM   EGD
UTSW-Glioma         ?            ?          ?          ?         ?
UCSF-PDGM     MUST RESOLVE       ?          ?          —         ?
EGD                 ?            ?          ?          ?         —
```

**T03.6 is judgement work and degrades under solo operation.** IDH must be defined identically across cohorts (IDH1/IDH2 by sequencing or an established IHC+sequencing algorithm, WHO 2021) before any statistic is pooled. Cohort-specific assay or era differences — older cases assessed under pre-2021 criteria — are **flagged as label heterogeneity, not normalized away.** If executed solo, this is disclosed in Limitations.

## Human allocation
**B:** owns the audit — metadata verification, patient-ID auditing, exclusion verification. This is B's most important contribution to the project. **A:** ID normalization design, exclusion policy, final sign-off, all manifest freezing. **C:** independent re-check of the count table (T03.3).

## Claude tasks
T03.3 (discrepancy reasoning), T03.6 (label harmonization — cross-cohort scientific judgement), T03.7 (ambiguous-label policy).

## Codex tasks
T03.1, T03.2, T03.4, T03.5, T03.8, T03.9, T03.10, T03.11, T03.12 — all bounded and testable. **T03.4 and T03.5 receive mandatory joint Claude review** given their scientific risk.

## Parallelization map
```
T03.1 ─> T03.4 ─> T03.5 ─┐
T03.2 ─> T03.3 ──────────┤
T03.6 ─> T03.7 ──────────┼─> T03.10 ─> T03.11 ─> T03.12 ─> Gate D
T03.8, T03.9 ────────────┘
```

## Worktrees / branches
```
agent/codex/p03-id-normalization    agent/codex/p03-overlap-audit
agent/codex/p03-manifests           agent/claude/p03-label-harmonization
```
`leakage/` and `splits/` are Codex-implemented but **Claude-reviewed** — the one place where joint review is mandatory rather than optional.

## Files / modules expected
`src/glioma_selective/leakage/{id_normalization,overlap_audit,exclusions}.py`, `src/glioma_selective/data/metadata.py`, `tests/regression/test_leakage.py`, `data/manifests/{cohort_manifest,exclusions_*,label_verification}.json`, `docs/research/protocols/LABEL_DEFINITIONS.md`.

## Data required
UTSW + UCSF-PDGM raw and metadata. EGD if it has arrived; otherwise it is audited separately on arrival.

## Compute required
CPU only.

## Outputs / artifacts
Verified label-count table (SPEC-claimed vs. file-verified) · complete overlap matrix · UCSF-PDGM exclusion list post-BraTS-dedup · exclusion manifest with reasons · **final cohort manifest, hashed** · label-definition document · naturally-missing inventory · passing leakage regression test in CI.

## Tests
`test_leakage.py` (**the most important test in the repository**, runs on every commit, never skipped): no patient ID in two splits; no excluded ID in any split; `UTSW ∩ UCSF = ∅`; `UTSW ∩ EGD = ∅`; `UCSF ∩ BraTS-2021 = ∅` post-exclusion; every split ID exists in the cohort manifest; manifest hashes match recorded values.
ID normalization: known-tricky cases (leading zeros, mixed case, prefix variants) map correctly; normalization is idempotent; two different patients never collide.

## Quality gates
Gate D. Manifest hashes committed. **Gate B blocks on the leakage regression test from this point forward, permanently.**

## Scientific validation
1. Independent re-derivation of label counts by C (or by Codex from the raw files, under solo fallback) — must match B's.
2. Manual spot-check of ≥20 overlap-matrix decisions against the raw ID strings.
3. Every count discrepancy versus the specification explained in writing, not waved through.

## Acceptance criteria
1. Label counts verified from files for every cohort and marker; the SPEC-vs-verified table has an explanation for **every** discrepancy — including the specification's own 625-patients-vs-622-IDH-labels gap.
2. Overlap matrix complete; every cell has a recorded result.
3. `UCSF-PDGM ∩ BraTS-2021 = ∅` after exclusion, verified and hashed.
4. Exclusion manifest carries a machine-readable reason for every excluded patient.
5. Ambiguous labels excluded (never imputed) and counted.
6. Label definitions documented per cohort; heterogeneity flagged.
7. Naturally-missing sequence inventory complete (feeds **D-012**).
8. Cohort manifest hashed and committed.
9. Leakage regression test passing in CI and demonstrably failing on planted leakage.
10. Post-exclusion class counts recorded for IDH and 1p/19q — **input to the Phase 05 power check.**

## Failure conditions
**Any UTSW ∩ external overlap** → those patients are excluded from UTSW (never from the external set — the external set must stay intact to remain representative) · IDH counts materially below specification → Phase 05 power check may force a design change · 1p/19q positives far below 63 → **D-007** revisited, RQ4 possibly demoted to descriptive or dropped · label definitions irreconcilable → cohort-stratified reporting instead of pooling.

## Rollback / recovery
Manifests are versioned; a corrected audit produces v2 with a decision-log entry. **Because no split or training exists yet, correcting an error here is cheap — which is exactly why this phase precedes everything.**

## Risks
**R-C01, R-C02, R-C07** (all critical, all owned here) · R-H03 (insufficient class counts) · R-C05 (modality mapping, continued from Phase 02).

## Decisions requiring Research Lead approval
Duplicate-scan retention rule (earliest? highest quality? pre-operative only?) · ambiguous-label exclusion boundary · **D-012** naturally-missing inclusion rule · whether any label-definition mismatch warrants cohort exclusion rather than case exclusion · handling of the 3 UTSW patients without IDH labels.

## Exit criteria
All acceptance criteria met; Gate D passed; manifests hashed and committed; **D-009 and D-012 resolved** and recorded.

## Dependencies for next phase
Phase 04 needs the final cohort manifest so preprocessing runs only on included patients. Phase 05 needs post-exclusion class counts for the power check.
