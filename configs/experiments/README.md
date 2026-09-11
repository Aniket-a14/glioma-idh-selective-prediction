# `configs/experiments/`

Named, runnable experiments. Each file here is a complete Hydra config that
overrides `configs/config.yaml`'s defaults with specific named configs from
the other groups — it does not introduce new scientific content itself, it
*selects* content that already lives in `data/`, `model/`, `training/`, etc.

```yaml
# configs/experiments/r2_modality_dropout_seed0.yaml
# @package _global_
defaults:
  - override /training: modality_dropout_seed0
  - override /model: segresnet_backbone

experiment_name: r2_modality_dropout_seed0
seed: 0
```

Run with:

```bash
python -m glioma_selective.cli.train +experiments=r2_modality_dropout_seed0
```

No experiment configs exist yet — the first ones are written alongside the
9 training runs budgeted in `docs/research/DECISION_LOG.md` D-005, starting
Phase 06. Every run recorded in `experiments/REGISTRY.md` (repo root, distinct
from this directory) names the experiment config it used.
