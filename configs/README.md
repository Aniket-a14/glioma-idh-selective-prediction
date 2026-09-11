# `configs/`

Experiments are **defined here, not in code** (`docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md`
§10). A scientific parameter hard-coded inside a `src/` module is a review-blocking
defect — it belongs in one of these YAML files instead.

## Config system

**Hydra**, with structured configs over OmegaConf. The choice, and the two
alternatives it was weighed against, are recorded in
`docs/research/DECISION_LOG.md` **D-013** — read that before changing anything
here; it is a provisional default the Research Lead confirms no later than
the Phase 05 freeze.

## Layout

```
configs/
├── config.yaml        # root composition — see its own comments
├── data/               } one directory per config group, matching a
├── preprocessing/       } src/glioma_selective/ module boundary:
├── model/                }  configs/<group>/base.yaml is always the
├── training/               }  Hydra default; named variants
├── calibration/             }  (configs/<group>/<name>.yaml) are selected
├── selective/               }  by an experiment config or a CLI override
├── evaluation/              }
└── experiments/        # named, runnable experiments — see its README.md
```

Every group directory holds a `base.yaml` placeholder as of Phase 00. Adding
real content to a group happens in the phase that owns that science (see each
`base.yaml`'s comment for which phase) — never earlier, to avoid the scope
creep the project's own risk register (R-C08) names as its main hazard.

## Composition convention

- A **group config** (`configs/<group>/<name>.yaml`) holds one coherent named
  setting for that group only — e.g. one model architecture variant, one
  training recipe. It never reaches into another group.
- An **experiment config** (`configs/experiments/<name>.yaml`) composes named
  configs from several groups via Hydra's `defaults` list, plus an
  `experiment_name` and a `seed`. It is the unit a run actually uses. See
  `configs/experiments/README.md`.
- Overrides happen through Hydra's `defaults` list or the CLI
  (`python -m glioma_selective.cli.train training=modality_dropout_seed0`),
  never by editing `base.yaml` in place once other configs depend on it.

## Ownership

`configs/` is Claude-owned (`docs/research/AGENT_WORKTREE_PROTOCOL.md` §3).
Codex proposes schema changes via a task rather than editing directly, since
config-group boundaries are a scientific-definition surface, not a tooling
one.
