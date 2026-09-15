# Calibrated Selective Prediction for MRI-Based Glioma IDH Classification

Under missing MRI modalities and cross-institutional domain shift.

**Status:** see [`docs/research/PROJECT_STATE.md`](docs/research/PROJECT_STATE.md) for the current phase — that file is the live source of truth, this line is not.

---

## What this project asks

Can an MRI-based glioma IDH classifier learn to recognize **when it should not answer** — and abstain — in the two situations where medical imaging AI is known to fail: a missing MRI sequence, and a scan from a hospital the model never trained on?

This is an empirical trustworthiness study, **not a new-architecture paper**. The backbone is a standard 3D SegResNet-style MONAI encoder, deliberately boring, so that any observed failure is attributable to the selective-prediction mechanism rather than to architectural idiosyncrasy.

It is pre-registered to be able to fail. If selective prediction degrades under shift — non-monotonic risk–coverage curves, coverage collapse, calibration blow-up — that is the finding, and it is publishable.

---

## Where things are

| | |
|---|---|
| **Scientific source of truth** | [`glioma-idh-selective-prediction-research-specification.md`](glioma-idh-selective-prediction-research-specification.md) |
| **Execution source of truth** | [`docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md`](docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md) |
| **Start here** | [`docs/research/README.md`](docs/research/README.md) |
| **Phase-by-phase detail** | [`docs/research/phases/`](docs/research/phases/) |

---

## Setup

On a new machine (fresh clone, new collaborator, the GPU server), give any AI agent:

> *"Read `docs/research/prompts/SETUP_PROMPT.md` and set up the system."*

It creates the virtual environment, installs the package and git hooks, and verifies everything
CI checks — the same steps on every machine, kept current automatically as the
codebase grows. Datasets never live in this repository; they live on an external SSD reached
through the `data/` and `artifacts/` symlinks, set up by the same prompt. On Windows, run it
inside WSL2 (Ubuntu) — the prompt covers installing that too.

**Team members picking up small side-work** (not a research phase): give any AI agent

> *"Read `docs/research/prompts/CONTRIBUTOR_PROMPT.md` and pick up a task."*

It claims one bounded task from `docs/research/CONTRIBUTOR_TASKS.md`, does only that, and opens a
PR — it never touches the research phases themselves.

---

## Three things that would invalidate this project

1. **Patient-level leakage** across UTSW / UCSF-PDGM / EGD / BraTS / TCGA.
2. **Looking at external performance before Gate E** — voids claim C4 outright.
3. **Scope creep into architecture search** — the specification names this as the project's main risk.

Read [`docs/research/EXTERNAL_VALIDATION_PROTOCOL.md`](docs/research/EXTERNAL_VALIDATION_PROTOCOL.md) before touching UCSF-PDGM or EGD, and [`docs/research/DATA_GOVERNANCE_PROTOCOL.md`](docs/research/DATA_GOVERNANCE_PROTOCOL.md) before downloading anything.
