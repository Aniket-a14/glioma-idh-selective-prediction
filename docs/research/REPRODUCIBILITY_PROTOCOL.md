# REPRODUCIBILITY PROTOCOL

Designed before the first real training run, not retrofitted after it.

---

## 1. The run record

Every experiment writes a JSON run record to `artifacts/experiments/<run_id>/record.json`. **All twenty fields are mandatory**; a missing field blocks Gate C.

| # | Field | Source |
|---|---|---|
| 1 | `run_id` | ULID, generated at launch |
| 2 | `timestamp_utc` | launch time |
| 3 | `git_sha` | `git rev-parse HEAD` |
| 4 | `git_dirty` | **must be `false` for FINAL/ABLATION/EXTERNAL runs** |
| 5 | `dataset_manifest_hash` | SHA-256 of the cohort manifest |
| 6 | `split_manifest_hash` | SHA-256 of the frozen split |
| 7 | `exclusion_list_hash` | SHA-256 |
| 8 | `config` | fully resolved config, not a reference |
| 9 | `seed` | int |
| 10 | `python_version` | |
| 11 | `dependency_lock_hash` | hash of the lock file |
| 12 | `torch_version`, `monai_version` | |
| 13 | `gpu_info` | model, VRAM, CUDA runtime, driver |
| 14 | `preprocessing_version` | version + parameter hash |
| 15 | `checkpoint_hash` | SHA-256 of the weights |
| 16 | `training_history` | per-epoch losses/metrics |
| 17 | `predictions_path` | frozen parquet |
| 18 | `calibration_params` | temperature, conformal quantile, α |
| 19 | `selective_thresholds` | the τ / α grid used |
| 20 | `metrics`, `log_path` | |

**The on-disk record is authoritative.** Everything else — MLflow, notebooks, memory — is a convenience.

---

## 2. Tracking: MLflow, file-backed, local

**Decision.** Use MLflow with a local file store, artifacts on the external SSD. No cloud dependency, no tracking server to maintain.

**Rationale.** The run-record schema above needs a queryable store, and ~9 training runs plus 108 evaluation cells is past comfortable manual bookkeeping. MLflow is a *convenience layer over* the JSON records, not a replacement: if the MLflow store is corrupted or deleted, no result is lost. This satisfies the master prompt's caution against forcing an unnecessary cloud dependency.

`MLFLOW_TRACKING_URI` is blank in CI and unit tests so tracking never becomes a test dependency.

---

## 3. Configuration

Hydra/OmegaConf, decided in Phase 00. Experiments are defined by **config composition**, e.g.:

```
configs/experiments/final_internal_conformal.yaml
  defaults:
    - /data: utsw_frozen_v1
    - /preprocessing: standard_1mm
    - /model: segresnet_4ch_aux
    - /training: modality_dropout_p03
    - /calibration: temperature + conformal_split
    - /selective: alpha_grid_005_010_020
    - /evaluation: all_18_conditions
```

**Magic constants inside Python modules are a review-blocking defect.** If a number affects a result, it lives in a config and appears in the run record.

---

## 4. Seeding and honest determinism

Seeds are set for Python `random`, NumPy, and Torch (CPU and CUDA), and `torch.use_deterministic_algorithms(True)` is enabled where it does not forbid a required operation. Dataloader workers are seeded deterministically.

**We do not claim bitwise reproducibility we cannot deliver.** Some CUDA kernels (certain 3D convolution backward paths, atomics in scatter operations) are non-deterministic regardless of seeding. The protocol:

1. Record which operations run non-deterministically, in the run record.
2. Quantify it: re-run one FINAL configuration with an identical seed and report the run-to-run variation in the primary metric.
3. Report that variation in the manuscript alongside the headline number.

An honest ±0.004 AUROC run-to-run band is more credible than a false claim of exact reproducibility.

---

## 5. Prediction artifacts are the analysis substrate

The model runs **once** per (checkpoint × cohort × modality condition). Its per-patient outputs are frozen to parquet:

```
patient_id | cohort | modality_condition | run_id | checkpoint_hash
           | p_hat | logit | mc_dropout_samples | ensemble_member_probs
           | nonconformity_score | label
```

Every risk–coverage curve, AURC, threshold sweep, bootstrap, and figure is recomputed from these files. Consequences, all deliberate:

- Analysis is cheap and fast — the 108 result cells cost CPU minutes, not GPU days.
- Analysis is reproducible without a GPU, so Person C can verify results independently.
- It is **impossible to accidentally re-tune by re-running the model**, because analysis never touches the model.
- The compute budget closes (see **D-005**).

---

## 6. Environment

`pyproject.toml` with a committed lock file. Versions are **not pinned at plan time** — Phase 01 verifies MONAI/PyTorch/CUDA compatibility against the actual GPU server before anything is locked, because the driver and CUDA runtime there are unknown.

Both machines install from the same lock. `scripts/capture_environment.py` writes the full environment fingerprint into every run record.

---

## 7. The reproducibility package (Phase 14)

Released with the paper:

- Source code at the publication SHA, tagged.
- All configs for every reported run.
- Cohort, exclusion, and split manifests with hashes (IDs included only where dataset terms permit; otherwise hashes and counts).
- Environment lock file.
- Run records for every reported experiment.
- Frozen prediction artifacts where terms permit redistribution.
- Frozen statistical result files.
- One command that regenerates every figure and table from the frozen results.

**Acceptance test:** someone not on the project follows the README and regenerates every figure and table. If they cannot, the package is incomplete.

---

## 8. Regeneration test (Gate F)

```bash
rm -rf paper/figures paper/tables
python -m glioma_selective.cli.build_paper_artifacts
git diff --stat paper/          # must be empty (or numerically identical)
```

**A figure that cannot be regenerated does not go in the paper.**
