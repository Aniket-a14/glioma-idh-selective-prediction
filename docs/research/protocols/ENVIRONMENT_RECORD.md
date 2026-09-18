# ENVIRONMENT RECORD

Phase 01 T01.4: `scripts/capture_environment.py` run on both machines. Raw JSON fingerprints are
the authoritative record; this file is the human-readable summary plus the scientific
comparison against SPEC §3.1/§3.5 that T01.5 exists to do.

**Both captures below predate T01.5** (dependency pinning) and T01.6 (locked install), so
`pytorch`/`monai`/`dependency_lock_hash` are correctly absent on both — this is the first,
pre-lock capture pass the phase file's own `T01.3 → T01.4 → T01.5` ordering expects, not a
mistake. A second capture pass after T01.6 will show these fields populated and matching.

## local-mac

Captured 2026-09-18, git SHA `1dd227c8673d212aaf1bf42ece3de2643f28afa3`.

| Field | Value |
|---|---|
| CPU | Apple M5 |
| RAM | 16.00 GiB |
| Free disk (repo mount) | 185.83 GiB |
| Python | 3.14.7 |
| GPU / VRAM / CUDA / driver | not available (no NVIDIA GPU — Apple Silicon) |
| PyTorch / MONAI | not installed |
| Dependency lock hash | not yet generated |

Role per `MASTER_RESEARCH_EXECUTION_PLAN.md` §12: development, CPU tests, preprocessing,
analysis, figures, writing. No GPU role expected or needed here.

## gpu-server (`home-gpu`, hostname `aniket-B450M-DS3H-V2`)

First captured 2026-09-18 pre-lock (git SHA `1dd227c8...`); re-captured post-T01.5/T01.6
(git SHA `83f98e8950c36df65aa27479071ea526b278f1a4`) with the environment actually installed:

| Field | Value |
|---|---|
| CPU | AMD Ryzen 5 5600G with Radeon Graphics |
| RAM | 15.48 GiB |
| Free disk (`/data`, `GLIOMA_STORAGE_ROOT` target) | 228.45 GiB (post-install) |
| Python | 3.12.3 |
| GPU | NVIDIA GeForce RTX 2060 SUPER |
| VRAM | **8192 MiB (8 GB)** |
| Driver | 595.84 |
| CUDA (driver max / PyTorch build) | 13.2 / 13.0 |
| `torch.cuda` capability | 7.5 (matches Turing, matches installed build — acceptance criterion 7) |
| PyTorch / MONAI | 2.14.0 / 1.6.0 |
| Dependency lock hash | `aee7b75e361fe46177dc5bcf535ea7aec02f0c21a89bb8a1ecc8e7ada6c42007` — **identical to local-mac** (acceptance criterion 5) |

`GLIOMA_STORAGE_ROOT=/data/glioma-idh/storage`, `GLIOMA_MACHINE=gpu-server`. Repo checkout at
`/data/glioma-idh/repo`, venv at `/data/glioma-idh/venv`. `bootstrap_storage.py` run twice
(idempotent, acceptance criterion 1) — `data/`/`artifacts/` symlinks confirmed.

## T01.5 — measured hardware vs. SPEC §3.1/§3.5

**This is the genuine gate the phase file names it as, not a formality — see `DECISION_LOG.md`
D-017.** Both VRAM and RAM measured on the only GPU-bearing machine are below the specification's
stated envelope:

| | SPEC target | Measured | |
|---|---|---|---|
| VRAM (§3.1) | 16–24 GB | **8 GB** | half the floor |
| RAM (§3.5) | ≥32 GB | **15.48 GB** | well under half |

This is exactly the failure condition `PHASE_01_INFRASTRUCTURE.md` names explicitly ("Measured
VRAM < 16 GB (triggers a specification-checked accommodation decision)") and one of the phase's
own listed "Decisions requiring Research Lead approval" ("patch size if the benchmark forces a
change from 128³ · whether cloud GPU fallback is provisioned now or deferred"). See D-017 for the
full analysis and options — this is not resolved by this record alone, it requires Research Lead
sign-off before Phase 06 (first real training) can proceed.

## T01.7 — GPU memory benchmark (home GPU server, RTX 2060 SUPER, 8 GB)

**Explicitly a smoke-test benchmark, not the Phase 06 sizing decision** — see D-017's 2026-09-18
update: NVIDIA Labs A100 access is the real Phase 06 training environment, still unscheduled.
This benchmark exists because Phase 01's acceptance criteria require it and because it's still
useful for the CPU/toy-scale pre-training-authorization steps (master plan §12, steps 2–4) that
don't need A100-class hardware.

Method: `SegResNet` (`spatial_dims=3, in_channels=4, out_channels=2, init_filters=16`, MONAI
1.6.0), one forward + backward pass + optimizer step per cell, random input tensors, fp32, peak
VRAM via `torch.cuda.max_memory_allocated`. Not the full training pipeline (no augmentation, no
`DataLoader` overhead, no mixed precision) — a lower bound on real usage, not an exact prediction.

| Patch | Batch | Peak VRAM | Status |
|---|---|---|---|
| 96³ | 1 | 1004.6 MiB | ok |
| 96³ | 2 | 1994.0 MiB | ok |
| 128³ | 1 | 2340.5 MiB | ok |
| 128³ | 2 | 4662.0 MiB | ok |

**Finding: all four cells fit comfortably within 8 GB**, including 128³ at batch 2 (4.66 GB peak,
~3.5 GB headroom before the OOM ladder in `RECOVERY_RUNBOOK.md` §2 would even be needed). This is
more headroom than D-017's original framing assumed — the core backbone at SPEC §4.2's target
patch sizes was never actually going to be the tight constraint on this card; real training-loop
overhead (data loading, augmentation, larger effective batch via accumulation) is the more likely
source of any future OOM, not the bare model. Still not a substitute for A100 access at Phase 06 —
`init_filters=16` is a moderate configuration, and the full joint-training/ensemble setups (SPEC
§4.6, D-005's 9-run budget) were never sized for an 8 GB card in the first place.

## Storage layout note (cross-reference D-014)

`GLIOMA_STORAGE_ROOT` differs by machine, as `.env.example` already anticipates:
- local-mac: `/Volumes/Research_2` (external SSD), with `data/external` symlinked to
  `/Volumes/Research_1` (second external SSD) — see D-014.
- gpu-server: `/data` (233.83 GB free, a local NVMe partition, not removable media) — this
  machine's repo checkout lives at `/data/glioma-idh/repo`.

## GPU-server access note

The GPU server's root filesystem (`/`) was found at 100% full during this capture (a single
runaway `/var/log/syslog.1`, 28 GB, unrelated to this project — deleted with Research Lead
sign-off). An unrelated project's directory (`/data/cancer-rg`, PET-CT lung cancer staging) was
also found on `/data` and removed with Research Lead sign-off; this project's checkout now lives
at the dedicated `/data/glioma-idh/`. Repo access from the GPU server uses a read-only GitHub
deploy key (`~/.ssh/glioma_deploy_key` on that machine), registered specifically for this
purpose — not a broad personal credential.
