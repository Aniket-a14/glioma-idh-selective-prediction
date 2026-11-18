# Gate D independent review — Phase 08

Date: 2026-11-18. Reviewed code: `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`.

Reviewer: Codex, independent of the phase author. **D-001 degraded solo fallback: a second agent, not a second human.** No claim is made that a human Person C reviewed or signed anything.

**Gate D verdict: HOLD — D-012 remains unresolved.** Review task status: **DONE_WITH_CONCERNS**. Acceptance counts: 7 met, 0 not met, 1 cannot tell.

Criteria source: [PHASE_08_MISSING_MODALITY.md](../phases/PHASE_08_MISSING_MODALITY.md). Author briefs/readiness tables were treated as assertions to check. The embedded read-only checker below was actually executed, exit 0, using the requested virtualenv and `PYTHONPATH=src`. Each criterion repeats its exact command; shared commands were run once, not once per repeated listing. Outputs are trimmed.

Storage was resolved through `glioma_selective.utils.paths` with `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`. Only the named UTSW run artifacts and UTSW manifest summary were used (plus R8’s explicitly referenced stage-1 record). No external image/label file was opened; the authorization flag was unset and was never assigned. No installation, training, inference, refit of the IDH model, or write to the SSD occurred. A historical “met” GPU outcome means its frozen report was checked; a new live GPU measurement is not claimed.

## Criterion 1: met

Modality dropout confirmed active in R2–R6 with the schedule documented.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
dropout_R2 {"modality_dropout": true, "modality_dropout_keep_all_probability": 0.5, "seed": 0}
dropout_R3 {"modality_dropout": true, "modality_dropout_keep_all_probability": 0.5, "seed": 1}
dropout_R4 {"modality_dropout": true, "modality_dropout_keep_all_probability": 0.5, "seed": 2}
dropout_R5 {"modality_dropout": true, "modality_dropout_keep_all_probability": 0.5, "seed": 3}
dropout_R6 {"modality_dropout": true, "modality_dropout_keep_all_probability": 0.5, "seed": 4}
dropout_source ["src/glioma_selective/training/modality_dropout.py:1: \"\"\"Modality dropout: zero whole input channels during training (SPEC \u00a74.4, D-041).", "src/glioma_selective/training/modality_dropout.py:2: ", "src/glioma_selective/training/modality_dropout.py:3: A dropped modality is zeroed, never imputed. The schedule is fixed for every epoch:", "src/glioma_selective/training/modality_dropout.py:4: with probability ``keep_all_probability`` a patient keeps all four sequences,", "src/glioma_selective/training/modality_dropout.py:5: otherwise one of the 14 non-empty proper subsets of sequences is kept, chosen", "src/glioma_selective/training/modality_dropout.py:6: uniformly, and the other channels are zeroed. At least one sequence always stays.", "src/glioma_selective/training/modality_dropout.py:7: \"\"\"", "src/glioma_selective/training/modality_dropout.py:8: ", "src/glioma_selective/training/modality_dropout.py:9: from __future__ import annotations", "src/glioma_selective/training/modality_dropout.py:10: ", "src/glioma_selective/training/modality_dropout.py:11: from itertools import combinations", "src/glioma_selective/training/modality_dropout.py:12: ", "src/glioma_selective/training/modality_dropout.py:13: import numpy as np", "src/glioma_selective/training/modality_dropout.py:14: import torch", "src/glioma_selective/training/modality_dropout.py:15: ", "src/glioma_selective/training/modality_dropout.py:16: __all__ = [\"KEPT_SUBSETS\", \"apply_modality_dropout\", ... [trimmed]
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

Comparison and judgment: Every R2–R6 record enables modality_dropout with keep_all_probability=0.5. Source defines the epoch-independent schedule: keep all with probability .5; otherwise choose uniformly among 14 nonempty proper subsets. The training-loop modality-dropout test passed; at least one channel survives.

## Criterion 2: met

All six conditions implemented; masks unit-tested.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
sweep_masks ["src/glioma_selective/evaluation/condition_sweep.py:22: def modality_channel_indices(names: Sequence[str]) -> tuple[int, ...]:", "src/glioma_selective/evaluation/condition_sweep.py:23:     \"\"\"Map frozen YAML modality names to the canonical image channel indices.\"\"\"", "src/glioma_selective/evaluation/condition_sweep.py:24:     sequence_by_name = {sequence.name: sequence for sequence in CORE_SEQUENCES}", "src/glioma_selective/evaluation/condition_sweep.py:25:     unknown = set(names) - set(sequence_by_name)", "src/glioma_selective/evaluation/condition_sweep.py:26:     if unknown:", "src/glioma_selective/evaluation/condition_sweep.py:27:         raise ValueError(f\"unknown modality names: {sorted(unknown)}\")", "src/glioma_selective/evaluation/condition_sweep.py:28:     indices = tuple(CORE_SEQUENCES.index(sequence_by_name[name]) for name in names)", "src/glioma_selective/evaluation/condition_sweep.py:29:     # R-C05: the channel mapping is checked against the canonical channel order.", "src/glioma_selective/evaluation/condition_sweep.py:30:     for name, index in zip(names, indices, strict=True):", "src/glioma_selective/evaluation/condition_sweep.py:31:         assert CORE_SEQUENCES[index].name == name", "src/glioma_selective/evaluation/condition_sweep.py:32:     return indices", "src/glioma_selective/evaluation/condition_sweep.py:33: ", "src/glioma_selective/evaluation/condition_sweep.py:34: "]
mask_application ["src/glioma_selective/evaluation/condition_sweep.py:46: def _score_condition_split(", "src/glioma_selective/evaluation/condition_sweep.py:47:     model: nn.Module,", "src/glioma_selective/evaluation/condition_sweep.py:48:     dataset: Any,", "src/glioma_selective/evaluation/condition_sweep.py:49:     *,", "src/glioma_selective/evaluation/condition_sweep.py:50:     condition_id: str,", "src/glioma_selective/evaluation/condition_sweep.py:51:     zeroed_indices: Sequence[int],", "src/glioma_selective/evaluation/condition_sweep.py:52:     device: torch.device,", "src/glioma_selective/evaluation/condition_sweep.py:53:     passes: int,", "src/glioma_selective/evaluation/condition_sweep.py:54:     seed: int,", "src/glioma_selective/evaluation/
... [remaining output trimmed]
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

Comparison and judgment: All six named masks are implemented; canonical mapping is T1=0,T1CE=1,T2=2,FLAIR=3. The unit suite passed tests/unit/test_conditions.py, test_condition_sweep.py and test_modality_dropout.py, including exact tensor zeroing at the model boundary and T1CE+FLAIR-only masking.

## Criterion 3: met

**Zeroing verified; no imputation path exists anywhere in the codebase.**

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
imputation_search "src/glioma_selective/training/modality_dropout.py:3:A dropped modality is zeroed, never imputed. The schedule is fixed for every epoch:\nsrc/glioma_selective/visualization/tables.py:5:there are no imputed cells. Aggregate manifests supply counts, not demographics.\nsrc/glioma_selective/models/segresnet.py:66:    so missing-modality inputs are zeroed and never imputed (SPEC \u00a74.4).\n"
mask_application ["src/glioma_selective/evaluation/condition_sweep.py:46: def _score_condition_split(", "src/glioma_selective/evaluation/condition_sweep.py:47:     model: nn.Module,", "src/glioma_selective/evaluation/condition_sweep.py:48:     dataset: Any,", "src/glioma_selective/evaluation/condition_sweep.py:49:     *,", "src/glioma_selective/evaluation/condition_sweep.py:50:     condition_id: str,", "src/glioma_selective/evaluation/condition_sweep.py:51:     zeroed_indices: Sequence[int],", "src/glioma_selective/evaluation/condition_sweep.py:52:     device: torch.device,", "src/glioma_selective/evaluation/condition_sweep.py:53:     passes: int,", "src/glioma_selective/evaluation/condition_sweep.py:54:     seed: int,", "src/glioma_selective/evaluation/condition_sweep.py:55:     cohort: str,", "src/glioma_selective/evaluation/condition_sweep.py:56: ) -> list[dict[str, Any]]:", "src/glioma_selective/evaluation/condition_sweep.py:57:     from glioma_selective.uncertainty.mc_dropout import mc_dropout_probabilities", "src/glioma_selective/evaluation/condition_sweep.py:58: ", "src/glioma_selective/evaluation/condition_sweep.py:59:     generator = torch.Generator(device=device).manual_seed(seed)", "src/glioma_selective/evaluation/condition_sweep.py:60:     rows: list[dict[str, Any]] = []", "src/glioma_selective/evaluation/condition_sweep.py:61:     model.to(device)", "src/glioma_selective/evaluation/condition_sweep.py:62:     model.eval()", "src/glioma_selective/evaluation/conditi ... [trimmed]
dropout_source ["src/glioma_selective/training/modality_dropout.py:1: \"\"\"Modality dropout: zero whole input channels during training (SPEC \u00a74.4, D-041).", "src/glioma_selective/training/modality_dropout.py:2: ", "src/glioma_selective/training/modality_dropout.py:3: A
... [remaining output trimmed]
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

Comparison and judgment: The source/config/script search finds only statements forbidding imputation. Read the mask path and dataset.py normalization-then-zero path: channel removal assigns exact 0 after normalization; no generator/imputer is called. Synthetic forward-input tests verify zeros, rather than merely checking a mask name.

## Criterion 4: met

Full sweep complete: 6 conditions × 6 mechanisms on the internal test set.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
sweep_R1 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.7646869983948635, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8683788121990369, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.4764044943820225, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.7964686998394863, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.8719101123595505, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.7605136436597111, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "08b1efe8ec5368a189c1a950de0ae4b8690cd543", "run_id": "01M45268QDQ2CFBSPNH117MF41", "worst_single_drop": "drop_t1ce"}
sweep_R2 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.7932584269662921, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8792937399678973, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.6314606741573033, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.8728731942215088, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.878330658105939, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.7797752808988764, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "989d04978561edde89c338078cbd9d7c66ae60a8", "run_id": "01M46999FB083AX4WW0067YM13", "worst_single_drop": "drop_t1ce"}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
conformal_quantiles_cal_test [["full", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["full", "refit", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "refit", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "refit", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["drop_t1", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9516129032258065, -0.008064516129032251], ["drop_t1", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["drop_t1", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1", "refit", 0.05, 0.7519863224670393, 0
... [remaining output trimmed]
```

Comparison and judgment: The Phase 09 checker independently reconstructs 6 conditions × 6 mechanisms = 36 internal cells from R1/R2–R6 frozen predictions. The main JSON has 30 computed cells and six M6 absence markers; the companion phase09_m6_analysis.json supplies the six M6 cells under D-056. The readiness document’s “108 cells” is not the computed internal grid (F10).

## Criterion 5: met

Prediction artifacts frozen per condition with run ID, git SHA, and checkpoint hash.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
sweep_R1 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.7646869983948635, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8683788121990369, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.4764044943820225, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.7964686998394863, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.8719101123595505, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.7605136436597111, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "08b1efe8ec5368a189c1a950de0ae4b8690cd543", "run_id": "01M45268QDQ2CFBSPNH117MF41", "worst_single_drop": "drop_t1ce"}
sweep_R2 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.7932584269662921, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8792937399678973, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.6314606741573033, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.8728731942215088, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.878330658105939, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.7797752808988764, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "989d04978561edde89c338078cbd9d7c66ae60a8", "run_id": "01M46999FB083AX4WW0067YM13", "worst_single_drop": "drop_t1ce"}
sweep_R3 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.8426966292134831, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8991974317817014, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.7165329052969502, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.8975922953451043, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.9117174959871589, "has_git_sha": true, "n_test": 124, "sidecar_verified":
... [remaining output trimmed]
```

Comparison and judgment: All 36 condition parquets across R1–R6 verify their SHA-256 sidecars, contain the same UTSW calibration/test patient-label sets within run, carry run/checkpoint identifiers and Arrow git_sha, and match their condition metadata/checkpoint records. No inference or artifact overwrite was performed.

## Criterion 6: met

Per-condition conformal quantiles computed both ways (refit and carried-over) and recorded.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
conformal_quantiles_cal_test [["full", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["full", "refit", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "refit", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "refit", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["drop_t1", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9516129032258065, -0.008064516129032251], ["drop_t1", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["drop_t1", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1", "refit", 0.05, 0.7519863224670393, 0
... [remaining output trimmed]
```

Comparison and judgment: The Phase 09 checker independently recomputes all 36 condition × variant × alpha quantiles: six conditions, carried-over/refit, alpha .05/.10/.20. Each agrees with frozen JSON within 2e-6 for quantile values and exactly for empirical coverage. Carried-over uses full-input calibration; refit uses that condition’s calibration. Compared with criterion 6 and the frozen primary carried-over rule.

## Criterion 7: met

Degradation ordering is clinically plausible, or an investigation is documented.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
sweep_R2 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.7932584269662921, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8792937399678973, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.6314606741573033, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.8728731942215088, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.878330658105939, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.7797752808988764, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "989d04978561edde89c338078cbd9d7c66ae60a8", "run_id": "01M46999FB083AX4WW0067YM13", "worst_single_drop": "drop_t1ce"}
sweep_R3 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.8426966292134831, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8991974317817014, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.7165329052969502, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.8975922953451043, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.9117174959871589, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "t1ce_flair_only": {"auroc": 0.8006420545746389, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}}, "git_sha": "989d04978561edde89c338078cbd9d7c66ae60a8", "run_id": "01M4FPECM9DKAR7F6B7VFRQNC5", "worst_single_drop": "drop_t1ce"}
sweep_R4 {"checkpoint_matches": true, "conditions": {"drop_flair": {"auroc": 0.8229534510433387, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1": {"auroc": 0.8319422150882825, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t1ce": {"auroc": 0.5961476725521669, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "drop_t2": {"auroc": 0.7910112359550562, "has_git_sha": true, "n_test": 124, "sidecar_verified": true}, "full": {"auroc": 0.821669341894061, "has_git_sha": true, "n_test": 124, "sidecar_verified":
... [remaining output trimmed]
```

Comparison and judgment: drop_t1ce is the worst single drop in all five seeds, and the expected T1CE-versus-T1 ordering is present. Means from frozen parquets are full about .874 and drop_t1ce about .673. Dropping T1 can slightly improve AUROC; strict degradation of every mask is not demonstrated, but the criterion asks for plausible ordering or investigation, and the named channel-mapping sanity check passes. No rerun/tuning is warranted from this result alone.

## Criterion 8: cannot tell

Naturally-missing cases analysed separately and flagged (**D-012**, **D-008**).

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
utsw_naturally_missing {"generated_at": "2026-09-18T12:18:05.433449+00:00", "missingness": {"description": "Sequences absent from the raw cohort download; no sequence was deliberately dropped for this inventory.", "simulated": false, "source": "raw_download", "type": "naturally_occurring"}, "utsw": {"complete_patient_count": 625, "incomplete_patient_count": 0, "missing_sequence_combinations": {}, "missing_sequence_patient_counts": {"FLAIR": 0, "T1": 0, "T1ce": 0, "T2": 0}, "patient_count": 625}}
D-012 "D-012 \u2014 Naturally-missing sequences conflict with a completeness inclusion criterion\n**Status:** OPEN \u00b7 **Resolve by:** Phase 03 \u00b7 **Blocking:** yes\n\n**Conflict.** SPEC \u00a75.4 says: *\"if any UTSW/UCSF/EGD case is naturally missing a sequence ... handle it identically to the simulated-missing pipeline and flag it as a naturally-occurring instance in reporting.\"* But the missing-modality design requires **complete** four-sequence studies as the baseline condition (you cannot drop T2 from a study that never had it), and \u00a72.3 notes Elyassirad et al. imposed a complete-sequence inclusion criterion for exactly ... [remaining decision entry trimmed]
D-057 "D-057 \u2014 Does Gate E wait for EGD? (RESOLVED 2026-11-18: alternative (b))\n**Status:** RESOLVED by the Research Lead in chat on 2026-11-18 (\"leave EGD for now, it is a tough download, we will do external validation of EGD later\"), read as alternative (b). Original status was OPEN \u00b7 **Blocking:** YES (Phase 11: it fixes the BH family size, the freeze manifest contents and the Gate E criterion 9 wording)\n\n**Conflict.** The SAP lists the BH family as 44 tests with EGD and 29 without, and says its composition is to be confirmed at the freeze. `EXTERNAL_VALIDATION_PROTOCOL.md` section 5 says: if EGD is not granted by Phase 11,  ... [remaining decision entry trimmed]
```

Comparison and judgment: F02: the UTSW inventory artifact records 625 complete, zero incomplete and naturally_occurring/simulated=false; there is no UTSW natural-missingness subgroup to analyze. I did not re-inventory images or inspect any external data/labels. D-012 still says OPEN, Blocking: yes, resolve by Phase 03; its partial finding does not resolve the policy. D-057 defers EGD to an addendum but does not explicitly close D-012. Research Lead must record current-study non-applicability/closure and the future EGD policy before claiming this criterion globally met. This review does not access EGD to settle it.

## Scope limit

F02 is a decision-log closure problem for the current-study scope. The UTSW zero count is evidenced by the frozen inventory, not by a new image inventory. The external rows in the author document were not rechecked, because the user prohibited touching external data. D-008’s simulated-missingness limitation still needs publication disclosure; its Phase 14 duty is not a Phase 08 numerical test.

Next action: Research Lead resolves D-012 for the current no-EGD scope and records the deferred external duty.

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

def phase08():
 for i in range(2,7):
  r=load(i,'record.json');cfg=r['config']['training'];emit('dropout_R'+str(i),{k:cfg.get(k) for k in ['modality_dropout','modality_dropout_keep_all_probability','seed']})
 for i in range(1,7):
  r=load(i,'record.json');p=ROOT/RUNS[i-1]/'conditions';verified(p/'conditions_meta.json');meta=json.loads((p/'conditions_meta.json').read_text());out={}
  for c in CONDS:
   f=frame(i,'conditions/'+c+'.parquet');f0=frame(i,'conditions/full.parquet')
   assert list(zip(f.patient_id,f.cohort,f.label))==list(zip(f0.patient_id,f0.cohort,f0.label))
   assert (f.run_id==r['run_id']).all() and (f.checkpoint_hash==r['checkpoint_hash']).all()
   md=pq.read_metadata(p/(c+'.parquet')).metadata
   t=f[f.cohort=='utsw_internal_test'];out[c]={'n_test':len(t),'auroc':auc(t.p_hat.to_numpy(float),t.label.to_numpy(int)),'has_git_sha':b'git_sha' in md,'sidecar_verified':True}
  emit('sweep_R'+str(i),{'run_id':meta['run_id'],'git_sha':meta['git_sha'],'checkpoint_matches':meta['checkpoint_hash']==r['checkpoint_hash'],'conditions':out,'worst_single_drop':min(CONDS[1:5],key=lambda c:out[c]['auroc'])})
 inv=json.loads((paths.manifests_dir()/'naturally_missing_sequence_inventory.json').read_text())
 emit('utsw_naturally_missing',{'generated_at':inv['generated_at_utc'],'utsw':inv['cohorts']['utsw'],'missingness':inv['missingness']})
def show(tag, filename, start, end):
    lines=Path(filename).read_text().splitlines()
    emit(tag, [f"{filename}:{i+1}: {line}" for i,line in enumerate(lines) if start<=i+1<=end])
def decision(key):
    text=Path('docs/research/DECISION_LOG.md').read_text()
    sections=text.split('\n## ')
    emit(key,next(x for x in sections if x.startswith(key+' ')))

phase08()
decision('D-012');decision('D-008');decision('D-057')
show('dropout_source','src/glioma_selective/training/modality_dropout.py',1,56)
show('sweep_masks','src/glioma_selective/evaluation/condition_sweep.py',22,34)
show('mask_application','src/glioma_selective/evaluation/condition_sweep.py',46,83)
r=subprocess.run(['rg','-n','imput','src','configs','scripts'],capture_output=True,text=True)
emit('imputation_search',r.stdout)

```
