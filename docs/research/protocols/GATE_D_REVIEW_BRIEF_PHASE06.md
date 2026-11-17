# Gate D review brief: Phase 06 (baseline model, R1 and R2)

Written 2026-11-17 for the independent reviewer. Gate D needs someone who did not write the phase to check every acceptance
criterion against the artifacts (`README.md` quality gates). The author's own evidence table is
`PHASE06_CLOSEOUT.md`; this brief tells you what to re-check yourself and how. Nothing here needs the GPU or any external
cohort. You need the external SSD (`/Volumes/Research_2`) and the repository at `main`.

Runs: R1 `01M45268QDQ2CFBSPNH117MF41` (no modality dropout), R2 `01M46999FB083AX4WW0067YM13` (primary). Files are under
`/Volumes/Research_2/artifacts/experiments/<run>/`.

## What to re-check, criterion by criterion (`PHASE_06_BASELINE_MODEL.md`, acceptance criteria 1 to 11)

| # | Criterion | How to check it yourself |
|---|---|---|
| 1 | Seven authorization steps pass, recorded | Open `authorization_report.json` in `01M451ZVEWSWG3SG3NKHA7RW1M` (R1) and `01M468A4DB96AY7CB3JFYGRZM6` (R2): `authorized` is true and the seven entries of `results` are `passed` (CPU unit tests, one-sample data test, tiny-batch forward pass, tiny overfit, GPU memory test, checkpoint save/resume equivalence, deterministic/config logging) |
| 2 | 10 to 30 M parameters | `python -c "from glioma_selective.models.segresnet import build_model, ModelConfig; m = build_model(ModelConfig()); print(sum(p.numel() for p in m.parameters()))"` prints 18815144 (re-run 2026-11-17) |
| 3 | Overfit test on 4 patients reaches near-zero loss | The `tiny overfit` entry of `results` in each authorization report: loss 0.79 to about 0.011 in 43 steps |
| 4 | Save and resume is numerically identical | The `checkpoint save/resume equivalence` entry (`resumed_max_abs=0`); the resume tests in `tests/unit`; R2 resumed 4 times on real reboots (`train.log`) |
| 5 | Early stopping on the calibration split only | `train.log` and the config: patience 30, metric is calibration-split loss (D-039); confirm the internal test split is never read in `src/glioma_selective/training/` (`grep -rn internal_test src/glioma_selective/training` returns nothing today; a weak check, so also read the epoch loop's split handling) |
| 6 | Internal AUROC at least 0.75, CI excludes 0.5 | `phase06_report.json`: R1 0.872 (0.797, 0.933), R2 0.878 (0.804, 0.935). The Phase 10 recomputation gives the same point (0.878) with 0.808 to 0.939; the interval differs in the third decimal (different bootstrap; not investigated, the point estimates agree) |
| 7 | AUPRC next to AUROC | `phase06_report.json` |
| 8 | Auxiliary Dice recorded | `segmentation_dice.json`; phase file has no Dice threshold |
| 9 | Frozen parquet with run id, git SHA, checkpoint hash | `predictions.parquet` columns `run_id`, `checkpoint_hash`; R1's record SHA `4be0e7f8` differs from its freeze commit (D-044, `--allow-sha-mismatch`); R2's equal |
| 10 | Run record complete, `git_dirty` false | `record.json`: 25 keys, `git_dirty` false in both; `end_time_utc` is null in both (known gap, fixed for later runs) |
| 11 | D-006 and D-011 resolved | `DECISION_LOG.md`, both RESOLVED 2026-09-30 |

Independent integrity checks (each takes seconds):

```
shasum -a 256 /Volumes/Research_2/artifacts/experiments/<run>/checkpoints/best.pt   # equals checkpoint_hash in record.json
shasum -a 256 -c predictions.parquet.sha256                                         # run inside the run folder
```

Expected `best.pt` hashes: R1 `d3c33660fc78a151...`, R2 `1d0c53023fef5615...` (full hashes in `PHASE06_CLOSEOUT.md`).
Both matched on 2026-11-17 after the copy to the SSD.

## Scientific validation required by the phase file

The spec's literature range is AUROC 0.90 and above; R1 and R2 are 0.872 and 0.878 (upper bounds 0.933, 0.935). Check that
you agree this is not "materially lower" and triggers no pipeline or leakage investigation. The author's reading is in
`PHASE06_CLOSEOUT.md`, "Scientific validation".

## Known gaps to judge, not to fix

- **T06.9 pilot** was a 1-epoch speed run only (`pilot-timing`); no hyperparameter sizing was run. R1 and R2 used the D-039
  starting values; the one value changed before the runs was the overfit-test learning rate (D-043). Logged as D-049. Decide
  whether this satisfies the phase file's pilot task or needs a written exception.
- R1 and R2 are one seed each; the ensemble (R3 to R6) came later under Phase 08.
- The step-7 authorization record stays at `status: running` (the harness never finalizes it; nothing reads it).

## What to send back

For each criterion: agree, disagree (with the file and line you checked) or cannot check. A disagreement is a finding for
the Research Lead; nobody edits the closeout table to make it pass. The Research Lead records the outcome in
`PROJECT_STATE.md` and marks Gate D for Phase 06.

Scope note: this covers Phase 06 only. Gate D is also required at the end of Phases 07 to 10; those are not briefed here.
