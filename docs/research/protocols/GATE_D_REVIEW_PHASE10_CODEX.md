# Gate D independent review — Phase 10

Date: 2026-11-18. Reviewed code: `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`.

Reviewer: Codex, independent of the phase author. **D-001 degraded solo fallback: a second agent, not a second human.** No claim is made that a human Person C reviewed or signed anything.

**Gate D verdict: HOLD — internal finality and literature verification incomplete; staged BH remains pending.** Review task status: **DONE_WITH_CONCERNS**. Acceptance counts: 8 met, 3 not met, 0 cannot tell.

Criteria source: [PHASE_10_ABLATIONS_INTERNAL_STATS.md](../phases/PHASE_10_ABLATIONS_INTERNAL_STATS.md). Author briefs/readiness tables were treated as assertions to check. The embedded read-only checker below was actually executed, exit 0, using the requested virtualenv and `PYTHONPATH=src`. Each criterion repeats its exact command; shared commands were run once, not once per repeated listing. Outputs are trimmed.

Storage was resolved through `glioma_selective.utils.paths` with `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`. Only the named UTSW run artifacts and UTSW manifest summary were used (plus R8’s explicitly referenced stage-1 record). No external image/label file was opened; the authorization flag was unset and was never assigned. No installation, training, inference, refit of the IDH model, or write to the SSD occurred. A historical “met” GPU outcome means its frozen report was checked; a new live GPU measurement is not claimed.

## Criterion 1: met

All six ablation axes complete (internal-vs-external deferred to Phase 12 by design).

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
ablation_R7 {"checkpoint_matches": true, "history_epochs": 100, "model": {"aux_segmentation": true, "blocks_down": [1, 2, 2, 4], "blocks_up": [1, 1, 1], "head_dropout": 0.2, "head_hidden": 64, "in_channels": 4, "init_filters": 32, "pooling_min_mass": 1.0, "seg_channels": 3, "tumour_aware_pooling": false}, "n_rows": 248, "status": "completed", "variant": {"label": "r7", "pos_weight": 2.5728155339805827, "variant": "whole_brain"}}
ablation_R8 {"checkpoint_matches": true, "history_epochs": 47, "model": {"aux_segmentation": true, "blocks_down": [1, 2, 2, 4], "blocks_up": [1, 1, 1], "head_dropout": 0.2, "head_hidden": 64, "in_channels": 4, "init_filters": 32, "pooling_min_mass": 1.0, "seg_channels": 3, "tumour_aware_pooling": true, "two_stage": true}, "n_rows": 248, "status": "completed", "variant": {"label": "r8s2", "pos_weight": 2.5728155339805827, "stage1_checkpoint_sha256": "9aa0b44ecae1390057da6e6b5a198f7d316b3b2bb982c2bdb5b31e659d529bdc", "stage1_run_id": "01M7ETEEYVT8KXCVJSQS5R7KJC", "variant": "stage2_cls"}}
confirmatory {"A1": {"family_member_id": "utsw:A1", "lower": -0.011952751888752217, "n": 124, "p_value": "56/667", "point": -0.004833083071467209, "status": "computed", "upper": 0.0006080761028929014}, "A2": {"family_member_id": "utsw:A2", "lower": -0.036659966783334476, "n": 124, "p_value": "1652/2001", "point": -0.00402910208518148, "status": "computed", "upper": 0.029202169924684756}, "A3": {"family_member_id": "utsw:A3", "lower": -0.032123739675673245, "n": 124, "p_value": "1862/2001", "point": 0.0008039809862857294, "status": "computed", "upper": 0.03681851456446775}, "B1": {"family_member_id": "utsw:B1", "lower": -0.01938103474797115, "n": 124, "p_value": "1970/2001", "point": 0.00034512481468966516, "status": "computed", "upper": 0.018190867077668173}, "B2": {"family_member_id": "utsw:B2", "lower": 0.2953757968410412, "n": 124, "p_value": "2/2001", "point": 0.41717145250010407, "status": "computed", "upper": 0.5433929844459943}, "B3": {"family_member_id": "utsw:B3", "lower": -0.02551583334029463, "n": 124, "p_value": "1558/2001", "point": -0.0025690026770017055, "status": "computed", "upper": 0.020396975242147848}, "B4": {"family_member_id": "utsw:
... [remaining output trimmed]
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

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
```

Comparison and judgment: The internal parts of the six axes are covered: missing vs full, calibrated vs raw, always-predict vs selective, uncertainty-method choice, R7 pooling, and R8 joint-vs-independent. Internal/external is explicitly deferred by criterion 1. Compare the Phase 09 36-cell reconstruction and Phase 10 A/B/D/E comparison IDs; no extra architecture was searched.

## Criterion 2: met

R7 and R8 trained; total training runs ≤ 9.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
ablation_R7 {"checkpoint_matches": true, "history_epochs": 100, "model": {"aux_segmentation": true, "blocks_down": [1, 2, 2, 4], "blocks_up": [1, 1, 1], "head_dropout": 0.2, "head_hidden": 64, "in_channels": 4, "init_filters": 32, "pooling_min_mass": 1.0, "seg_channels": 3, "tumour_aware_pooling": false}, "n_rows": 248, "status": "completed", "variant": {"label": "r7", "pos_weight": 2.5728155339805827, "variant": "whole_brain"}}
ablation_R8 {"checkpoint_matches": true, "history_epochs": 47, "model": {"aux_segmentation": true, "blocks_down": [1, 2, 2, 4], "blocks_up": [1, 1, 1], "head_dropout": 0.2, "head_hidden": 64, "in_channels": 4, "init_filters": 32, "pooling_min_mass": 1.0, "seg_channels": 3, "tumour_aware_pooling": true, "two_stage": true}, "n_rows": 248, "status": "completed", "variant": {"label": "r8s2", "pos_weight": 2.5728155339805827, "stage1_checkpoint_sha256": "9aa0b44ecae1390057da6e6b5a198f7d316b3b2bb982c2bdb5b31e659d529bdc", "stage1_run_id": "01M7ETEEYVT8KXCVJSQS5R7KJC", "variant": "stage2_cls"}}
R8_stage1 {"checkpoint_matches": true, "history_epochs": 214, "run_id": "01M7ETEEYVT8KXCVJSQS5R7KJC", "status": "completed", "variant": "stage1_seg"}
run_budget {"R8_stage1_is_extra_training_stage": "requires separate record in addition to 8 named configurations; inspect D-051 budget definition", "named_IDH_R1_to_R8": 8}
```

Comparison and judgment: R7 and R8 stage 2 have completed histories, verified checkpoints and 248-row prediction artifacts. The separately recorded R8 stage 1 also completed, and its actual hash matches stage 2’s stored stage1_checkpoint_sha256. D-051 explicitly counts the two R8 stages as one of eight named run-budget items; there are nine actual training stages, within the stated ≤9 even by the stricter physical-stage count.

## Criterion 3: met

Bootstrap CIs (≥1000 patient-level iterations) for AUROC, AUPRC, AURC, selective risk at fixed coverage, ECE, Brier.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
provenance {"bootstrap": "one shared patient-index matrix", "checkpoint_hash": "1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a", "ensemble_checkpoint_hashes": {"01M46999FB083AX4WW0067YM13": "1d0c53023fef56150cf8c5a026ab2854aff7b7edc0f642a94c0989df010d838a", "01M4FPECM9DKAR7F6B7VFRQNC5": "22df1ce15c960efde48e874aced97391a15e9d4fb38277424a270298d9821c40", "01M60CYFD2AYA8DCPBTDSJS4DM": "02afbabcf14bdd4e28b02e1fbd55c560210e532ac130593966ef78e9f2a9ff4c", "01M66E2KR6ZV2YPBTNPF5FD53T": "6f27df060d8b53a545890b3966ad1a0403b87b5105c090370686d0753ae22dd2", "01M776GTZC70FTB1ABD2DDMYHH": "7c8f3191d28e91db7d8ede7400c7376d0b349901566312c05be8d8796866afc1"}, "git_sha": "5b6878c0526640d49fc1ca88e6513637cddd25c4", "internal_test_patient_count": 124, "iterations": 2000, "run_id": "01M46999FB083AX4WW0067YM13", "seed": 0}
metric_CIs_R2 {"auprc": {"bootstrap_95_interval": {"lower": 0.6467972404191409, "skipped_single_class_draws": 0, "upper": 0.8841371884565147, "valid_draws": 2000}, "point": 0.7782311870661562}, "aurc_mean_over_cutoffs": {"bootstrap_95_interval": {"lower": 0.04077129449484881, "upper": 0.12297767039479833, "valid_draws": 2000}, "point": 0.07553439802055385}, "auroc": {"bootstrap_95_interval": {"lower": 0.8076105133523463, "skipped_single_class_draws": 0, "upper": 0.9386660617059891, "valid_draws": 2000}, "hanley_mcneil_95_interval": {"lower": 0.8006073739060853, "upper": 0.9560539423057928}, "point": 0.878330658105939, "quoted": "hanley_mcneil_95_interval"}, "calibration": {"M1": {"brier": {"bootstrap_95_interval": {"lower": 0.10361669464181963, "upper": 0.18092603853198203, "valid_draws": 2000}, "point": 0.13992721038099037}, "ece": {"bootstrap_95_interval": {"lower": 0.08667728962934067, "upper": 0.1903050808569359, "valid_draws": 2000}, "point": 0.11886621112725818}, "probability": "raw"}, "M2": {"brier": {"bootstrap_95_interval": {"lower": 0.10430432771820898, "upper": 0.17745656583230113, "valid_draws": 2000}, "point": 0.13871782798972945}, "ece": {"bootstrap_95_interval": {"lower": 0.09044735085912663, "upper": 0.1942063268897603, "valid_draws": 2000}, "point": 0.12216068670319964}, "probability": "temperature_scaled"}}, "selective_risk_at_co
... [remaining output trimmed]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
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

Comparison and judgment: Phase 10 stores 2,000-patient-draw intervals for AUROC/AUPRC/AURC/ECE/Brier on R2/R7/R8; Phase 09 supplies fixed-coverage selective-risk intervals for the full internal mechanism/condition grid. Person C pack was re-run and agrees on all 188 covered values; reviewer Phase 09 bootstrap covers all 180 risk intervals. Patient IDs are unique in each split, and the shared index matrix resamples patients, not independently sampled mechanisms.

## Criterion 4: met

DeLong applied to all paired AUROC comparisons on the same test set.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
confirmatory {"A1": {"family_member_id": "utsw:A1", "lower": -0.011952751888752217, "n": 124, "p_value": "56/667", "point": -0.004833083071467209, "status": "computed", "upper": 0.0006080761028929014}, "A2": {"family_member_id": "utsw:A2", "lower": -0.036659966783334476, "n": 124, "p_value": "1652/2001", "point": -0.00402910208518148, "status": "computed", "upper": 0.029202169924684756}, "A3": {"family_member_id": "utsw:A3", "lower": -0.032123739675673245, "n": 124, "p_value": "1862/2001", "point": 0.0008039809862857294, "status": "computed", "upper": 0.03681851456446775}, "B1": {"family_member_id": "utsw:B1", "lower": -0.01938103474797115, "n": 124, "p_value": "1970/2001", "point": 0.00034512481468966516, "status": "computed", "upper": 0.018190867077668173}, "B2": {"family_member_id": "utsw:B2", "lower": 0.2953757968410412, "n": 124, "p_value": "2/2001", "point": 0.41717145250010407, "status": "computed", "upper": 0.5433929844459943}, "B3": {"family_member_id": "utsw:B3", "lower": -0.02551583334029463, "n": 124, "p_value": "1558/2001", "point": -0.0025690026770017055, "status": "computed", "upper": 0.020396975242147848}, "B4": {"family_member_id": "utsw:B4", "lower": -0.008884461657644012, "n": 124, "p_value": "86/667", "point": 0.032683518308801715, "status": "computed", "upper": 0.08049222536590672}, "B5": {"family_member_id": "utsw:B5", "lower": -0.009109760014235803, "n": 124, "p_value": "236/2001", "point": 0.037920180774976456, "status": "computed", "upper": 0.08862813 ... [trimmed]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
```

Output (trimmed):

```text
83 passed in 0.73s
```

Comparison and judgment: E1 and E3 are the two pre-registered paired internal AUROC comparisons (R7−R2 and R8−R2). Both use paired DeLong on the identical 124-patient test set. Pack and independent DeLong reference tests reproduce their p-values (about .5973 and .5862); criterion 4 does not call for all possible unregistered pairs.

## Criterion 5: met

Paired bootstrap/permutation applied to all AURC and selective-risk deltas.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
confirmatory {"A1": {"family_member_id": "utsw:A1", "lower": -0.011952751888752217, "n": 124, "p_value": "56/667", "point": -0.004833083071467209, "status": "computed", "upper": 0.0006080761028929014}, "A2": {"family_member_id": "utsw:A2", "lower": -0.036659966783334476, "n": 124, "p_value": "1652/2001", "point": -0.00402910208518148, "status": "computed", "upper": 0.029202169924684756}, "A3": {"family_member_id": "utsw:A3", "lower": -0.032123739675673245, "n": 124, "p_value": "1862/2001", "point": 0.0008039809862857294, "status": "computed", "upper": 0.03681851456446775}, "B1": {"family_member_id": "utsw:B1", "lower": -0.01938103474797115, "n": 124, "p_value": "1970/2001", "point": 0.00034512481468966516, "status": "computed", "upper": 0.018190867077668173}, "B2": {"family_member_id": "utsw:B2", "lower": 0.2953757968410412, "n": 124, "p_value": "2/2001", "point": 0.41717145250010407, "status": "computed", "upper": 0.5433929844459943}, "B3": {"family_member_id": "utsw:B3", "lower": -0.02551583334029463, "n": 124, "p_value": "1558/2001", "point": -0.0025690026770017055, "status": "computed", "upper": 0.020396975242147848}, "B4": {"family_member_id": "utsw:B4", "lower": -0.008884461657644012, "n": 124, "p_value": "86/667", "point": 0.032683518308801715, "status": "computed", "upper": 0.08049222536590672}, "B5": {"family_member_id": "utsw:B5", "lower": -0.009109760014235803, "n": 124, "p_value": "236/2001", "point": 0.037920180774976456, "status": "computed", "upper": 0.08862813 ... [trimmed]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
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

Comparison and judgment: A1–A3, B1–B5, E2/E4 AURC deltas use paired patient bootstrap, as do Phase 09’s 180 selective-risk D(phi) intervals. The shared resample matrix and matched IDs were checked. Compared with SAP §§4–6 and D-052; no independent-samples test was substituted.

## Criterion 6: not met

BH correction applied across the pre-registered family; the family membership matches Phase 05 exactly.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
BH {"count": 29, "rows": [{"block": "A", "cohort": "utsw", "comparison": "AURC(M5) - AURC(M3), full", "id": "utsw:A1", "status": "computed"}, {"block": "A", "cohort": "utsw", "comparison": "AURC(M5) - AURC(M4), full", "id": "utsw:A2", "status": "computed"}, {"block": "A", "cohort": "utsw", "comparison": "AURC(M3) - AURC(M4), full", "id": "utsw:A3", "status": "computed"}, {"block": "B", "cohort": "utsw", "comparison": "AURC(M5, drop_t1) - AURC(M5, full)", "id": "utsw:B1", "status": "computed"}, {"block": "B", "cohort": "utsw", "comparison": "AURC(M5, drop_t1ce) - AURC(M5, full)", "id": "utsw:B2", "status": "computed"}, {"block": "B", "cohort": "utsw", "comparison": "AURC(M5, drop_t2) - AURC(M5, full)", "id": "utsw:B3", "status": "computed"}, {"block": "B", "cohort": "utsw", "comparison": "AURC(M5, drop_flair) - AURC(M5, full)", "id": "utsw:B4", "status": "computed"}, {"block": "B", "cohort": "utsw", "comparison": "AURC(M5, t1ce_flair_only) - AURC(M5, full)", "id": "utsw:B5", "status": "computed"}, {"block": "D", "cohort": "utsw", "comparison": "ECE(M1) - ECE(M2), full", "id": "utsw:D1", "status": "computed"}, {"block": "D", "cohort": "utsw", "comparison": "Brier(M1) - Brier(M2), full", "id": "utsw:D2", "status": "computed"}, {"block": "E", "cohort": "utsw", "comparison": "AUROC(R7) - AUROC(R2), full", "id": "utsw:E1", "status": "computed"}, {"block": "E", "cohort": "utsw", "comparison": "AURC(R7) - AURC(R2), full", "id": "utsw:E2", "status": "computed"}, {"block": "E", "cohort ... [trimmed]
independent_BH14 {"A1": 0.36101949025487257, "A2": 0.9631850741296019, "A3": 0.9845077461269364, "B1": 0.9845077461269364, "B2": 0.013993003498250875, "B3": 0.9631850741296019, "B4": 0.36101949025487257, "B5": 0.36101949025487257, "D1": 0.9347326336831584, "D2": 0.886223554889222, "E1": 0.9347326336831584, "E2": 0.9347326336831584, "E3": 0.9347326336831584, "E4": 0.36101949025487257}
D-052 "D-052 \u2014 Phase 10 statistics: the paired-bootstrap p-value and when the Benjamini-Hochberg family can be completed\n**Status:** RESOLVED 2026-11-14 (Research Lead: \"accept d-052\", recommendation (a) with (c) as a labelled supplementary table; the p-value formula was applied from the s
... [remaining output trimmed]
```

Comparison and judgment: F05: the frozen file lists exactly 29 pre-registered members: 14 computed UTSW, 15 pending external. Membership matches the confirmed no-EGD SAP family. Full-family BH has not been applied. D-052 explicitly authorizes deferring that single pass to Phase 13, so this is an approved staged exception. The labelled supplementary 14-member BH is independently reproduced and is not the 29-member correction. No external label was accessed to fill it.

## Criterion 7: met

RQ4 complete, **explicitly labelled exploratory**, wide CIs reported, no inferential claim made.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
probe {"internal_test": {"comparator_idh_bootstrap": {"auprc_95_interval": [0.2067955353254074, 0.5702428899982835], "auroc_95_interval": [0.576905762304922, 0.8460739087301586], "iterations": 2000, "skipped_single_class": 0}, "comparator_idh_probability": {"auprc": 0.33368944524170685, "auroc": 0.7142857142857143, "auroc_hanley_mcneil_half_width": 0.16453768435422192, "n": 66, "n_codeleted": 14}, "idh_mutant_only": {"comparator_idh_probability": {"auprc": 0.4100239726815357, "auroc": 0.336734693877551, "auroc_hanley_mcneil_half_width": 0.2034862023348772, "n": 28, "n_codeleted": 14}, "probe": {"auprc": 0.7630687261898441, "auroc": 0.673469387755102, "auroc_hanley_mcneil_half_width": 0.20162485802800542, "n": 28, "n_codeleted": 14}, "probe_bootstrap": {"auprc_95_interval": [0.5434020979020979, 0.9152119931196018], "auroc_95_interval": [0.4409722222222222, 0.8698383188502671], "iterations": 2000, "skipped_single_class": 0}}, "probe": {"auprc": 0.5865604399372746, "auroc": 0.7870879120879121, "auroc_hanley_mcneil_half_width": 0.15088279363610807, "n": 66, "n_codeleted": 14}, "probe_bootstrap": {"auprc_95_interval": [0.3478588630854641, 0.8218704457910485], "auroc_95_interval": [0.6274475762527233, 0.9189542932557638], "iterations": 2000, "skipped_single_class": 0}}, "label": "exploratory (RQ4, D-007); no inferential claim; a null result is not evidence of absence", "probe": {"converged": true, "model": "L2 logistic regression, C = 1, class-balanced, train-split standardization" ... [trimmed]
probe_independent {"auprc": 0.5865604399372746, "auroc": 0.7870879120879121, "frozen_objective": 75.62363252770007, "idh_mutant_auroc": 0.673469387755102, "idh_mutant_n": 28, "n_codeleted": 14, "n_test": 66, "objective": 75.62363252770642}
```

Comparison and judgment: Verified the probe JSON sidecar and independently optimized the fixed L2/class-balanced objective on frozen UTSW features: objective 75.623632527706 vs stored 75.623632527700; AUROC/AP rankings match exactly. 193 train patients/37 codeleted, 66 test/14 codeleted; all-patient AUROC .7871 with stored 95% [.6274,.9190], IDH-mutant-only .6735 with [.4410,.8698]. Frozen JSON explicitly says exploratory, no inferential claim, null is not evidence of absence. No encoder extraction/GPU rerun occurred.

## Criterion 8: met

Segmentation Dice/HD95 reported for the auxiliary task.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
segmentation_R2 {"dice": {"calibration": {"mean": 0.4749011635265176, "n_with_segmentation": 123, "n_without_segmentation": 1, "per_channel": {"enhancing": 0.44455926621895175, "necrotic_core": 0.3951960348862432, "oedema": 0.5849481894743578}}, "internal_test": {"mean": 0.47267292945834144, "n_with_segmentation": 124, "n_without_segmentation": 0, "per_channel": {"enhancing": 0.4310567952272538, "necrotic_core": 0.38962577686442385, "oedema": 0.5973362162833468}}}, "hd95_reaggregated": {"calibration": {"enhancing": {"both_empty": 0, "derived_mean_mm": 15.357496289424903, "false": 29, "missed": 0, "n_evaluable": 94, "stored_mean_mm": 15.357496289424903}, "necrotic_core": {"both_empty": 2, "derived_mean_mm": 15.023473279457459, "false": 5, "missed": 3, "n_evaluable": 113, "stored_mean_mm": 15.023473279457459}, "oedema": {"both_empty": 0, "derived_mean_mm": 17.750119400960088, "false": 0, "missed": 0, "n_evaluable": 123, "stored_mean_mm": 17.750119400960088}}, "internal_test": {"enhancing": {"both_empty": 0, "derived_mean_mm": 16.620324396892915, "false": 29, "missed": 0, "n_evaluable": 95, "stored_mean_mm": 16.620324396892915}, "necrotic_core": {"both_empty": 0, "derived_mean_mm": 12.926352416411286, "false": 3, "missed": 4, "n_evaluable": 117, "stored_mean_mm": 12.926352416411286}, "oedema": {"both_empty": 0, "derived_mean_mm": 19.45304715757846, "false": 0, "missed": 0, "n_evaluable": 124, "stored_mean_mm": 19.45304715757846}}}}
segmentation_R7 {"dice": {"calibration": {"mean": 0.4853246349711034, "n_with_segmentation": 123, "n_without_segmentation": 1, "per_channel": {"enhancing": 0.5000257913349918, "necrotic_core": 0.3871304444012663, "oedema": 0.5688176691770521}}, "internal_test": {"mean": 0.48543931789456646, "n_with_segmentation": 124, "n_without_segmentation": 0, "per_channel": {"enhancing": 0.48071011509184325, "necrotic_core": 0.4093888445017128, "oedema": 0.5662189940901433}}}, "hd95_reaggregated": {"calibration": {"enhancing": {"both_empty": 0, "derived_mean_mm": 13.261862079769172, "false": 29, "missed": 0, "n_evaluable": 94, "stored_mean_mm": 13.261862079769172}, "necrotic_core": {"both_empty": 0, "derived_mean_mm": 15.556786822157148, "false": 7,
... [remaining output trimmed]
```

Comparison and judgment: All three runs have SHA-256-verified Dice and HD95 reports. HD95 evaluable counts/means are independently reaggregated from per-patient outcomes for both splits and all channels; empty-mask counts and the separate penalty convention are explicit. Internal mean Dice: R2 .4726729295, R7 .4854393179, R8 .7409823549. Criterion requires reporting, not a new GPU segmentation pass.

## Criterion 9: met

Independent implementations agree on bootstrap, DeLong, and BH.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
independent_BH14 {"A1": 0.36101949025487257, "A2": 0.9631850741296019, "A3": 0.9845077461269364, "B1": 0.9845077461269364, "B2": 0.013993003498250875, "B3": 0.9631850741296019, "B4": 0.36101949025487257, "B5": 0.36101949025487257, "D1": 0.9347326336831584, "D2": 0.886223554889222, "E1": 0.9347326336831584, "E2": 0.9347326336831584, "E3": 0.9347326336831584, "E4": 0.36101949025487257}
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

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
```

Output (trimmed):

```text
83 passed in 0.73s
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
```

Comparison and judgment: Existing DeLong independent-midrank reference and exact bootstrap/BH fixtures pass. Pack recomputation reproduces the real-data bootstrap/DeLong values. The reviewer independently rederives all 14 supplementary BH values and all Phase 09 patient bootstrap intervals. This satisfies the agent fallback; it does not certify a named human Person C ran the pack.

## Criterion 10: not met

All internal statistics machine-readable and committed.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
hash "3d2a220c49b558a543833057514ea65f733a80f5e49aa04411fd776ffd271f54"
tracked_frozen_statistics ""
```

Comparison and judgment: F09: all internal statistics are machine-readable on the SSD with matching sidecars, but the actual phase09/phase10 result JSON files are not tracked in Git (git ls-files for their exact basenames returns empty). Repository hashes and result documents are committed. This follows the no-artifacts/data policy, but does not literally satisfy “statistics ... committed”. Resolve the acceptance wording/representation with the Research Lead; do not commit patient artifacts to force this criterion to pass.

## Criterion 11: not met

**All internal analysis is final.** Nothing internal changes after this phase.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
analysis_open_items ["docs/research/protocols/PHASE10_INTERNAL_RESULTS.md:135: ## Open for Phase 10", "docs/research/protocols/PHASE10_INTERNAL_RESULTS.md:136: ", "docs/research/protocols/PHASE10_INTERNAL_RESULTS.md:137: - Record of the runs: R7 trained to epoch 99 (best epoch 69) and had one unexplained stop after epoch 71 and resumed from epoch 72; whether that resume matches an uninterrupted run is not verified. R8 stage 1 trained about 39 h, stage 2 stopped after epoch 46. R7 HD95 was frozen with `--allow-sha-mismatch` (run git SHA `0ad683e`, current `5b6878c`), as R2's was; the model config is read from the run record.", "docs/research/protocols/PHASE10_INTERNAL_RESULTS.md:138: - T10.8: DeLong cross-check passed (1000 random cases against an independent midrank implementation); bootstrap and BH cross-checks agree on the Phase 09 fixtures; the paired-bootstrap p-value (S2, S3) was checked against an independent loop on 50 random cases.", "docs/research/protocols/PHASE10_INTERNAL_RESULTS.md:139: - Independent recomputation of every headline number by Person C (pack ready: `scripts/person_c_recompute.py` and `PERSON_C_RECOMPUTATION_GUIDE.md`; the Research Lead's run of it reproduces 188 of 188 numbers, Person C has not run it yet), Gate D review, and the single Benjamini-Hochberg pass at Phase 13."]
literature_status ["docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md:1: # Phase 10 scientific validation 3: R7 and R8 against the literature", "docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md:2: ", "docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md:3: Written 2026-11-18. Phase 10 asks that the confirmatory ablations be compared with the literature they are meant to reproduce, as a check on our implementation, not as a contribution (`PHASE_10_ABLATIONS_INTERNAL_STATS.md`, validation 3). R7 is whole-brain pooling (H1, tumour-aware pooling ablation). R8 is two-stage independent segmentation and classification (H2, joint versus independent).", "docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md:4: ", "docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md:5: **Status of the sources: search snippets only.** Two web searches on 2
... [remaining output trimmed]
```

Comparison and judgment: F11: all internal analysis cannot be certified final while the earlier phase criteria and Phase 10 scientific validation 3 remain outstanding. The literature file explicitly contains snippet-only, unverified sources under D-010. Full-family BH is also deferred by approved D-052. A second human/signature cannot be supplied by this review; the Research Lead must record acceptance/closure of the findings and the final internal freeze. No future external result can be used to retune these internal results.

## Scientific validation beyond the numbered criteria

1. Recomputed: the Person C pack gives 188/188 agreement. It was run by this independent agent under D-001, not by a second human. Its documented exclusions (Phase 09, Dice/HD95, probe, BH) were separately checked to the extent described above; no fresh GPU feature extraction or segmentation pass was run.

2. Recomputed CI-width comparison: see power_comparison output below, derived from power_check_results.json and frozen metric intervals, rather than POWER_CHECK.md numbers. AUROC bootstrap half-width about .06553, Hanley–McNeil .07772; risk half-widths about .06349–.08018. The actual AUROC uncertainty sits between simulations at true AUROC .85 and .90; some risk intervals are wider than the ideal binormal simulation. No coverage-grid change is justified by this comparison alone.

```text
power_comparison {"actual_AUROC_boot_half_width": 0.06552777417682137, "actual_Hanley_McNeil_half_width": 0.07772328419985375, "actual_risk_half_widths": {"0.5": 0.06349206349206349, "0.6": 0.07350877192982457, "0.7": 0.07418283963227784, "0.8": 0.07999999999999999, "0.9": 0.07589285714285715}, "power_configs": [{"auroc_ci_half_width": 0.0731510835582008, "auroc_true": 0.85, "coverage_grid": [0.9, 0.8, 0.7, 0.6, 0.5], "n_accepted": [111, 98, 86, 74, 62], "n_test": 123, "selective_risk_ci_half_width": [0.06995720720720713, 0.07025127551020406, 0.06914486434108524, 0.06755799549549549, 0.06528024193548392], "selective_risk_expected": [0.16357357357357358, 0.13513605442176885, 0.11096899224806196, 0.08900900900900904, 0.07134408602150553]}, {"auroc_ci_half_width": 0.05851510960727875, "auroc_true": 0.9, "coverage_grid": [0.9, 0.8, 0.7, 0.6, 0.5], "n_accepted": [111, 98, 86, 74, 62], "n_test": 123, "selective_risk_ci_half_width": [0.0627507507507508, 0.060845663265306056, 0.05664341085271308, 0.05230461711711709, 0.04662365591397859], "selective_risk_expected": [0.12411411411411422, 0.09442176870748308, 0.07077519379844942, 0.05387387387387389, 0.0388709677419356]}]}
```

3. **cannot tell**: literature validation remains snippet-only and expressly unverified under D-010. The checker reads the status directly from PHASE10_LITERATURE_SANITY_CHECK.md. I did not replace a full-text check with another snippet search. To settle it, a reviewer must open the named primary full texts, check metric/cohort definitions and controlled H1/H2 comparisons, and record which numbers/directions are verified. No source was silently upgraded to verified.

Next action: Research Lead closes the internal prerequisites and literature check, accepts or rejects the recorded wording exceptions, and retains D-052’s deferred BH pass.

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

def phase10():
 j=load(2,'phase10_analysis.json');verified(ROOT/RUNS[1]/'phase10_analysis.json');emit('hash',digest(ROOT/RUNS[1]/'phase10_analysis.json'));emit('provenance',j['provenance'])
 for i in [7,8]:
  r=load(i,'record.json');f=frame(i);emit('ablation_R'+str(i),{'status':r['status'],'variant':r['config'].get('variant',r['config'].get('run')),'model':r['config']['model'],'checkpoint_matches':digest(ROOT/RUNS[i-1]/'checkpoints/best.pt')==r['checkpoint_hash'],'history_epochs':len(r['training_history']),'n_rows':len(f)})
 for key,b in j['runs'].items():
  emit('metric_CIs_'+key,{k:v for k,v in b.items() if k in ['auroc','auprc','aurc_mean_over_cutoffs','calibration','selective_risk_at_coverage']})
 emit('confirmatory',j['confirmatory']);fam=j['bh_family'];emit('BH',{'count':len(fam),'status_counts':pd.Series([x['status'] for x in fam]).value_counts().to_dict(),'rows':fam,'supplementary':j['supplementary_bh_internal_only']})
 for i in [2,7,8]:
  d=load(i,'segmentation_dice.json');verified(ROOT/RUNS[i-1]/'segmentation_dice.json');h=load(i,'segmentation_hd95.json');verified(ROOT/RUNS[i-1]/'segmentation_hd95.json');out={}
  for split,sp in h['splits'].items():
   out[split]={}
   for ch,b in sp['per_channel'].items():
    vals=[x['value'] for x in b['outcomes'] if x['case']=='evaluable'];mean=float(np.mean(vals)) if vals else None;close(mean,b['primary']['mean']);assert len(vals)==b['primary']['n_evaluable'];out[split][ch]={'n_evaluable':len(vals),'derived_mean_mm':mean,'stored_mean_mm':b['primary']['mean'],'missed':b['missed'],'false':b['false'],'both_empty':b['both_empty']}
  emit('segmentation_R'+str(i),{'dice':d['splits'],'hd95_reaggregated':out})
 probe=load(2,'probe_1p19q/probe_1p19q.json');verified(ROOT/RUNS[1]/'probe_1p19q/probe_1p19q.json');emit('probe',probe)

 from scipy.optimize import minimize
 f=np.load(ROOT/RUNS[1]/'probe_1p19q/features.npz',allow_pickle=False);x=f['train_features'];y=f['train_label'];mu=x.mean(axis=0);sd=x.std(axis=0);sd[sd==0]=1;z=(x-mu)/sd;weights=np.where(y==1,len(y)/(2*y.sum()),len(y)/(2*(len(y)-y.sum())))
 def obj(beta):
  v=z@beta[:-1]+beta[-1];delta=weights*(expit(v)-y);return float(.5*np.sum(beta[:-1]**2)+np.sum(weights*(np.logaddexp(0,v)-y*v))),np.r_[z.T@delta+beta[:-1],delta.sum()]
 result=minimize(obj,np.zeros(z.shape[1]+1),jac=True,method='L-BFGS-B',options={'maxiter':1000,'ftol':1e-14,'gtol':1e-9})
 score=expit(((f['test_features']-mu)/sd)@result.x[:-1]+result.x[-1]);ty=f['test_label'];subset=f['test_idh_label']==1
 emit('probe_independent',{'objective':float(result.fun),'frozen_objective':probe['probe']['objective'],'n_test':len(ty),'n_codeleted':int(ty.sum()),'auroc':auc(score,ty),'auprc':ap(score,ty),'idh_mutant_n':int(subset.sum()),'idh_mutant_auroc':auc(score[subset],ty[subset])});close(auc(score,ty),probe['internal_test']['probe']['auroc']);close(ap(score,ty),probe['internal_test']['probe']['auprc'])
 from fractions import Fraction
 raw=np.array([float(Fraction(str(j['confirmatory'][k]['p_value']))) for k in j['confirmatory']]);order=np.argsort(raw);adj=np.empty(len(raw));adj[order]=np.minimum(1,np.minimum.accumulate((raw[order]*len(raw)/np.arange(1,len(raw)+1))[::-1])[::-1]);emit('independent_BH14',dict(zip(j['confirmatory'],adj)))
 for v,b in zip(adj,j['supplementary_bh_internal_only']['members']):close(v,float(Fraction(b['adjusted_p_value'])))
 # Inspect only the R8 stage-1 ID explicitly recorded in R8 stage-2, not an artifact-tree scan.
 r8=load(8,'record.json');stage=r8['config']['run']['stage1_run_id'];r=json.loads((ROOT/stage/'record.json').read_text());emit('R8_stage1',{'run_id':stage,'status':r['status'],'variant':r['config']['run']['variant'],'history_epochs':len(r['training_history']),'checkpoint_matches':digest(ROOT/stage/'checkpoints/best.pt')==r8['config']['run']['stage1_checkpoint_sha256']})

 emit('run_budget',{'named_IDH_R1_to_R8':len(RUNS),'R8_stage1_is_extra_training_stage':'requires separate record in addition to 8 named configurations; inspect D-051 budget definition'})
def show(tag, filename, start, end):
    lines=Path(filename).read_text().splitlines()
    emit(tag, [f"{filename}:{i+1}: {line}" for i,line in enumerate(lines) if start<=i+1<=end])
def decision(key):
    text=Path('docs/research/DECISION_LOG.md').read_text()
    sections=text.split('\n## ')
    emit(key,next(x for x in sections if x.startswith(key+' ')))

phase10()
decision('D-051');decision('D-052');decision('D-057')
show('family_confirmation','docs/research/protocols/BH_FAMILY_CONFIRMATION.md',1,50)
show('literature_status','docs/research/protocols/PHASE10_LITERATURE_SANITY_CHECK.md',1,45)
emit('tracked_frozen_statistics',subprocess.run(['git','ls-files','*phase09_analysis.json','*phase09_m6_analysis.json','*phase10_analysis.json'],capture_output=True,text=True).stdout)
show('analysis_open_items','docs/research/protocols/PHASE10_INTERNAL_RESULTS.md',135,145)
power=json.loads(Path('docs/research/protocols/power_check_results.json').read_text());j=load(2,'phase10_analysis.json');b=j['runs']['R2']['auroc'];ci=b['bootstrap_95_interval'];hm=b['hanley_mcneil_95_interval']
emit('power_comparison',{'actual_AUROC_boot_half_width':(ci['upper']-ci['lower'])/2,'actual_Hanley_McNeil_half_width':(hm['upper']-hm['lower'])/2,'power_configs':[x for x in power['splits']['60/20/20']['configs'] if x['auroc_true'] in [.85,.90]],'actual_risk_half_widths':{k:(v['risk_95_interval']['upper']-v['risk_95_interval']['lower'])/2 for k,v in load(2,'phase09_analysis.json')['conditions']['full']['M5']['selective_risk_at_coverage'].items()}})

```
