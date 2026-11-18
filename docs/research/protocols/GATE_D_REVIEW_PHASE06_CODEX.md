# Gate D independent review — Phase 06

Date: 2026-11-18. Reviewed code: `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`.

Reviewer: Codex, independent of the phase author. **D-001 degraded solo fallback: a second agent, not a second human.** No claim is made that a human Person C reviewed or signed anything.

**Gate D verdict: PASS WITH CONCERNS.** Review task status: **DONE_WITH_CONCERNS**. Acceptance counts: 11 met, 0 not met, 0 cannot tell.

Criteria source: [PHASE_06_BASELINE_MODEL.md](../phases/PHASE_06_BASELINE_MODEL.md). Author briefs/readiness tables were treated as assertions to check. The embedded read-only checker below was actually executed, exit 0, using the requested virtualenv and `PYTHONPATH=src`. Each criterion repeats its exact command; shared commands were run once, not once per repeated listing. Outputs are trimmed.

Storage was resolved through `glioma_selective.utils.paths` with `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`. Only the named UTSW run artifacts and UTSW manifest summary were used (plus R8’s explicitly referenced stage-1 record). No external image/label file was opened; the authorization flag was unset and was never assigned. No installation, training, inference, refit of the IDH model, or write to the SSD occurred. A historical “met” GPU outcome means its frozen report was checked; a new live GPU measurement is not claimed.

## Criterion 1: met

All seven authorization steps pass and are recorded.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
authorization_R1 {"authorized": true, "results": [{"detail": "481 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.010751175; curve_start=0.79067647; curve_min=0.010751175; curve_end=0.010751175", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
authorization_R2 {"authorized": true, "results": [{"detail": "623 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.0111804; curve_start=0.79067647; curve_min=0.0111804; curve_end=0.0111804", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
```

Comparison and judgment: Compared the two on-disk authorization reports with the seven required steps, in order. Both authorize the run and record every step as passed. These are historical CUDA observations; I did not run a new GPU job.

## Criterion 2: met

Model parameter count within 10–30M (SPEC §3.4).

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
parameters 18815144
```

Comparison and judgment: 18,815,144 parameters, built from the current ModelConfig defaults; compared with the inclusive 10–30 million requirement.

## Criterion 3: met

Tiny overfit test reaches near-zero loss on 4 patients.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
authorization_R1 {"authorized": true, "results": [{"detail": "481 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.010751175; curve_start=0.79067647; curve_min=0.010751175; curve_end=0.010751175", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
authorization_R2 {"authorized": true, "results": [{"detail": "623 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.0111804; curve_start=0.79067647; curve_min=0.0111804; curve_end=0.0111804", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
overfit_source ["src/glioma_selective/training/authorization.py:
... [remaining output trimmed]
```

Comparison and judgment: Recorded real (synthetic=false) four-patient overfit: loss 0.79067647 to 0.010751175 (R1) and 0.0111804 (R2), 43 steps each, below the harness threshold 0.05. authorization.py constructs four real samples for this step. A fresh full-size CUDA rerun cannot be checked on this Mac (cuda_available=false); that would require the training GPU and a separately authorized scratch run. The historical acceptance result is present.

## Criterion 4: met

Checkpoint save/resume is numerically identical.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
authorization_R1 {"authorized": true, "results": [{"detail": "481 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.010751175; curve_start=0.79067647; curve_min=0.010751175; curve_end=0.010751175", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
authorization_R2 {"authorized": true, "results": [{"detail": "623 passed", "name": "CPU unit tests", "status": "passed"}, {"detail": "1 sample; data, zero-channel and augmentation checks passed", "name": "one-sample data test", "status": "passed"}, {"detail": "batch=2; device=cuda; logits finite with zeroed channel", "name": "tiny-batch forward pass", "status": "passed"}, {"detail": "steps=43; final_loss=0.0111804; curve_start=0.79067647; curve_min=0.0111804; curve_end=0.0111804", "name": "tiny overfit", "status": "passed"}, {"detail": "device=NVIDIA GeForce RTX 2060 SUPER; peak_bytes=5825517056; total_bytes=8161329152; fraction=0.713795", "name": "GPU memory test", "status": "passed"}, {"detail": "N=3; resumed_max_abs=0; checkpoint forward identical", "name": "checkpoint save/resume equivalence", "status": "passed"}, {"detail": "launch record accepted; clean checkout; torch.use_deterministic_algorithms(True, warn_only=True); no non-deterministic operation warnings in the logging probe", "name": "deterministic/config logging", "status": "passed"}]}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Comparison and judgment: Both recorded checkpoint probes have resumed_max_abs=0. Current CPU checkpoint/resume tests in test_training_loop.py passed as part of the unit command. This establishes the saved probe and current CPU behavior; bitwise equivalence of a fresh interrupted production CUDA run remains unmeasured and would require a paired GPU run.

## Criterion 5: met

R1 and R2 trained to convergence with early stopping on the **calibration split only**.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
training_R1 {"best_epoch_0based": 14, "epochs": 45, "metrics": {"best_epoch": 14, "calibration_auroc_at_best_epoch": 0.910593900481541, "calibration_classification_loss": 0.5882278412219978, "stopped_early": true}, "patience": 30, "trailing_nonimproving_epochs": 30}
training_R2 {"best_epoch_0based": 34, "epochs": 65, "metrics": {"best_epoch": 34, "calibration_auroc_at_best_epoch": 0.9170144462279294, "calibration_classification_loss": 0.5652036989227899, "stopped_early": true}, "patience": 30, "trailing_nonimproving_epochs": 30}
training_source ["src/glioma_selective/training/run.py:144: def _build_datasets(seed: int) -> tuple[Any, Any, Any]:", "src/glioma_selective/training/run.py:145:     from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids", "src/glioma_selective/training/run.py:146:     from glioma_selective.preprocessing.normalize import load_normalization_stats", "src/glioma_selective/training/run.py:147: ", "src/glioma_selective/training/run.py:148:     manifests = paths.manifests_dir()", "src/glioma_selective/training/run.py:149:     stats_path = manifests / \"normalization_stats.json\"", "src/glioma_selective/training/run.py:150:     expected = Path(str(stats_path) + \".sha256\").read_text(encoding=\"ascii\").split()[0]", "src/glioma_selective/training/run.py:151:     stats = load_normalization_stats(stats_path, expected_sha256=expected)", "src/glioma_selective/training/run.py:152:     storage = paths.processed_data_dir()", "src/glioma_selective/training/run.py:153:     train = IDHDataset(", "src/glioma_selective/training/run.py:154:         load_split_patient_ids(\"train\"),", "src/glioma_selective/training/run.py:155:         stats=stats,", "src/glioma_selective/training/run.py:156:         seed=seed,", "src/glioma_selective/training/run.py:157:         augment=True,", "src/glioma_selective/training/run.py:158:         storage=storage,", "src/glioma_selective/training/run.py:159:     )", "src/glioma_selective/training/run.py:160:     calibration = IDHDataset(", "src ... [trimmed]
stopping_source ["src/glioma_selective/training/loop.py:409:         calibration = evaluate(model, calibration_loader, config, pos_weight, device)", "
... [remaining output trimmed]
```

Comparison and judgment: Recomputed the minimum calibration classification loss from each full history: R1 best zero-based epoch 14 of 45, R2 epoch 34 of 65. Each ends after exactly 30 non-improving epochs, equal to configured patience. Dataset construction loads train and calibration only; checkpoint selection uses calibration.classification_loss. Compared with criterion 5 and the D-039 stopping rule.

## Criterion 6: met

Internal test AUROC is "sane" — defined concretely as **AUROC ≥ 0.75 with a bootstrap CI excluding 0.5**. (SPEC §9 step 4 says "sane"; this is the number that makes it measurable.)

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
baseline_R1 {"brier": 0.17122640446513873, "coverage": 1.0, "derived_auprc": 0.7429757990636939, "derived_auprc_ci": [0.5949750352584352, 0.866718916108959], "derived_auroc": 0.8719101123595505, "derived_auroc_ci": [0.7955252371741733, 0.9326813592284741], "ece10": 0.18632296135242835, "frozen_auroc_ci": [0.7970225000569333, 0.9325907270570701], "iterations": 2000, "mutant": 35, "n": 124, "seed": 0}
baseline_R2 {"brier": 0.13992721006181305, "coverage": 1.0, "derived_auprc": 0.7782311870661562, "derived_auprc_ci": [0.6467972404191409, 0.8841371884565146], "derived_auroc": 0.878330658105939, "derived_auroc_ci": [0.8076105133523463, 0.9386660617059891], "ece10": 0.11886621431386386, "frozen_auroc_ci": [0.8036164174972315, 0.9351179257232608], "iterations": 2000, "mutant": 35, "n": 124, "seed": 0}
original_order_CI_R1 {"frozen": [0.7970225000569333, 0.9325907270570701], "recomputed": [0.7970225000569333, 0.9325907270570701]}
original_order_CI_R2 {"frozen": [0.8036164174972315, 0.9351179257232608], "recomputed": [0.8036164174972315, 0.9351179257232608]}
```

Comparison and judgment: Independent pairwise AUROC and 2,000 patient-index bootstrap draws reproduce the Phase 06 points and intervals when original parquet order is retained. Both points exceed 0.75 and both lower limits exceed 0.5. Sorting patient IDs reproduces the later Phase 10 interval: the apparent discrepancy is seeded resampling order, not a metric discrepancy.

## Criterion 7: met

AUPRC reported alongside AUROC (SPEC §5.4 — mandatory given 176:446 imbalance).

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
baseline_R1 {"brier": 0.17122640446513873, "coverage": 1.0, "derived_auprc": 0.7429757990636939, "derived_auprc_ci": [0.5949750352584352, 0.866718916108959], "derived_auroc": 0.8719101123595505, "derived_auroc_ci": [0.7955252371741733, 0.9326813592284741], "ece10": 0.18632296135242835, "frozen_auroc_ci": [0.7970225000569333, 0.9325907270570701], "iterations": 2000, "mutant": 35, "n": 124, "seed": 0}
baseline_R2 {"brier": 0.13992721006181305, "coverage": 1.0, "derived_auprc": 0.7782311870661562, "derived_auprc_ci": [0.6467972404191409, 0.8841371884565146], "derived_auroc": 0.878330658105939, "derived_auroc_ci": [0.8076105133523463, 0.9386660617059891], "ece10": 0.11886621431386386, "frozen_auroc_ci": [0.8036164174972315, 0.9351179257232608], "iterations": 2000, "mutant": 35, "n": 124, "seed": 0}
```

Comparison and judgment: Independent non-interpolated average precision agrees with frozen AUROC-adjacent AUPRC: R1 0.7429757991, R2 0.7782311871. Compared with phase06_report.json and the required imbalance-aware reporting.

## Criterion 8: met

Auxiliary segmentation Dice recorded.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
dice_R1 {"calibration": {"mean": 0.3018291147635627, "n_with_segmentation": 123, "n_without_segmentation": 1, "per_channel": {"enhancing": 0.22280839455536933, "necrotic_core": 0.20078042649991115, "oedema": 0.4818985232354077}}, "internal_test": {"mean": 0.2844640274402533, "n_with_segmentation": 124, "n_without_segmentation": 0, "per_channel": {"enhancing": 0.20061382285513524, "necrotic_core": 0.1776479810256662, "oedema": 0.47513027843995836}}}
dice_R2 {"calibration": {"mean": 0.4749011635265176, "n_with_segmentation": 123, "n_without_segmentation": 1, "per_channel": {"enhancing": 0.44455926621895175, "necrotic_core": 0.3951960348862432, "oedema": 0.5849481894743578}}, "internal_test": {"mean": 0.47267292945834144, "n_with_segmentation": 124, "n_without_segmentation": 0, "per_channel": {"enhancing": 0.4310567952272538, "necrotic_core": 0.38962577686442385, "oedema": 0.5973362162833468}}}
```

Comparison and judgment: Both SHA-256-verified segmentation_dice.json files record calibration and internal-test Dice and counts; no Dice threshold is specified. This verifies recorded values, not a new segmentation inference pass.

## Criterion 9: met

Prediction artifacts frozen to parquet with run ID, git SHA, and checkpoint hash.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
freeze_R1 {"actual_checkpoint_sha256": "d3c33660fc78a151de5f212b8094f1df450fe9ee8719abd4ab8104ee7d85cfb0", "metadata": {"checkpoint_hash": "d3c33660fc78a151de5f212b8094f1df450fe9ee8719abd4ab8104ee7d85cfb0", "git_sha": "5939446ec6cf2b2eacf8423fb73222b9aa87c7ef", "record_git_sha": "4be0e7f8fa629944ef5709b3a55657da5f768de1", "run_id": "01M45268QDQ2CFBSPNH117MF41", "schema_version": "1"}, "record_checkpoint_sha256": "d3c33660fc78a151de5f212b8094f1df450fe9ee8719abd4ab8104ee7d85cfb0", "record_git_sha": "4be0e7f8fa629944ef5709b3a55657da5f768de1", "row_checkpoint_matches": true, "row_run_id_matches": true, "rows": 248}
freeze_R2 {"actual_checkpoint_sha256": "1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a", "metadata": {"checkpoint_hash": "1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a", "git_sha": "8a7f59e61e0ade31be5234874d8b6b610bbb2b9f", "run_id": "01M46999FB083AX4WW0067YM13", "schema_version": "1"}, "record_checkpoint_sha256": "1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a", "record_git_sha": "8a7f59e61e0ade31be5234874d8b6b610bbb2b9f", "row_checkpoint_matches": true, "row_run_id_matches": true, "rows": 248}
```

Comparison and judgment: Both parquets verify against their sidecars; row run IDs/checkpoint hashes and actual best.pt bytes agree with their records. Git SHA is in Arrow metadata. R1 records both the training SHA 4be0e7f8 and freeze SHA 5939446e; the mismatch is explicit and allowed by resolved D-044. R2 SHAs agree.

## Criterion 10: met

Run records complete for all 20 fields; `git_dirty` false.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
record_R1 {"end_time_utc": null, "git_dirty": false, "mandatory_key_count": 22, "missing": [], "null_mandatory": [], "status": "completed"}
record_R2 {"end_time_utc": null, "git_dirty": false, "mandatory_key_count": 22, "missing": [], "null_mandatory": [], "status": "completed"}
record_validation_R1 []
record_validation_R2 []
```

Comparison and judgment: All 20 protocol groups (22 flattened mandatory keys) are present and non-null, validate_run_record returns [], and git_dirty=false. Explicit not-applicable baseline calibration/threshold strings are valid. end_time_utc is null in both records; it is lifecycle metadata outside the 20 groups, so this is finding F08 rather than a failure of criterion 10.

## Criterion 11: met

**D-006 and D-011 resolved** in the decision log.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
D-006 "D-006 \u2014 Baseline 5 (\"reproduced published comparator\") is unbounded in scope\n**Status:** RESOLVED 2026-09-30 (Research Lead: option (b)) \u00b7 **Resolve by:** Phase 06 \u00b7 **Blocking:** yes\n\n**Resolution 2026-09-30.** Option (b). M6 is our own SegResNet backbone with the auxiliary segmentation head and tumour-aware pooling, trained and evaluated always-predict. It is described in the manuscript as a tumour-aware joint-learning comparator in the style of COM-Net/MTS-UNET/GMMAS, implemented on our backbone for cohort-matched comparability, and not as a reproduction of those systems. Published numbers are cited as context on ... [remaining decision entry trimmed]
D-011 "D-011 \u2014 BraTS pretraining is permitted but not required\n**Status:** RESOLVED 2026-09-30 (Research Lead: option (a)) \u00b7 **Resolve by:** Phase 06 \u00b7 **Blocking:** yes\n\n**Resolution 2026-09-30.** Option (a). No BraTS pretraining: every network is trained from random initialization on UTSW train only. This removes the BraTS-to-UCSF/TCGA/EGD ID-overlap leakage class. Reopening it requires its own Gate-D-level exclusion audit and Research Lead sign-off recorded here.\n\n**Conflict.** SPEC \u00a72.5 permits BraTS *\"only as a source of segmentation pretraining weights (if at all)\"* and, if used, requires excluding every subje ... [remaining decision entry trimmed]
```

Comparison and judgment: Both decisions are RESOLVED, 2026-09-30, by the Research Lead. D-006 bounds the comparator; D-011 chooses no BraTS pretraining. The author brief does not substitute for these decision entries.

## Scientific validation and limits

The concrete sane-AUROC requirement passes. A controlled comparison to the specification’s 0.90+ literature range cannot be certified from the author’s narrative alone: comparator cohorts, uncertainty and full-text numbers were not independently established here. Both bootstrap intervals include 0.90, and no “materially lower” margin is pre-specified. This does not license architecture search or retraining. D-049 already resolves the timing-only pilot as an accepted limitation; no new pilot exception is needed.

F08 (low): R1/R2 end_time_utc remains null despite completed status. The recorded historical GPU probes are present; live CUDA availability here is false.

Next action: Research Lead records the Phase 06 disposition and preserves the D-044/D-049 and lifecycle caveats.

## Reproducible read-only checker

The command above executes this embedded code. It contains reviewer calculations and source inspection only; it never calls artifact-writing analysis entry points.

<!-- BEGIN REVIEW CHECKER -->
```python
import sys, os, json, hashlib, math, re, subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import minimize_scalar
from scipy.special import expit
from glioma_selective.utils import paths
assert 'GLIOMA_EXTERNAL_EVAL_AUTHORIZED' not in os.environ
RUNS = ['01M45268QDQ2CFBSPNH117MF41','01M46999FB083AX4WW0067YM13','01M4FPECM9DKAR7F6B7VFRQNC5','01M60CYFD2AYA8DCPBTDSJS4DM','01M66E2KR6ZV2YPBTNPF5FD53T','01M776GTZC70FTB1ABD2DDMYHH','01M7C0KRNY5M2SNH59PH97XZ8K','01M7JZYEBFCJF8WY0W1WJ3RZX7']
ROOT = paths.experiments_dir()
CONDS = ['full','drop_t1','drop_t1ce','drop_t2','drop_flair','t1ce_flair_only']
GRID = [.9,.8,.7,.6,.5]
def emit(tag, value): print(tag, json.dumps(value, sort_keys=True, default=str))
def load(i,name): return json.loads((ROOT/RUNS[i-1]/name).read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def verified(p):
 assert digest(p)==p.with_name(p.name+'.sha256').read_text().split()[0], str(p)
 return True
def frame(i,name='predictions.parquet',split=None):
 p=ROOT/RUNS[i-1]/name; verified(p); f=pd.read_parquet(p)
 assert set(f.cohort)<= {'utsw_calibration','utsw_internal_test'}, str(p)
 if split: f=f[f.cohort=='utsw_'+split]
 assert not f.duplicated(['patient_id','cohort','modality_condition']).any()
 return f.sort_values('patient_id').reset_index(drop=True)
def temp(f):
 z=f.logit.to_numpy(float); y=f.label.to_numpy(int)
 r=minimize_scalar(lambda t:np.mean(np.logaddexp(0,z/np.exp(t))-y*z/np.exp(t)),bounds=(math.log(.05),math.log(20)),method='bounded',options={'xatol':1e-12})
 return float(np.exp(r.x))
def ece(p,y,b=10):
 q=np.minimum((p*b).astype(int),b-1)
 return sum(abs(float(np.sum(p[q==i]-y[q==i])))/len(y) for i in range(b))
def auc(p,y):
 a=p[y==1,None]; b=p[y==0][None,:]
 return float(np.mean((a>b)+.5*(a==b)))
def ap(p,y):
 o=np.argsort(-p,kind='stable'); p=p[o];y=y[o]; k=np.flatnonzero(np.r_[p[1:]!=p[:-1],True])+1
 tp=np.cumsum(y)[k-1];return float(np.sum(np.diff(np.r_[0,tp])*tp/k)/y.sum())
def curve(s,e):
 o=np.argsort(-np.asarray(s),kind='stable'); s=np.asarray(s)[o];e=np.asarray(e)[o]
 k=np.flatnonzero(np.r_[s[1:]!=s[:-1],True])+1; risks=np.cumsum(e)[k-1]/k
 return k,risks,e,o
def area(s,e):
 k,r,_,_=curve(s,e);return float(np.sum(np.diff(np.r_[0,k])*r)/len(e))
def interval(v): return np.quantile(v,[.025,.975])
def close(a,b,tol=1e-9):
 assert np.allclose(a,b,atol=tol,rtol=0), (a,b)
def quantile(p,y,a):
 from fractions import Fraction
 n=len(y); k=math.ceil((n+1)*(1-Fraction(str(a))))
 s=np.where(y==1,1-p,p)
 return float(np.sort(s)[k-1]) if k<=n else math.inf

def phase06():
 from glioma_selective.models.segresnet import build_model, ModelConfig
 from glioma_selective.tracking.run_record import MANDATORY_KEYS,validate_run_record
 emit('parameters',sum(p.numel() for p in build_model(ModelConfig()).parameters()))
 for i,auth in [(1,'01M451ZVEWSWG3SG3NKHA7RW1M'),(2,'01M468A4DB96AY7CB3JFYGRZM6')]:
  j=json.loads((ROOT/auth/'authorization_report.json').read_text())
  emit('authorization_R'+str(i),{'authorized':j['authorized'],'git_dirty':j['git_dirty'],'results':j['results']})
  r=load(i,'record.json'); h=r['training_history']; cfg=r['config']['training']
  loss=np.array([x['calibration_classification'] for x in h]); best=int(np.argmin(loss))
  emit('training_R'+str(i),{'epochs':len(h),'best_epoch_0based':best,'trailing_nonimproving_epochs':len(h)-best-1,'patience':cfg['early_stopping_patience'],'metrics':{k:v for k,v in r['metrics'].items() if k not in ['internal_analysis','internal_test']}})
  emit('record_R'+str(i),{'mandatory_key_count':len(MANDATORY_KEYS),'missing':[k for k in MANDATORY_KEYS if k not in r],'null_mandatory':[k for k in MANDATORY_KEYS if r.get(k) is None],'git_dirty':r['git_dirty'],'status':r['status'],'end_time_utc':r.get('end_time_utc')})
  try: validate_run_record(r); emit('record_validation_R'+str(i),validate_run_record(r))
  except Exception as e: emit('record_validation_R'+str(i),str(e))
  p=ROOT/RUNS[i-1]; f=frame(i); meta={k.decode():v.decode() for k,v in pq.read_metadata(p/'predictions.parquet').metadata.items() if k!=b'ARROW:schema'}
  emit('freeze_R'+str(i),{'rows':len(f),'metadata':meta,'row_run_id_matches':bool((f.run_id==RUNS[i-1]).all()),'row_checkpoint_matches':bool((f.checkpoint_hash==r['checkpoint_hash']).all()),'actual_checkpoint_sha256':digest(p/'checkpoints/best.pt'),'record_checkpoint_sha256':r['checkpoint_hash'],'record_git_sha':r['git_sha']})
  t=frame(i,split='internal_test');prob=t.p_hat.to_numpy(float);y=t.label.to_numpy(int); report=load(i,'phase06_report.json');verified(p/'phase06_report.json')
  it=report['bootstrap']['iterations'];seed=report['bootstrap']['seed'];rng=np.random.default_rng(seed);aa=[];pp=[]
  for idx in rng.integers(0,len(y),size=(it,len(y))):
   if 0<y[idx].sum()<len(y):aa.append(auc(prob[idx],y[idx]));pp.append(ap(prob[idx],y[idx]))
  original=pd.read_parquet(p/'predictions.parquet');original=original[original.cohort=='utsw_internal_test'];oprob=original.p_hat.to_numpy(float);oy=original.label.to_numpy(int);original_ci=interval([auc(oprob[idx],oy[idx]) for idx in np.random.default_rng(seed).integers(0,len(oy),size=(it,len(oy))) if 0<oy[idx].sum()<len(oy)])
  emit('original_order_CI_R'+str(i),{'recomputed':original_ci.tolist(),'frozen':report['auroc_ci']});close(original_ci,report['auroc_ci'])
  emit('baseline_R'+str(i),{'n':len(y),'mutant':int(y.sum()),'iterations':it,'seed':seed,'derived_auroc':auc(prob,y),'derived_auroc_ci':interval(aa).tolist(),'frozen_auroc_ci':report['auroc_ci'],'derived_auprc':ap(prob,y),'derived_auprc_ci':interval(pp).tolist(),'brier':float(np.mean((prob-y)**2)),'ece10':ece(prob,y),'coverage':1.0})
  close(auc(prob,y),report['auroc']);close(ap(prob,y),report['auprc'])
  verified(p/'segmentation_dice.json'); emit('dice_R'+str(i),load(i,'segmentation_dice.json')['splits'])
def show(tag, filename, start, end):
    lines=Path(filename).read_text().splitlines()
    emit(tag, [f"{filename}:{i+1}: {line}" for i,line in enumerate(lines) if start<=i+1<=end])
def decision(key):
    text=Path('docs/research/DECISION_LOG.md').read_text()
    sections=text.split('\n## ')
    emit(key,next(x for x in sections if x.startswith(key+' ')))

phase06()
show('training_source','src/glioma_selective/training/run.py',144,167)
show('stopping_source','src/glioma_selective/training/loop.py',409,450)
show('overfit_source','src/glioma_selective/training/authorization.py',510,550)
for key in ['D-006','D-011','D-044','D-049']: decision(key)
emit('cuda_available',__import__('torch').cuda.is_available())

```
