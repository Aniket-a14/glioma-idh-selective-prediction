# Phase 08 — Missing-Modality Robustness

**Duration:** ~10 days · **Gate:** C · **Compute:** GPU (inference-heavy)

## Scientific purpose
Construct one of the two stressor axes the paper is about. **Channels are zeroed, never imputed** — imputation would conflate the missing-modality question with an imputation-quality question the study is not designed to answer (SPEC §4.4).

## Engineering purpose
Modality-dropout training and the systematic inference-time subset sweep, producing frozen predictions for all six modality conditions.

## Specification requirements satisfied
SPEC §4.2 (a dropped modality's channel is zeroed, not imputed), §4.4 (modality dropout in training; systematic evaluation of all clinically meaningful subsets, minimum each single drop plus "only T1CE+FLAIR"), §4.9 ablation axis 1.

## RQs / claims addressed
**RQ1 (missing-modality half); C2 directly.**

## Entry criteria
Phase 07 complete; all mechanisms working on complete-modality internal data.

## Inputs
R1–R6 checkpoints; all mechanism parameters; frozen split.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T08.1 | Modality-dropout training augmentation with a fixed probability schedule | A | — | Claude | CPU | no | T08.2 |
| T08.2 | Verify R2–R6 were trained with modality dropout; document the schedule | A | — | Human | none | no | T08.3 |
| T08.3 | Modality-mask machinery: zeroing, **never imputation** | A | — | Codex | CPU | no | T08.4 |
| T08.4 | Enumerate the six conditions as configs | A | — | Codex | none | no | T08.5 |
| T08.5 | Inference sweep: 6 conditions × 6 mechanisms, internal test | A | — | Human | GPU | no | Phase 09 |
| T08.6 | Freeze prediction artifacts per condition | A | — | Codex | GPU | no | Phase 09 |
| T08.7 | Naturally-missing-case sub-analysis (from **D-012**) | B | A (+2d) | Codex | CPU | yes | Phase 13 |
| T08.8 | Recalibrate conformal quantiles **per condition** on the calibration split | A | — | Claude | CPU | no | Phase 09 |

**The six conditions** (SPEC §4.4 minimum, frozen at Phase 05): `full` · `−T1` · `−T1CE` · `−T2` · `−FLAIR` · `T1CE+FLAIR only`.

**T08.8 is a genuine design question with a scientific answer.** Under a missing modality, should the conformal quantile be refitted on a calibration split with the same modality missing, or carried over from the complete-data calibration? These test different things: refitting asks *"does conformal work if you know what's missing?"*; carrying over asks *"what happens when the deployment condition differs from calibration?"* — which is closer to reality and closer to RQ2's exchangeability question. **Report both**, with the pre-registered primary being the carried-over variant, since it is the one that actually probes exchangeability violation.

**T08.3 hard constraint.** A zeroed channel is exactly zero after normalization — not the modality mean, not noise, not an imputed volume. A unit test asserts this, and the config schema has no imputation option to select.

## Human allocation
**A:** owns the sweep. **B:** naturally-missing sub-analysis. **C:** none.

## Claude tasks
T08.1 (dropout schedule design), T08.8 (the recalibration question — scientific judgement).

## Codex tasks
T08.3, T08.4, T08.6, T08.7 — bounded and testable.

## Parallelization map
```
T08.1 ─> T08.2 ─> T08.3 ─> T08.4 ─> T08.5 ─> T08.6
T08.8 ──────────────────────────────┘
T08.7 in parallel
```

## Worktrees / branches
```
agent/claude/p08-modality-dropout    agent/codex/p08-modality-conditions
```

## Files / modules expected
`src/glioma_selective/training/modality_dropout.py`, `src/glioma_selective/evaluation/modality_conditions.py`, `src/glioma_selective/data/masks.py`, `tests/unit/test_modality_masks.py`, `configs/evaluation/conditions/`.

## Data required
UTSW calibration + internal test. **No external data.**

## Compute required
GPU inference only — no new training. 6 conditions × 6 mechanisms over the internal test set, plus MC-dropout sampling and 5-member ensemble passes.

## Outputs / artifacts
Modality-dropout schedule documentation · **frozen prediction artifacts for all 6 internal conditions × 6 mechanisms** · per-condition conformal quantiles (both refit and carried-over) · naturally-missing sub-analysis.

## Tests
`test_modality_masks.py`: a zeroed channel is exactly 0.0 post-normalization; the mask matches the named condition; `full` leaves input unchanged; `T1CE+FLAIR only` zeroes exactly T1 and T2; **no code path performs imputation** (asserted by absence of any imputation entry point); the model forward pass accepts every mask without shape error.
Dropout: the schedule produces the configured probability over many samples; at least one channel always survives (never all four zeroed).

## Quality gates
Gate C for the sweep. Gate B for merges.

## Scientific validation
Performance must degrade as modalities are removed, and the degradation ordering should be clinically plausible — losing T1CE (the contrast sequence carrying most enhancement information for glioma genotyping) is expected to hurt more than losing T1. **If it does not, suspect a channel mis-mapping** (R-C05), which would have survived from Phase 03 and is exactly the kind of error that produces plausible-but-wrong results.

## Acceptance criteria
1. Modality dropout confirmed active in R2–R6 with the schedule documented.
2. All six conditions implemented; masks unit-tested.
3. **Zeroing verified; no imputation path exists anywhere in the codebase.**
4. Full sweep complete: 6 conditions × 6 mechanisms on the internal test set.
5. Prediction artifacts frozen per condition with run ID, git SHA, and checkpoint hash.
6. Per-condition conformal quantiles computed both ways (refit and carried-over) and recorded.
7. Degradation ordering is clinically plausible, or an investigation is documented.
8. Naturally-missing cases analysed separately and flagged (**D-012**, **D-008**).

## Failure conditions
Performance does not degrade with modality removal → the model may be ignoring channels; investigate before proceeding · degradation ordering implausible → suspect channel mapping; return to Phase 03 · all-four-zeroed samples appear in training → schedule bug.

## Rollback / recovery
Inference-only; any condition can be recomputed from the frozen checkpoints at modest GPU cost.

## Risks
**R-C05 (modality mapping — this phase is the last natural place to catch it)** · **D-008** (simulated missingness — a reporting obligation, recorded here and carried to Phase 14).

## Decisions requiring Research Lead approval
Modality-dropout probability schedule · whether to add conditions beyond the SPEC §4.4 minimum (**recommendation: no** — six is enough and more invites scope creep) · which recalibration variant is primary (**recommendation: carried-over**).

## Exit criteria
All acceptance criteria met; Gate C satisfied; artifacts frozen for all 6 internal conditions.

## Dependencies for next phase
Phase 09 needs frozen predictions for all internal conditions and mechanisms.
