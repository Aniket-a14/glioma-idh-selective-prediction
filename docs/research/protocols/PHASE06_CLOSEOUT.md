# Phase 06 close-out evidence (R1 and R2)

Written 2026-10-09 from the run records and frozen artifacts. Every number below is read from a file named in the table;
nothing is reasoned from memory. Machine: home GPU (RTX 2060 SUPER, 8 GB), commits `4be0e7f` (R1) and `8a7f59e` (R2).

## Runs

| | R1 | R2 |
|---|---|---|
| Role | no modality dropout (baseline 1/5 source) | modality dropout, primary model (D-041) |
| Run ID | `01M45268QDQ2CFBSPNH117MF41` | `01M46999FB083AX4WW0067YM13` |
| Seed | 0 | 0 |
| Authorization report | `01M451ZVEWSWG3SG3NKHA7RW1M` (commit `4be0e7f`, 7/7 passed, CUDA) | `01M468A4DB96AY7CB3JFYGRZM6` (commit `8a7f59e`, 7/7 passed, CUDA) |
| Epochs run / best epoch | 45 / 14 (stopped early, patience 30) | 65 / 34 (stopped early, patience 30) |
| Best calibration-split classification loss | 0.588 | 0.565 |
| Checkpoint hash (`best.pt`) | `d3c33660fc78a151de5f212b8094f1df450fe9ee8719abd4ab8104ee7d85cfb0` | `1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a` |
| `git_dirty` | false | false |
| Resumes | 0 | 4 (server reboots; resume path from step 6 of the harness) |

## Internal test (124 patients: 35 IDH-mutant, 89 wild-type; hard 0.5 threshold, bootstrap 2000, seed 0)

| | R1 | R2 |
|---|---|---|
| AUROC (95% CI) | 0.872 (0.797, 0.933) | 0.878 (0.804, 0.935) |
| AUPRC (95% CI); no-skill 0.282 | 0.743 (0.597, 0.869) | 0.778 (0.637, 0.882) |
| Brier | 0.171 | 0.140 |
| ECE (10 equal-width bins) | 0.186 | 0.119 |
| Mean Dice, internal test (enhancing / necrotic core / oedema) | 0.284 (0.201 / 0.178 / 0.475) | 0.473 (0.431 / 0.390 / 0.597) |
| Mean Dice, calibration split | 0.302 | 0.475 |

Source files per run: `phase06_report.json`, `segmentation_dice.json`, `predictions.parquet` (each with a `.sha256` sidecar,
verified after copying to the SSD).

## Acceptance criteria (PHASE_06_BASELINE_MODEL.md)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Seven authorization steps pass and are recorded | met | both `authorization_report.json` files, `authorized: true`, all seven `passed` |
| 2 | Parameters within 10-30M | met | 18,815,144 (counted from `build_model(ModelConfig())`) |
| 3 | Tiny overfit reaches near-zero loss on 4 patients | met | loss 0.79 to 0.0108 (R1 report) and 0.0112 (R2 report) in 43 steps |
| 4 | Checkpoint save/resume numerically identical | met | harness step 6 (exact equality under deterministic mode, D-040); R2 resumed 4 times on real reboots |
| 5 | R1 and R2 trained to convergence, early stopping on the calibration split only | met | D-039 definition (calibration loss, patience 30, max 300); both stopped early; internal test never used |
| 6 | Internal AUROC >= 0.75 with CI excluding 0.5 | met | R1 0.872 (0.797, 0.933); R2 0.878 (0.804, 0.935) |
| 7 | AUPRC reported beside AUROC | met | table above |
| 8 | Auxiliary Dice recorded | met | `segmentation_dice.json`, both splits; the values are low for R1 and moderate for R2, there is no Dice threshold in the phase file |
| 9 | Prediction artifacts frozen to parquet with run ID, git SHA, checkpoint hash | met | R1 artifact carries `record_git_sha` 4be0e7f and freeze commit 5939446 (`--allow-sha-mismatch`, D-044); R2 artifact SHA equals the run SHA |
| 10 | Run records complete for the 22 mandatory keys (D-038); `git_dirty` false | met with one gap | all 22 keys present in both records; lifecycle key `end_time_utc` is `null` in both because `train_run` never wrote it. Fixed for later runs in this branch; R1 and R2 records keep the null (the end time is the last `train.log` line) |
| 11 | D-006 and D-011 resolved | met | both RESOLVED 2026-09-30 in `DECISION_LOG.md` |

## Scientific validation (phase file)

Literature range cited in the spec is 0.90 and above for comparable systems. R1 and R2 are 0.872 and 0.878, with upper CI
bounds of 0.933 and 0.935, so neither is "materially lower" and neither is "materially higher". No pipeline or leakage
investigation is triggered by the values. The gap to 0.90 is stated here so it is not discovered later.

## Not closed by this evidence

- **T06.9 pilot.** The only pilot run is `pilot-timing` (`01M3RQCSDVMPZHN4Z9P0848425`, 1 epoch, commit `e437147`, 2026-09-30),
  a speed measurement. No hyperparameter sizing was run. R1 and R2 used the D-039 starting values; the only value changed
  before the runs was the harness overfit-test learning rate (D-043), set to 3e-4 on 4 training patients; the training config was not tuned. Logged as D-049.
- **Gate D** needs an independent review of the criteria above. It has not happened.
- **Authorization records.** The harness leaves its step-7 record with `status: running` (it writes a launch record and never
  finalizes it). Nothing reads that status; recorded here so nobody mistakes it for a live run.
