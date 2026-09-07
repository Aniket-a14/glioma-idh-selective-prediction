# Calibrated Selective Prediction for MRI-Based Glioma IDH Classification

Under missing MRI modalities and cross-institutional domain shift.

**Status:** planning complete; Phase 00 not started. No research functionality is implemented.

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

## Setup (once code exists)

```bash
cp .env.example .env          # set GLIOMA_STORAGE_ROOT to your SSD
python scripts/bootstrap_storage.py
```

Datasets never live in this repository. They live on an external SSD reached through the `data/` and `artifacts/` symlinks.

---

## Three things that would invalidate this project

1. **Patient-level leakage** across UTSW / UCSF-PDGM / EGD / BraTS / TCGA.
2. **Looking at external performance before Gate E** — voids claim C4 outright.
3. **Scope creep into architecture search** — the specification names this as the project's main risk.

Read [`docs/research/EXTERNAL_VALIDATION_PROTOCOL.md`](docs/research/EXTERNAL_VALIDATION_PROTOCOL.md) before touching UCSF-PDGM or EGD, and [`docs/research/DATA_GOVERNANCE_PROTOCOL.md`](docs/research/DATA_GOVERNANCE_PROTOCOL.md) before downloading anything.
