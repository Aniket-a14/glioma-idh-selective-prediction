# Phase 06 — Baseline 3D Model (Always-Predict, Uncalibrated)

**Duration:** ~14 days · **Gate:** C · **Compute:** GPU

## Scientific purpose
Establish that the frozen backbone reaches a sane internal AUROC before any trust machinery is added (SPEC §9 step 4). If the base classifier does not discriminate, selective prediction has nothing to select over, and every downstream claim is uninterpretable.

## Engineering purpose
Implement the specified architecture, the training loop, checkpointing and resume, and the seven-step pre-training authorization harness.

## Specification requirements satisfied
SPEC §4.1 (3D SegResNet-style MONAI encoder; **not** a bespoke transformer), §4.2 (four-channel input, 96³/128³ crops, scalar IDH probability), §4.3 (auxiliary segmentation head, tumour-aware pooling — confirmatory), §4.8 baselines 1 and 5, §5.4 (class-balanced loss, PR-AUC alongside ROC-AUC).

## RQs / claims addressed
Supplies the always-predict baseline against which C1, C2, and C3 are all measured. M1 and M6 originate here.

## Entry criteria
Phase 05 freeze complete; Phase 04 T04.6 complete (normalization statistics fitted on the frozen split and hashed, D-023); Phase 01 environment and benchmark complete; **all seven pre-training authorization steps must pass before any expensive run.**

## Inputs
Frozen split; frozen normalization statistics; preprocessed volumes; GPU benchmark table.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T06.1 | Model interface: 4-channel input, classification head, optional aux seg head | A | — | Claude | CPU | no | T06.2 |
| T06.2 | SegResNet-style encoder (MONAI), ~10–30M params | A | — | Claude | CPU | no | T06.3 |
| T06.3 | Tumour-aware pooling through the auxiliary mask | A | — | Claude | CPU | no | T06.4 |
| T06.4 | Losses: class-balanced classification + auxiliary Dice | A | — | Claude | CPU | no | T06.6 |
| T06.5 | Reproducible dataloading; online augmentation (**never persisted**) | A | — | Codex | CPU | yes | T06.6 |
| T06.6 | Training loop: AMP, grad accumulation, checkpointing, early stopping | A | — | Claude | GPU | no | T06.8 |
| T06.7 | Run-record integration (the 20 fields) | A | — | Codex | CPU | yes | T06.8 |
| T06.8 | **Seven-step authorization harness** | A | — | Codex | GPU | no | T06.9 |
| T06.9 | Pilot run; hyperparameter sizing on the training split only | A | — | Human | GPU | no | T06.10 |
| T06.10 | **R1 + R2 final internal runs** | A | — | Human | GPU | no | Phase 07 |
| T06.11 | Freeze prediction artifacts for the internal test set | A | — | Codex | GPU | no | Phase 07 |
| T06.12 | Resolve **D-006** (comparator scope) and **D-011** (BraTS pretraining) | A | — | Claude | none | yes | Phase 09 |

**T06.8 — the seven steps, in order, all required:** CPU unit tests → one-sample data test → tiny-batch forward pass → tiny overfit test (loss → ~0 on 4 patients) → GPU memory test at the target patch size → checkpoint save/resume equivalence → deterministic/config logging. **Only then is an expensive run authorized.** The tiny overfit test is the highest-value of the seven: a model that cannot overfit four patients has a bug that no amount of training will fix.

**Model selection uses the UTSW calibration split only.** Early stopping, checkpoint choice, and any hyperparameter decision reference internal data exclusively. This is SI-08 and it is not negotiable.

## Human allocation
**A:** owns the model and all runs. **B:** none. **C:** independent verification of the reported internal AUROC from the frozen prediction artifacts.

## Claude tasks
T06.1–T06.4, T06.6, T06.12 — architecture and training-loop design, high-context, cross-module.

## Codex tasks
T06.5, T06.7, T06.8, T06.11 — bounded infrastructure with clear pass/fail criteria.

## Parallelization map
```
T06.1 ─> T06.2 ─> T06.3 ─> T06.4 ─┐
T06.5, T06.7 (Codex, parallel) ───┼─> T06.6 ─> T06.8 ─> T06.9 ─> T06.10 ─> T06.11
T06.12 in parallel ───────────────┘
```

## Worktrees / branches
```
agent/claude/p06-model-architecture   agent/claude/p06-training-loop
agent/codex/p06-dataloading           agent/codex/p06-authorization-harness
```

## Files / modules expected
`src/glioma_selective/models/{segresnet,heads,pooling}.py`, `src/glioma_selective/training/{loop,checkpoint,losses,augment}.py`, `src/glioma_selective/tracking/run_record.py`, `scripts/{authorize_training,train}.py`, `tests/unit/test_model_shapes.py`, `tests/integration/test_tiny_overfit.py`, `configs/model/`, `configs/training/`.

## Data required
UTSW train + calibration + internal test. **No external data.**

## Compute required
GPU. Per SPEC §3.4, 1–3 days per major run. This phase produces R1 and R2 of the nine-run budget.

## Outputs / artifacts
Trained checkpoints R1 (no modality dropout) and R2 (primary model) with hashes · run records · training histories · **frozen prediction artifacts on the internal test set** · GPU memory profile · authorization-harness report.

## Tests
Model: output shapes for batch × 4 channels × {96³,128³}; parameter count within 10–30M; forward works with a zeroed channel; tumour-aware pooling reduces to global pooling when the mask is all-ones.
Training: tiny overfit reaches near-zero loss on 4 patients; **checkpoint save→load→forward is numerically identical**; resume from mid-epoch continues correctly; AMP does not change results beyond tolerance; augmentation is deterministic under a fixed seed.

## Quality gates
**Gate C before every run:** clean tree, valid config, frozen manifest hashes, environment recorded, smoke test passed, storage available, checkpoint path valid. Gate B for merges.

## Scientific validation
Internal AUROC compared against the literature range for MRI-based IDH classification (SPEC §6 reports 0.90+ internally for comparable systems). A materially lower value triggers investigation *before* proceeding — not architecture search, but a check for pipeline bugs, label mismatch, or channel mis-mapping. **A materially higher value is equally suspicious** and triggers a leakage re-check.

## Acceptance criteria
1. All seven authorization steps pass and are recorded.
2. Model parameter count within 10–30M (SPEC §3.4).
3. Tiny overfit test reaches near-zero loss on 4 patients.
4. Checkpoint save/resume is numerically identical.
5. R1 and R2 trained to convergence with early stopping on the **calibration split only**.
6. Internal test AUROC is "sane" — defined concretely as **AUROC ≥ 0.75 with a bootstrap CI excluding 0.5**. (SPEC §9 step 4 says "sane"; this is the number that makes it measurable.)
7. AUPRC reported alongside AUROC (SPEC §5.4 — mandatory given 176:446 imbalance).
8. Auxiliary segmentation Dice recorded.
9. Prediction artifacts frozen to parquet with run ID, git SHA, and checkpoint hash.
10. Run records complete for all 20 fields; `git_dirty` false.
11. **D-006 and D-011 resolved** in the decision log.

## Failure conditions
Internal AUROC < 0.75 → investigate pipeline, labels, and channel mapping. **This is NOT authorization for architecture search** (SI-11) — if the frozen architecture genuinely cannot reach a sane AUROC, that is a decision-log entry and a Research Lead conversation, not a backbone hunt · tiny overfit fails → a real bug, stop · OOM at both 128³ and 96³ → escalate to the D-005/R-H04 accommodation ladder.

## Rollback / recovery
Runs resume from checkpoints. A failed run is discarded and re-launched; the run record retains the failure. Nothing frozen in Phase 05 changes.

## Risks
**R-C08 (architecture scope creep — this is where the temptation peaks)** · R-H04 (OOM) · R-H05 (server downtime) · R-C05 (a channel mis-mapping surviving to here would show as a mysteriously mediocre AUROC).

## Decisions requiring Research Lead approval
**D-006** comparator scope (recommendation: our own backbone in tumour-aware joint configuration, not a reimplementation) · **D-011** BraTS pretraining (recommendation: none) · any hardware-forced architecture change · the definition of "converged".

## Exit criteria
All acceptance criteria met; Gate C satisfied for both runs; prediction artifacts frozen; checkpoints hashed.

## Dependencies for next phase
Phase 07 needs the R2 checkpoint and the calibration-split predictions.
