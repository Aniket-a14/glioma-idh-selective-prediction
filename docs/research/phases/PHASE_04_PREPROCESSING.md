# Phase 04 — Preprocessing Pipeline and MRI Quality Control

**Duration:** ~12 days (mostly overnight CPU) · **Gate:** D · **Compute:** CPU

> **D-026 (2026-09-19):** the UTSW and UCSF-PDGM downloads are already skull-stripped, co-registered and on a common 240×240×155, 1 mm grid, so T04.2, T04.3 and T04.5 run there as *verification* (`verified-passthrough`), not as transformations. The stages are still built and tested for failing cases and for EGD. See `DECISION_LOG.md` D-026.

## Scientific purpose
Produce co-registered, skull-stripped, bias-corrected, resampled, normalized volumes on a common footing across three cohorts — without leaking test or external distribution information into the normalization, and without silently accepting preprocessing failures that a loss curve would never reveal.

## Engineering purpose
A resumable, content-addressed, version-aware pipeline with per-case status tracking and a real visual QC step.

## Specification requirements satisfied
SPEC §3.3 (CPU-bound, overnight), §4.2 (four co-registered skull-stripped normalized volumes, 96³/128³ crops), §5.6 (rigid co-registration, HD-BET, N4, ~1 mm isotropic, **z-score from training-split statistics only**).

## RQs / claims addressed
Precondition for all. Preprocessing leakage would invalidate RQ2 and RQ3 specifically, since both compare distributions across cohorts.

## Entry criteria
Phase 03 complete; cohort manifest frozen and hashed. Tool choices fixed by D-024 (within-patient T1CE registration, HD-BET pinned release); split/normalization ordering fixed by D-023.

## Inputs
Raw cohorts; cohort manifest; exclusion manifest.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T04.1 | Volume discovery + sequence identification (extends Phase 02 adapters) | A | — | Codex | CPU | no | T04.2 |
| T04.2 | Rigid inter-sequence co-registration | A | — | Codex | CPU | no | T04.3 |
| T04.3 | Skull stripping (HD-BET) | A | — | Codex | CPU/GPU | no | T04.4 |
| T04.4 | N4 bias-field correction | A | — | Codex | CPU | no | T04.5 |
| T04.5 | Resample to ~1 mm isotropic; common orientation | A | — | Codex | CPU | no | T04.7, T04.8 |
| T04.6 | **Normalization statistics from UTSW-train ONLY**; apply everywhere unchanged. **Runs after Phase 05 T05.3 (split freeze), per D-023.** | A | — | Claude | CPU | no | Phase 06 |
| T04.7 | Segmentation-mask handling and alignment | A | — | Codex | CPU | yes | Phase 06 |
| T04.8 | Automated QC: shape, range, orientation, alignment, mask overlap | A | — | Codex | CPU | no | T04.9 |
| T04.9 | **Visual QC on a representative sample** | B | A (+8d) **DEGRADED** | Human | none | no | Gate D |
| T04.10 | Resumability + content-addressed caching by parameter hash | A | — | Codex | CPU | yes | — |
| T04.11 | Per-case status manifest; failure categorization | A | — | Codex | CPU | no | T04.12 |
| T04.12 | QC-failure exclusions appended to the exclusion manifest | A | — | Codex | CPU | no | Phase 05 |

**T04.6 is a leakage control, not a preprocessing convenience.** Ordering per D-023: it runs after the Phase 05 split is frozen on the post-QC roster. Per-modality z-score statistics are computed **exclusively** from the UTSW training split and applied unchanged to calibration, internal test, UCSF-PDGM, and EGD. Computing them on pooled data — or per-cohort — would leak external distribution information into the model's effective input space and silently invalidate the domain-shift evaluation that is the paper's point. The CLI refuses any other fitting cohort; a unit test asserts provenance; the statistics file is hashed and frozen at Phase 05.

**T04.9 cannot be replaced by "the command exited 0."** SPEC-adjacent reality: registration can converge to a wrong transform, skull-stripping can remove tumour, N4 can amplify artifact, and a mis-mapped channel trains perfectly well. Define in advance:

| Element | Specification |
|---|---|
| Sample | ≥30 patients, stratified by cohort and IDH status; plus **every** automated-QC borderline case |
| Overlays | Each modality against T1CE; segmentation mask over FLAIR; skull-strip boundary over the original |
| Expected orientation | RAS, recorded and asserted |
| Shape/range | Post-resample shape consistent; intensity within expected z-score bounds |
| Alignment | Visual cross-modality registration check at three anatomical landmarks |
| Failure categories | `registration-failed`, `skullstrip-over` (brain removed), `skullstrip-under` (skull retained), `n4-artifact`, `orientation-wrong`, `corrupt`, `modality-mislabelled` |
| Exclude vs. correct | Systematic (a parameter) → correct and re-run. Individual → exclude with a `qc:*` reason. |

## Human allocation
**B:** owns visual QC — the single most valuable non-automatable contribution in the project. **A:** pipeline design, normalization control, exclusion decisions. **C:** none. **D–F:** may perform a second-reader QC pass on a subset (non-critical-path, but valuable).

## Claude tasks
T04.6 (normalization leakage control — high scientific risk, cross-cutting).

## Codex tasks
T04.1–T04.5, T04.7, T04.8, T04.10, T04.11, T04.12 — each a bounded, individually testable pipeline stage.

## Parallelization map
```
T04.1 ─> T04.2 ─> T04.3 ─> T04.4 ─> T04.5 ─> T04.8 ─> T04.9 ─> T04.11 ─> T04.12 ─> [Phase 05 T05.1–T05.3] ─> T04.6
T04.7  ──────────────────────────────────┘
(D-023: T04.6 fits on the frozen UTSW-train split, so it follows the Phase 05 split freeze. The T04.8 z-score range check runs after T04.6; every other T04.8 check runs before.)
T04.10 in parallel throughout
```
Pipeline stages are sequential per case but **embarrassingly parallel across patients** — run as a batch overnight.

## Worktrees / branches
```
agent/codex/p04-registration      agent/codex/p04-skullstrip-n4
agent/codex/p04-resample-qc       agent/claude/p04-normalization
```

## Files / modules expected
`src/glioma_selective/preprocessing/{discovery,registration,skullstrip,n4,resample,normalize,masks,qc,cache}.py`, `scripts/run_preprocessing.py`, `tests/unit/test_normalization.py`, `tests/integration/test_preprocessing_pipeline.py`, `data/processed/`, `data/manifests/{normalization_stats,preprocessing_status}.json`, `artifacts/figures/qc/`.

## Data required
All included patients from the cohort manifest. **UCSF-PDGM and EGD are preprocessed here — this is operational access and explicitly permitted** (`EXTERNAL_VALIDATION_PROTOCOL.md` §1). Their labels are not touched.

## Compute required
CPU-bound; overnight batch for the full cohort (SPEC §3.3). HD-BET may use GPU if available, which shortens but does not change the plan.

## Outputs / artifacts
Preprocessed volumes, content-addressed by parameter hash · **normalization statistics (UTSW-train derived), hashed** · per-case status manifest · QC overlay figures · QC report with failure categorization · QC-based exclusions appended to the exclusion manifest.

## Tests
`test_normalization.py`: statistics computed from the training split only (asserted by provenance); applying to a held-out split does not recompute; the CLI refuses a non-UTSW-train fitting cohort; z-scored training data has mean≈0, std≈1 per modality.
Pipeline: a synthetic volume with known properties survives each stage with expected geometry; resample produces the target spacing; registration of a volume with itself is the identity; orientation is RAS after the pipeline; the cache returns identical output for identical parameters and recomputes on a parameter change.

## Quality gates
Gate D. **Visual QC sign-off is a hard requirement** — the phase cannot exit on automated checks alone.

## Scientific validation
Visual QC by a human on ≥30 stratified cases plus all borderline cases. Automated QC agreement with human judgement measured on the reviewed sample — if automated QC misses failures the human catches, the automated thresholds are recalibrated before the full run is trusted.

## Acceptance criteria
1. All included patients preprocessed, or excluded with a categorized `qc:*` reason.
2. Normalization statistics derived from UTSW-train alone, hashed, committed; provenance test passing.
3. Visual QC completed on ≥30 stratified cases plus every borderline case; overlays archived.
4. QC failure rate recorded per cohort; systematic failures corrected and re-run rather than excluded.
5. All volumes RAS-oriented at the target spacing with consistent shape; asserted automatically.
6. Segmentation masks aligned with their volumes (visual + Dice-with-self sanity check).
7. Pipeline is resumable: interrupt mid-run, restart, and only missing cases recompute.
8. Content-addressed cache verified — identical parameters reuse, changed parameters recompute.
9. Post-QC cohort counts recorded and fed to Phase 05.

## Failure conditions
QC failure rate > 10% in any cohort → investigate systematically before proceeding · normalization statistics fitted on anything but UTSW-train → **stop, recompute, re-preprocess** · modality mislabelling found during QC → return to Phase 03 adapter mapping · post-QC counts fall below the Phase 05 power threshold.

## Rollback / recovery
Content-addressed caching makes re-running a stage with corrected parameters cheap — only affected cases recompute. Raw data is untouched, so any error is fully recoverable.

## Risks
**R-C04 (normalization leakage — the critical risk of this phase)** · R-C05 (modality mapping, final chance to catch it) · R-H06 (pipeline failure) · R-M02 (if B is unavailable, visual QC is DEGRADED and must be disclosed).

## Decisions requiring Research Lead approval
Registration target, skull-stripping tool and version, and QC exclusion threshold are resolved (D-024). Whether a systematic failure warrants re-running the entire cohort is decided only if QC finds one.

## Exit criteria
All acceptance criteria met; Gate D passed; visual QC signed off. Normalization statistics are frozen and hashed by T04.6 after the Phase 05 split freeze (D-023), so the phase closes when that has happened.

## Dependencies for next phase
Phase 05 needs post-QC cohort counts (D-023: not the normalization statistics; those follow the split freeze). Phase 06 needs the frozen split and the frozen normalization statistics.
