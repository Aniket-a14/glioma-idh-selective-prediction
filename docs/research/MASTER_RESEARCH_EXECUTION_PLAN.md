# MASTER RESEARCH EXECUTION PLAN

**Project:** Calibrated Selective Prediction for MRI-Based Glioma IDH Classification under Missing Modalities and Cross-Institutional Domain Shift
**Status:** Plan approved; Phase 00 not yet started
**Plan version:** 1.0
**Scientific source of truth:** `glioma-idh-selective-prediction-research-specification.md` (hereafter **SPEC**)
**Engineering source of truth:** this document
**Authority:** the SPEC governs *what* is being asked; this plan governs *how* it is executed. Where this plan appears to change the science, that is a bug — file it in `DECISION_LOG.md`.

---

## 1. Executive summary

This project asks whether a glioma IDH classifier that is allowed to say **"I don't know"** actually becomes more trustworthy in the two situations where MRI-based AI is known to fail: when an MRI sequence is missing, and when the scan comes from a hospital the model never trained on.

It is deliberately **not** an architecture paper. The backbone is a standard 3D SegResNet-style MONAI encoder, chosen because it is boring, well-validated, and cheap — so that any observed failure can be attributed to the *selective-prediction mechanism* rather than to architectural idiosyncrasy. The contribution is empirical: a systematic risk–coverage characterization (selective risk, AURC, monotonicity, empirical-vs-nominal conformal coverage) across a 2×2 design of {complete, missing modalities} × {internal, external}.

The project is **pre-registered to be able to fail**. SPEC §1.4 fixes six falsifiable claims, each paired with the result that would refute it. If selective prediction degrades under shift — non-monotonic risk–coverage curves, coverage collapse, calibration blow-up — that is the finding, and it is publishable. The plan's job is to make it structurally difficult to quietly convert a negative result into a positive one.

Three failure modes would invalidate the entire study, and most of this plan's machinery exists to prevent them:

1. **Patient-level leakage** across UTSW / UCSF-PDGM / EGD / BraTS / TCGA. UCSF-PDGM has a *documented* partial overlap with BraTS-2021 and ships an ID-mapping file precisely so it can be removed.
2. **Peeking at external performance.** A single early "sanity check" on UCSF-PDGM or EGD voids claim C4 outright. This is enforced by Gate E, an environment flag, and a repository-level firewall — procedurally *and* technically.
3. **Scope creep into architecture search.** The SPEC's own closing line: *"the risk in this project is scope creep, not insufficient novelty."*

Execution runs across **16 phases** (00 genesis → 15 publication) with six quality gates. Two coding agents (Claude, Codex) work in non-overlapping git worktrees under a Research Lead who owns all merges into `main`. The plan is sized for three active people but every collaborator task carries a documented solo fallback, and the critical path is published in both forms.

---

## 2. Frozen scientific objective

> **"This project provides the first systematic risk–coverage analysis and empirical coverage characterization of inference-time calibrated selective prediction for MRI-based glioma IDH classification, testing — rather than assuming — whether abstaining on low-confidence cases genuinely improves reliability, and whether conformal coverage remains close to nominal, under missing MRI sequences and cross-institutional domain shift."**
> — SPEC §8.3, verbatim. This sentence is frozen. It may not be widened.

Formally (SPEC §1.2): for a possibly incomplete study `x = (x_T1, x_T1CE, x_T2, x_FLAIR)` and IDH status `y ∈ {0,1}`, we study a selective classifier `(f, g)` where `f(x) → p̂(y=1|x)` is a calibrated probability estimator and `g(x) → {0,1}` is a rejection function. Coverage `φ = E[g(x)]`. Selective risk `R(f,g) = E[ℓ(f(x),y)·g(x)] / E[g(x)]`. The risk–coverage curve traces `R(f,g_τ)` as the rejection threshold `τ` sweeps; **AURC** is its integral.

Standard conformal guarantees rest on exchangeability between calibration and test data. Domain shift and missingness are known to violate it. **We do not assume the guarantee holds.** The extent and pattern of coverage deviation *is the object of study*.

---

## 3. Research questions

Verbatim from SPEC §1.3.

- **RQ1 (primary).** Under missing MRI sequences and under cross-institutional domain shift, does a calibrated selective-prediction mechanism (conformal risk control, compared against temperature scaling and MC-dropout) produce a well-behaved risk–coverage trade-off — i.e., does rejecting low-confidence cases genuinely and monotonically lower selective risk and AURC relative to an always-predict baseline?
- **RQ2 (primary).** Does empirical coverage remain close to nominal coverage under missing modalities and cross-institutional domain shift, and how does violation of the exchangeability assumption affect coverage? This is treated strictly as an open empirical question — conformal guarantees are not assumed to hold under shift or missingness; the goal is to characterize whether and how they degrade, not to confirm that they survive.
- **RQ3 (secondary).** Does calibration (ECE, Brier score, reliability) degrade from internal to external evaluation for MRI-based IDH classification in this specific dataset combination (UTSW → UCSF-PDGM/EGD), replicating or contradicting the degradation reported elsewhere (e.g., GliomaVista-IDH external Brier 0.32)?
- **RQ4 (exploratory, secondary endpoint).** Does the same selective-prediction behavior hold for 1p/19q codeletion, given its smaller label count, or must conclusions there be reported only as exploratory with wide confidence intervals?

---

## 4. Falsifiable claims

Verbatim from SPEC §1.4. **The right-hand column is load-bearing** and may not be dropped, softened, or renegotiated after results are seen.

| # | Claim | Result that would prove it WRONG |
|---|---|---|
| C1 | Selective prediction (conformal) achieves lower selective risk at matched coverage than an always-predict baseline, internally. | Selective risk at any fixed coverage ≥ always-predict risk; risk–coverage curve is flat or increasing as coverage decreases. |
| C2 | Selective prediction preserves this advantage under missing modalities. | Selective-risk advantage over always-predict disappears or reverses when 1–2 sequences are dropped. |
| C3 | Selective prediction preserves this advantage under external (cross-institutional) shift. | No selective-risk advantage on UCSF-PDGM/EGD relative to always-predict, at matched coverage. |
| C4 | The magnitude and direction of any deviation between empirical and nominal coverage under domain shift and missingness can be measured and characterized (e.g., against a pre-registered tolerance band such as ±5 percentage points), without presupposing whether coverage holds or degrades. | The deviation cannot be reliably characterized — e.g., empirical coverage estimates are too noisy/unstable (given sample size) to distinguish "coverage preserved" from "coverage degraded" at the pre-registered tolerance. |
| C5 | Risk–coverage curves remain monotonic (rejecting less-confident cases never increases risk) across all four evaluation conditions. | Curves become non-monotonic under shift/missingness, mirroring documented failures in retinal/CXR imaging. |
| C6 | Abstention rate correlates with actual error rate (uncertain cases are disproportionately the wrong ones). | Abstained cases are no more likely to be erroneous than randomly selected cases of equal size. |

> **C4 is not yet falsifiable.** The SPEC offers "±5 percentage points" only as an example ("such as"). The tolerance band must be frozen to a specific number in **Phase 05**, before any external data is touched. See **D-004**.

**Negative results are valid results.** No experiment may be re-run, re-tuned, or re-scoped because its outcome refutes a claim. Refutations are recorded in `paper/NEGATIVE_RESULTS.md` as they occur and reported in the manuscript.

---

## 5. Novelty boundary

**Exhausted — NOT available as novelty claims** (SPEC §8.1, verbatim list): generic glioma detection; generic IDH classification from MRI; CNN-based classification; Transformer-based classification; CNN–Transformer hybrid architectures; multimodal MRI fusion; tumor-aware/ROI-aware learning; uncertainty estimation (as a reported number); calibration (as a reported number); missing-modality robustness (as an always-predict property); external validation (as a single-cohort test); joint segmentation+molecular-classification multi-task learning.

**The surviving gap** (SPEC §8.2): no paper performs inference-time calibrated selective prediction/abstention for MRI-based glioma IDH classification, formally characterized via risk–coverage/AURC analysis, evaluated jointly under **both** missing MRI modalities **and** genuine cross-institutional domain shift, with explicit empirical measurement of how close empirical coverage remains to nominal — without assuming in advance that the guarantee either holds or degrades.

**Mandatory differentiation targets.** Every manuscript draft must explicitly position against:

| Work | What it has | What it lacks — our wedge |
|---|---|---|
| **GMMAS** (Liu et al. 2026) | Joint learning, missing-modality, MC-dropout uncertainty, ECE curves, external cohort | Uncertainty used **only** for training-time pseudo-label filtering; never gates an inference-time decision. No abstention, no risk–coverage, no coverage test. |
| **Elyassirad et al. 2026** | Conformal abstention, IDH, UCSF→UPenn shift | **Single fixed operating point** (τ=0.01). No risk–coverage sweep, no AURC, no missing-modality axis, no ECE/Brier. *The most dangerous paper for our novelty.* |
| **Yogananda et al. 2025** | Calibrated confidence (Brier 0.0125), same dataset family incl. UTSW/UCSF/EGD | Never abstains. Missing-modality listed as its own unaddressed limitation. No risk–coverage. Differentiation must be on **mechanism**, not data. |
| **RISEN** (Liang et al. 2026) | Missing-modality via imputation, multi-institution | Always predicts after imputing. Our contrast: zero-and-possibly-abstain vs. impute-and-always-answer. |
| **FoundBioNet** (MICCAI 2025) | Tumor-aware foundation backbone, strongest external AUCs | No uncertainty, no calibration, no missing-modality. Cite as the discrimination ceiling we approach, not beat. |

---

## 6. Scope and non-scope

**In scope.** IDH mutation classification (primary endpoint). Post-hoc calibration. Four uncertainty/selective mechanisms. Systematic missing-modality evaluation by channel zeroing. Frozen external validation on UCSF-PDGM and EGD. Risk–coverage/AURC analysis. Patient-level bootstrap statistics. 1p/19q as an explicitly-labelled exploratory secondary analysis. Auxiliary tumor segmentation head as a *confirmatory* component.

**Explicitly out of scope — do not add without a SPEC amendment.**

| Excluded | Reason |
|---|---|
| **MGMT prediction** | Kim et al. 2022: 337/420 model variants not significantly different from chance; BraTS-2021 winner dropped to AUROC 0.562 externally. Adding it *weakens* the paper. |
| **Architecture search / backbone variants** | SPEC §4.1. Consumes the budget that is the actual contribution. |
| **Swin-UNETR / foundation-model backbone** | Optional robustness check *only if time permits*; not planned, not budgeted. |
| **2D or single-slice models** | The 2×2 design requires true 3D four-sequence volumes. |
| **Modality imputation** | Would conflate the missing-modality question with an imputation-quality question. Zeroing only. |
| **BraTS pretraining** | Recommended default: **none**. Removes an entire leakage class. See **D-011**. |
| **New uncertainty methods** | The four in SPEC §4.6 are the set. |
| **Prospective/clinical deployment claims** | Retrospective, non-interventional. CONSORT-AI/SPIRIT-AI do not apply. |

---

## 7. Datasets and their exact roles

> **All counts below are PROVISIONAL.** SPEC §9 step 1 explicitly instructs that per-marker counts be verified by parsing the actual clinical-metadata files and *not* trusted from the specification document. Phase 03 replaces every number here with a verified, hashed manifest. See **D-009**.

| Cohort | Role | n (provisional) | Access | Hard constraints |
|---|---|---|---|---|
| **UTSW-Glioma** | **PRIMARY — the only development cohort.** Train / calibration / internal test. | 625 patients; IDH n=622 (176 mut / 446 wt); 1p19q n=335 (63 / 272) | Open, TCIA. DOI 10.7937/dfae-1b86 | Everything — hyperparameters, thresholds, normalization stats, model selection, calibration — is fitted here and **only** here. |
| **UCSF-PDGM** | **EXTERNAL TEST.** Touched once, at Phase 12. | 501; IDH ~all; 1p19q 410/501 | Open, TCIA. DOI 10.1148/ryai.220058 | **Documented BraTS-2021 overlap.** Ships a BraTS-2021 ID-mapping file. Overlapping IDs MUST be removed before it counts as external. Grade skewed ~80% grade IV. |
| **EGD** | **EXTERNAL TEST.** Touched once, at Phase 12. | 774; IDH n=467; 1p19q n=259 | **DUA via Health-RI** (servicedesk@health-ri.nl). XNAT access alone insufficient. | **Weeks of lead time — initiate on day 1 of Phase 02.** Longest non-compute dependency in the project. |
| **LGG-1p19qDeletion** | Optional exploratory 1p/19q check only | 159; 102 codel / 57 not | Open, TCIA | **3 axial slices per patient, T1C+T2 only.** Cannot enter the 3D pipeline. Cannot support missing-modality experiments. No IDH labels. |
| **UPENN-GBM** | Optional supplementary external check | 630 (611 pre-op) | Open, TCIA | GBM-only ⇒ IDH almost entirely wildtype. Must be flagged as heavily imbalanced if used. |
| **BraTS 2021/23/24** | **LEAKAGE SOURCE — exclude from, never train on** | — | Open (registration) | Embeds TCGA-GBM (135) and TCGA-LGG (108) under identical subject IDs. |
| **TCGA-GBM / TCGA-LGG** | **LEAKAGE SOURCE** | — | — | Rejected as training or external cohort. Actively excluded from. |
| IvyGAP, RHUH-GBM | **Rejected** | ~39, ~40 | — | Too small to add power. |

**Overlap audit matrix (Phase 03).** Every cell must be computed and its result recorded, even when empty:

```
                BraTS-2021   TCGA-GBM   TCGA-LGG   UCSF-PDGM   EGD
UTSW-Glioma         ?            ?          ?          ?         ?
UCSF-PDGM      MUST RESOLVE      ?          ?          —         ?
EGD                 ?            ?          ?          ?         —
```

---

## 8. Scientific invariants

Immutable unless the Research Lead amends the SPEC in writing. Each is testable; each maps to enforcement machinery.

| ID | Invariant | Enforced by |
|---|---|---|
| **SI-01** | Primary endpoint is IDH mutation classification. | Config schema rejects unknown endpoints |
| **SI-02** | 1p/19q is exploratory/secondary only, and only if statistical support survives exclusions. | Phase 05 power check; manuscript labelling |
| **SI-03** | MGMT is not a project endpoint. | Config schema; CI grep for `mgmt` outside the exclusion rationale |
| **SI-04** | UTSW-Glioma is the only development cohort. | Split module refuses non-UTSW input |
| **SI-05** | UCSF-PDGM and EGD are external test sets and never development sets. | Gate E + `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` |
| **SI-06** | UCSF-PDGM's BraTS-2021 overlap is resolved before it counts as independent. | Phase 03 exclusion manifest hash |
| **SI-07** | All splitting is patient-level, after de-duplication. | Unit tests on split module; leakage regression test |
| **SI-08** | No external performance may influence tuning, thresholds, normalization, model selection, calibration, or checkpoint choice. | Gate E; firewall module; audit log |
| **SI-09** | Missing modalities are **zeroed**, never imputed. | Unit test; config schema forbids imputation |
| **SI-10** | Normalization statistics come from the UTSW **training split only**. | Unit test; stats artifact is hashed and frozen |
| **SI-11** | No architecture search. SegResNet-style backbone is fixed. | Non-scope list; PR review checklist |
| **SI-12** | Auxiliary segmentation / tumor-aware pooling is confirmatory, not the novelty claim. | Manuscript framing review |
| **SI-13** | Negative results are preserved and reported. | `paper/NEGATIVE_RESULTS.md`; results freeze at Gate F |
| **SI-14** | AUROC is never reported without ECE/Brier/AURC/coverage alongside. | Table-generation module refuses to emit AUROC alone |
| **SI-15** | Reporting follows TRIPOD+AI and CLAIM 2024, re-checked for updates immediately before submission. | Phase 14 checklist artifacts |

---

## 9. System architecture

```
                    ┌──────────────────────────────────────────────┐
                    │  UTSW-Glioma (DEVELOPMENT — the only one)    │
                    └───────────────────┬──────────────────────────┘
                                        │  patient-level, stratified
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                     TRAIN         CALIBRATION     INTERNAL TEST
                        │               │               │
        ┌───────────────┘               │               │
        ▼                               │               │
  normalization stats ──────────────────┼───────────────┼──────────┐
        │                               │               │          │
        ▼                               │               │          │
  ┌───────────────────────────┐         │               │          │
  │ 3D SegResNet-style encoder│         │               │          │
  │  4 channels (T1,T1CE,     │         │               │          │
  │   T2,FLAIR), 96³/128³     │         │               │          │
  │  + classification head    │         │               │          │
  │  + aux segmentation head  │         │               │          │
  │  + tumor-aware pooling    │         │               │          │
  │  modality dropout @train  │         │               │          │
  └────────────┬──────────────┘         │               │          │
               │  frozen checkpoint     │               │          │
               ▼                        ▼               │          │
        ┌────────────────────────────────────────┐      │          │
        │ CALIBRATION / UNCERTAINTY (post-hoc)   │      │          │
        │  temperature T, MC-dropout, ensemble,  │      │          │
        │  conformal quantile q̂                  │      │          │
        └────────────┬───────────────────────────┘      │          │
                     │ frozen params                    │          │
                     ▼                                  ▼          │
              ┌──────────────────────────────────────────────┐     │
              │ SELECTIVE LAYER  g(x): accept / abstain      │     │
              └──────────────────┬───────────────────────────┘     │
                                 ▼                                 │
              ┌──────────────────────────────────────────────┐     │
              │ PREDICTION ARTIFACTS (frozen .parquet)       │     │
              │ per patient × mechanism × condition          │     │
              └──────────────────┬───────────────────────────┘     │
                                 ▼                                 │
              ┌──────────────────────────────────────────────┐     │
              │ ANALYSIS — recomputed from artifacts, never  │     │
              │ by re-running the model. RC curves, AURC,    │     │
              │ coverage, bootstrap CIs, DeLong, BH          │     │
              └──────────────────┬───────────────────────────┘     │
                                 ▼                                 │
                            figures / tables                       │
                                                                   │
  ╔════════════════════ GATE E FIREWALL ════════════════════════╗  │
  ║  UCSF-PDGM (BraTS-dedup'd)   EGD (DUA)                      ║◄─┘
  ║  Operational access (download, integrity, dedup, preprocess)║
  ║  is permitted from Phase 02. LABEL/METRIC access is blocked ║
  ║  until the Research Lead signs Gate E, once, in Phase 11.   ║
  ╚═════════════════════════════════════════════════════════════╝
```

**Load-bearing property:** the model is run **once** per (checkpoint × cohort × modality condition) and its per-patient outputs are frozen to disk. Every mechanism comparison, threshold sweep, bootstrap, and figure is recomputed from those frozen artifacts. This makes analysis cheap, reproducible, and — critically — makes it impossible to "accidentally" re-tune by re-running the model.

---

## 10. Repository architecture

```
.
├── .github/workflows/          # CI: gate A + gate B
├── configs/                    # experiments are DEFINED here, not in code
│   ├── data/ preprocessing/ model/ training/
│   ├── calibration/ selective/ evaluation/ experiments/
├── docs/research/              # ← this planning corpus
│   ├── phases/ protocols/ decisions/
├── src/glioma_selective/
│   ├── cli/            # thin entry points; NO logic
│   ├── data/           # dataset adapters (one per cohort, isolated)
│   ├── leakage/        # overlap audit, ID normalization, exclusion manifests
│   ├── preprocessing/  # registration, skull-strip, N4, resample, normalize
│   ├── splits/         # patient-level stratified splitting, frozen + hashed
│   ├── models/         # SegResNet-style backbone, heads, pooling
│   ├── training/       # loop, checkpointing, resume, AMP, modality dropout
│   ├── calibration/    # temperature scaling, conformal quantiles
│   ├── uncertainty/    # MC-dropout, deep ensemble
│   ├── selective/      # g(x), risk–coverage, AURC, coverage deviation
│   ├── evaluation/     # metrics; NO plotting imports
│   ├── statistics/     # bootstrap, DeLong, permutation, BH
│   ├── visualization/  # figures; imports evaluation, never the reverse
│   ├── tracking/       # run records, hashes, MLflow adapter
│   └── utils/          # paths (THE canonical path abstraction), seeding, io
├── tests/{unit,integration,regression,fixtures}
├── scripts/            # call package APIs; never duplicate logic
├── notebooks/          # exploration only; never canonical
├── experiments/        # generated run outputs (gitignored beyond manifests)
├── paper/{figures,tables,checklists,bibliography}
├── data/       -> symlink to $GLIOMA_DATA_ROOT      (gitignored)
├── artifacts/  -> symlink to $GLIOMA_ARTIFACT_ROOT  (gitignored)
└── pyproject.toml .pre-commit-config.yaml .env.example .gitignore README.md
```

**Architectural rules.**
- Reusable scientific logic lives under `src/`. Scripts and notebooks call it; they never reimplement it.
- `evaluation/` must not import `visualization/`. Metrics are testable without a display.
- `statistics/` is isolated from model code — it operates on frozen prediction tables only.
- Dataset-specific quirks live in `data/adapters/<cohort>.py` and must not leak into generic pipeline code.
- `utils/paths.py` is the **only** module permitted to resolve filesystem roots. A CI check greps for `/Volumes/`, `/mnt/`, and `../../data` elsewhere.

---

## 11. Storage architecture

Datasets live on an external SSD; the repository never contains MRI data.

```
$GLIOMA_STORAGE_ROOT/
├── data/
│   ├── raw/          # as-downloaded, read-only after checksum. NEVER modified.
│   ├── external/     # UCSF-PDGM, EGD — firewalled
│   ├── interim/      # partial preprocessing output (resumable)
│   ├── processed/    # deterministic preprocessing output, content-addressed
│   ├── manifests/    # cohort/exclusion/split manifests + hashes (also in Git)
│   └── private/      # DUA-restricted metadata. NEVER committed, never synced.
└── artifacts/
    ├── cache/        # regenerable; safe to delete
    ├── checkpoints/  # model weights
    ├── experiments/  # run records
    ├── predictions/  # FROZEN per-patient outputs — the analysis substrate
    ├── figures/ logs/ mlflow/
```

`scripts/bootstrap_storage.py` (Phase 01) creates `data/` and `artifacts/` symlinks from `GLIOMA_STORAGE_ROOT`. It must be **idempotent**, refuse dangerous overwrites, verify targets exist, report broken symlinks clearly, and work on both macOS and the Linux GPU server. No machine-specific absolute path is ever committed.

**Retention policy.** Augmentation is performed **online** — augmented volumes are never persisted. Persist: raw (permanent), processed (permanent, content-addressed), manifests (permanent, in Git), checkpoints (permanent for frozen runs; dev runs pruned after 30 days), predictions (permanent — these *are* the results), cache (disposable).

---

## 12. Local / GPU execution architecture

Two environments, **one source tree**, reached by `git` + a locked environment + configs. No divergent copies.

| | Local (macOS) | Remote GPU server |
|---|---|---|
| Role | Development, CPU tests, preprocessing, analysis, figures, writing | Training, GPU inference |
| Data | Full raw + processed on external SSD | Processed cohorts only, subject to DUA check |
| Runs | unit tests, smoke tests, statistics, plots | pilot / final / ablation / frozen-external |

**Hardware is not assumed.** SPEC §3.1 targets 16–24 GB VRAM, but actual VRAM, CUDA version, driver, RAM, disk, and PyTorch/MONAI compatibility are **unknown** and must be captured in Phase 01 before any training is planned in detail. `scripts/capture_environment.py` records: `nvidia-smi`, GPU model, VRAM, CUDA runtime, driver, CPU, RAM, free disk, Python/PyTorch/MONAI versions, `torch.cuda` capability, git SHA, environment lock hash.

**Pre-training authorization sequence (Phase 06, all seven required, in order):**
1. CPU unit tests pass → 2. one-sample data test → 3. tiny-batch forward pass → 4. tiny overfit test (loss → ~0 on 4 patients) → 5. GPU memory benchmark at target patch size → 6. checkpoint save/resume equivalence test → 7. deterministic/config logging test.

Only then may an expensive run be authorized.

**Recovery.** All long runs are launched under `tmux`/`nohup` so SSH disconnect is survivable. Checkpoint every epoch plus a `last.ckpt`; resume is a tested code path, not an aspiration. CUDA OOM → documented fallback ladder (reduce patch size → gradient accumulation → reduce batch), and any such change is recorded as a deviation and checked against the SPEC rather than silently applied. Preprocessing is resumable and content-addressed, so an interrupted run re-does only what is missing.

**Data transfer.** Only preprocessed, de-identified, non-DUA-restricted cohorts may be synced to the GPU server, and only after the licensing/DUA terms for that specific cohort are checked and recorded. EGD terms must be read before EGD touches any second machine. `data/private/` is never synced.

---

## 13. Team model

Nominal team of six; **the project must be completable by three**, and every collaborator task carries a solo fallback so it survives if collaborators go inactive.

| Person | Role | Owns |
|---|---|---|
| **A** | Research Lead / Main Developer | Repository, scientific integration, final technical decisions, all merges to `main`, frozen experiments, Gate E authorization, reproducibility, manuscript integration. Operates Claude and Codex. |
| **B** | Data / Validation Contributor | Dataset acquisition and documentation, metadata verification, access tracking, patient-ID auditing, manual image/preprocessing QC, exclusion verification, manifest verification, independent result checking. |
| **C** | Research / Evaluation Contributor | Literature and reference maintenance, statistical-result verification, table verification, reporting-checklist maintenance, result auditing, figure/table validation, manuscript and reproducibility support. |
| **D–F** | Optional support | Documentation, manual verification, proofreading, supplementary work. **Never on the critical path.** |

**Solo-degradation rule.** Every task assigned to B or C records `solo_fallback: <executor> (+N days)`. Where the fallback is "A + Codex", an *independent-implementation* check substitutes for the second pair of human eyes: Codex reimplements the calculation from the specification text alone and the two results must agree. This is weaker than human review for judgement tasks (visual MRI QC, label-definition adjudication) — those are marked `solo_fallback: A (+N days), DEGRADED` and are called out in the Limitations section if executed solo.

---

## 14. Claude / Codex orchestration model

Both agents are used heavily. **They never own the same file at the same time.**

| | Claude | Codex |
|---|---|---|
| Strength | High-context reasoning, cross-module design, scientific judgement | Bounded, well-specified, testable implementation |
| Owns | System architecture, model architecture, calibration/selective design, phase planning, interface design, protocol enforcement, integration review, scientific documentation, manuscript-facing interpretation, difficult refactors | Utilities, CLIs, data validators, preprocessing components, metric implementations, statistical utilities, test generation, experiment automation, CI/tooling, type/lint fixes, profiling, reproducibility tooling |
| Typical dirs | `models/`, `selective/`, `calibration/`, `training/`, `docs/` | `utils/`, `cli/`, `data/`, `preprocessing/`, `statistics/`, `evaluation/`, `tests/`, `scripts/`, `.github/` |

**Independent-implementation pattern (used for every mathematically checkable component).** Claude specifies the contract and hand-calculated toy fixtures; Codex implements from the specification *without* seeing Claude's implementation; results must agree on the fixtures. Applied to: AURC, risk–coverage, conformal quantiles, ECE, Brier, DeLong, bootstrap, BH correction. This is the single highest-value use of two agents and catches the class of error that unit tests written by the implementer cannot.

**Per-task record.** Every task in every phase file carries: Task ID · objective · human owner · `solo_fallback` · AI executor · inputs · files touched · dependencies · expected output · tests required · validation procedure · acceptance criteria · scientific risk · compute class · parallelizable? · blocks which tasks · required reviewer.

---

## 15. Git and worktree model

`main` is a protected integration branch. Neither agent commits to it directly.

```
Branches:   agent/claude/pXX-task-name
            agent/codex/pXX-task-name
Worktrees:  ../worktrees/claude-pXX-task-name
            ../worktrees/codex-pXX-task-name
```

**Template.**
```bash
# create
git worktree add -b agent/codex/p04-n4-correction ../worktrees/codex-p04-n4-correction main
# integrate (Research Lead only)
git checkout main && git merge --no-ff agent/codex/p04-n4-correction
# clean up
git worktree remove ../worktrees/codex-p04-n4-correction
git branch -d agent/codex/p04-n4-correction
```

**Rules.** Both branches originate from a known `main` commit. Small atomic commits, one logical concern each; no giant "phase complete" commits. No force-pushing shared branches. No agent edits another agent's active worktree. Generated datasets, checkpoints, and caches are never committed. Merge conflicts are resolved by the Research Lead. **The git SHA is recorded for every scientifically meaningful experiment**, and a dirty tree blocks Gate C.

---

## 16. Dependency graph

```
P00 genesis
 └─> P01 storage/env/GPU ──────────────┐
 └─> P02 acquisition ──┬─> P03 audit ──┴─> P04 preprocessing ─> P05 freeze+prereg
        │              │                                              │
        │ EGD DUA (weeks, external) ───────────────────┐              ▼
        │                                              │        P06 baseline
        └──────────────────────────────────────────────┤              │
                                                       │              ▼
                                                       │        P07 calibration/uncertainty
                                                       │              │
                                                       │              ▼
                                                       │        P08 missing-modality
                                                       │              │
                                                       │              ▼
                                                       │        P09 selective (internal)
                                                       │              │
                                                       │              ▼
                                                       │        P10 ablations + internal stats
                                                       │              │
                                                       └──────────────┤
                                                                      ▼
                                                          P11 EXTERNAL FREEZE ── Gate E
                                                                      │
                                                                      ▼
                                                          P12 external evaluation (once)
                                                                      │
                                                                      ▼
                                                          P13 final stats/figures ── Gate F
                                                                      │
                                                                      ▼
                                                          P14 manuscript + repro package
                                                                      │
                                                                      ▼
                                                          P15 submission → publication
```

**The EGD DUA is the only dependency that cannot be compressed by working harder.** It is initiated in Phase 02 week 1 and joins the graph at Phase 11. If it has not arrived by Phase 11, the contingency is to proceed with UCSF-PDGM as the sole external cohort and add EGD as a reviewer-cycle addendum — a documented degradation, not a silent one.

---

## 17. Phase overview

| # | Phase | Gate | Compute | Parallel with |
|---|---|---|---|---|
| 00 | Repository genesis, spec extraction, governance, tooling | B | none | — |
| 01 | Storage, environment, GPU infrastructure validation | C-prereq | CPU + 1 GPU probe | 02 |
| 02 | Dataset acquisition + **EGD DUA initiation (day 1)** | D | none (network) | 01 |
| 03 | Metadata verification + patient-level overlap/leakage audit | D | CPU | — |
| 04 | Preprocessing pipeline + MRI visual QC | D | CPU (overnight) | — |
| 05 | Cohort finalization, frozen splits, **experiment pre-registration** | D + freeze | CPU | — |
| 06 | Baseline 3D model, always-predict uncalibrated | C | GPU | — |
| 07 | Calibration + uncertainty mechanisms | C | GPU (ensemble) | — |
| 08 | Missing-modality robustness | C | GPU | — |
| 09 | Selective-prediction internal experiments | C | CPU (from artifacts) | 10 |
| 10 | Ablations + internal statistical validation | D | GPU + CPU | 09 |
| 11 | External-evaluation freeze and authorization | **E** | none | — |
| 12 | Frozen cross-institutional external evaluation | E | GPU (inference only) | — |
| 13 | Final statistics, figures, tables, results freeze | F | CPU | — |
| 14 | Manuscript + reproducibility package | F | none | — |
| 15 | Submission, reviewer revisions, publication, archival | F | contingent | — |

Full task-level detail: `docs/research/phases/PHASE_NN_*.md`.

---

## 18. Experiment taxonomy

**Run classes** — different governance, deliberately.

| Class | Purpose | Governance | Recorded? |
|---|---|---|---|
| **DEV** | Debugging, shape checks | None; may be dirty | No |
| **SMOKE** | 1–2 min end-to-end sanity | Must pass before any PILOT | Yes, disposable |
| **PILOT** | Short run to size hyperparameters | Clean tree, config recorded | Yes |
| **FINAL-INTERNAL** | The reported internal result | **Gate C**; clean tree, frozen splits, hashed manifests | Yes, permanent |
| **ABLATION** | SPEC §4.9 axes | Gate C; pre-registered in Phase 05 | Yes, permanent |
| **EXTERNAL-FROZEN** | The single external run | **Gate E**; Research Lead signature; nothing may change afterward | Yes, immutable |
| **REVIEWER** | Post-submission requests | Labelled as post-hoc; never replaces the pre-registered primary result | Yes, separately labelled |

**Mechanisms.**

| ID | Mechanism | Needs its own training run? |
|---|---|---|
| M1 | Always-predict, uncalibrated (raw softmax) | no — base model |
| M2 | Always-predict, temperature-scaled | no — post-hoc on calibration split |
| M3 | Selective, MC-dropout predictive entropy | no — inference-time on base model |
| M4 | Selective, deep ensemble (N≈5) predictive variance | **yes — N members** |
| M5 | **Selective, conformal (PRIMARY)** | no — post-hoc quantile on calibration split |
| M6 | Always-predict, tumor-aware joint comparator (SPEC §4.8 baseline 5) | shares the base model; see **D-006** |

**Evaluation conditions** = {modality condition} × {cohort}.
Modality conditions (6): `full`, `−T1`, `−T1CE`, `−T2`, `−FLAIR`, `T1CE+FLAIR only`.
Cohorts (3): UTSW internal test, UCSF-PDGM, EGD.
⇒ 18 evaluation conditions × 6 mechanisms = **108 result cells**, all computed from frozen prediction artifacts at negligible cost.

**Training-run budget — the resolution to D-005.** Only *training* is expensive; M1/M2/M3/M5/M6 all derive from already-trained weights. Ensemble members are trained once and reused across all 18 conditions.

| Run | Purpose | Serves |
|---|---|---|
| R1 | Baseline, no modality dropout | ablation "modality dropout off" |
| R2–R6 | Modality-dropout model, seeds 0–4 | **R2 is the primary single model** (M1,M2,M3,M5,M6); R2–R6 together are M4 |
| R7 | Whole-brain pooling (no tumor-aware) | confirmatory H1 ablation |
| R8 | Two-stage independent seg + classify | confirmatory H2 ablation |
| R9 | Reserve / re-run buffer | contingency |

**9 training runs**, inside the SPEC §3.4 budget of 8–12. This is only achievable because prediction artifacts are frozen and reused — it is the reason for that design choice.

---

## 19. Data provenance model

Every number in the final paper traces back through an unbroken chain:

```
raw patient ID (source cohort, download date, checksum)
   → ID normalization (raw → private internal → public pseudonymized)
   → cross-dataset overlap audit  → exclusion manifest (reason per patient)
   → final cohort manifest (hashed)
   → preprocessing (version, params, content hash per volume)
   → split manifest (hashed, patient-level, stratified)
   → model input
   → prediction artifact (run ID + git SHA + checkpoint hash)
   → statistical result
   → manuscript table / figure cell
```

**Three ID tiers, never mixed.** *Raw identifiers* (as shipped) — used only inside the audit, stored in `data/private/`, never committed. *Private internal IDs* — the join key across manifests; committed only if the cohort's terms permit. *Public pseudonymized IDs* — what appears in released artifacts and the paper.

Restricted clinical metadata is not committed unless the dataset terms clearly permit it. Exclusions record a *reason*, not just an ID: `overlap:brats2021`, `label:ambiguous`, `qc:registration-failed`, `qc:corrupt`, `missing:sequence`, `duplicate:scan`.

---

## 20. Reproducibility model

**Every experiment records** (20 fields, enforced by `tracking/`): run ID · timestamp · git SHA · dirty/clean status · dataset manifest hash · split manifest hash · exclusion-list hash · full resolved config · seed · Python version · dependency lock hash · PyTorch/MONAI versions · GPU info · preprocessing version · checkpoint hash · training history · final predictions path · calibration parameters · selective thresholds · metrics · log path.

**Tracking.** MLflow, file-backed, artifacts on the external SSD — no cloud dependency. Chosen because the run-record schema above needs a queryable store and the experiment count (~9 training runs × many evaluations) is past comfortable manual bookkeeping. It is a convenience layer: the JSON run record on disk is authoritative, so a corrupted MLflow store never costs a result.

**Configuration.** Hydra/OmegaConf, decided in Phase 00. Experiments are defined by config composition; magic constants inside Python modules are a review-blocking defect.

**Honesty about determinism.** Seeds are set for Python, NumPy, and Torch, and `torch.use_deterministic_algorithms` is enabled where it does not forbid a needed op. Some CUDA kernels remain non-deterministic. We record which operations are non-deterministic and report run-to-run variation on a repeated seed rather than claiming bitwise reproducibility we cannot deliver.

---

## 21. Quality strategy

| Tool | Purpose | Threshold | CI behavior |
|---|---|---|---|
| **Ruff** (lint) | Correctness/style | Zero unexplained errors; every `# noqa` carries a reason | Blocks Gate A |
| **Ruff** (format) | Deterministic formatting | Fully formatted | Blocks Gate A |
| **mypy** | Typing on scientific infrastructure | Strict on `src/`; `evaluation/`, `statistics/`, `selective/`, `splits/`, `leakage/` are no-`Any` zones | Blocks Gate B |
| **pytest** | Correctness | Fast unit suite < 60 s; GPU/slow tests marked and excluded from Gate A | Blocks Gate A/B |
| **pytest-cov** | Meaningful coverage | **≥95%** on `evaluation/ statistics/ selective/ calibration/ splits/ leakage/`; **no target** on training loops | Blocks Gate B |
| **Radon** | Complexity | Flag CC > 10 for review; do **not** split a mathematically coherent function to game the metric | Advisory |
| **pip-audit** | Known CVEs | No unresolved high severity | Blocks Gate B |
| **Bandit** | Insecure patterns | Clean on `src/` | Blocks Gate B |
| **detect-secrets** | Credential/PHI leak | Zero new findings | Blocks Gate A |
| **codespell** | Typos in docs/manuscript | Clean | Advisory |
| **pre-commit** | Runs Gate A locally | Installed in Phase 00 | — |

**Waivers.** Any threshold may be waived with a written scientific justification recorded in `DECISION_LOG.md` and approved by the Research Lead. Silent waivers are a Gate B failure. No tool is added for a badge.

---

## 22. Testing strategy

Scientific calculations get stronger tests than CLI wrappers. Four levels:

1. **Hand-calculated toy examples.** Every metric has a fixture small enough to verify with a pencil — e.g. a 6-patient risk–coverage table where AURC is computed by hand in the test docstring.
2. **Edge cases.** Empty accepted set (coverage 0); coverage 1; all-correct; all-wrong; ties in the confidence score; a single-class calibration split; a conformal quantile that lands beyond the calibration set (n+1 correction); NaN/inf guards.
3. **Cross-checks against known implementations.** DeLong against a reference implementation; ECE against a published binning definition; bootstrap CI coverage against a simulated ground truth.
4. **Property/randomized invariants.** Coverage is monotone non-increasing in τ; AURC ∈ [0,1]; selective risk at coverage 1 equals full-set risk; conformal empirical coverage on *exchangeable* held-out data ≥ 1−α−ε; permuting patient order changes nothing.

**Mandatory test targets** (SPEC-critical): dataset manifest logic · patient splitting · leakage detection · modality masks · normalization-statistic calculation · metric calculations · calibration · conformal quantiles · risk–coverage · AURC · bootstrap sampling · statistical tests · config parsing · checkpoint handling.

**The leakage regression test** is the single most important test in the repository: given the frozen manifests, assert that no patient ID appears in more than one split, that no excluded ID appears anywhere, and that the UTSW ∩ external intersection is empty. It runs in CI on every commit and is never skipped.

---

## 23. Statistical-analysis strategy

Four strata, never blended in reporting:

| Stratum | Contents | Multiplicity |
|---|---|---|
| **Descriptive** | Cohort tables, label counts, flow diagram, QC exclusions | none |
| **Primary** | C1–C5 on IDH: selective risk at matched coverage, AURC, RC monotonicity, empirical-vs-nominal coverage | **BH-corrected** across the §4.9 family |
| **Secondary** | RQ3 calibration degradation (ECE/Brier internal→external); AUROC/AUPRC; confirmatory H1/H2 ablations | BH-corrected |
| **Exploratory** | RQ4 (1p/19q), any post-hoc analysis | Reported with CIs; **no inferential claim** |

**Methods.** Patient-level bootstrap, ≥1000 iterations, 95% CIs for AUROC, AUPRC, AURC, selective risk at fixed coverage, ECE, Brier. DeLong for paired AUROC on the same test set. Paired bootstrap or permutation for AURC and selective-risk differences between mechanisms. Benjamini–Hochberg across the ablation-comparison family.

**Resampling respects the design.** The resampling unit is the **patient**, always. Paired comparisons resample patients once and evaluate both mechanisms on the same resample — mechanisms are not independent samples and must never be treated as such.

**Monotonicity** (C5) is not eyeballed. It is tested: count and quantify violations `max(0, R(φ_i) − R(φ_j))` for `φ_i < φ_j`, with a bootstrap CI on the total violation magnitude, so "non-monotonic" is a number rather than an impression.

**Coverage deviation** (C4) is `|empirical − nominal|` with a bootstrap CI, judged against the tolerance band frozen in Phase 05 — and C4's own falsification condition (the CI is too wide to distinguish preserved from degraded) is itself a reportable outcome.

**Machine-readable first.** All statistics are written to versioned JSON/parquet **before** any table or figure is produced. Tables and figures are generated from those files by code. No number is ever transcribed by hand into the manuscript.

---

## 24. External-validation firewall

The distinction the whole project rests on:

| Permitted from Phase 02 (**operational**) | Blocked until Gate E (**performance**) |
|---|---|
| Downloading UCSF-PDGM / EGD | Computing any metric against external labels |
| Verifying checksums, file counts, integrity | Looking at external AUROC, coverage, risk |
| BraTS-2021 ID de-duplication | Tuning any hyperparameter, threshold, or normalization statistic on external data |
| Counting labels for the cohort table | Selecting a checkpoint using external results |
| Running deterministic preprocessing | Fitting calibration or conformal quantiles on external data |
| Visual QC of preprocessing output | Any "quick sanity check" of external accuracy |

**Technical enforcement.** `GLIOMA_EXTERNAL_EVAL_AUTHORIZED=0` in `.env` by default. Any code path that joins external predictions to external labels calls `firewall.assert_external_eval_authorized()`, which raises unless the flag is set **and** a signed freeze manifest exists. Flipping the flag is a logged, dated, Research-Lead-only action.

**Gate E freeze manifest** — generated and hashed before the flag flips, covering: code commit SHA · model checkpoints (hashed) · preprocessing configuration · normalization statistics · data exclusions · UTSW splits · calibration parameters and procedure · conformal method and α · operating points · missing-modality conditions · primary metrics · complete statistical-analysis plan.

**After the flag flips:** the event is logged; predictions, configs, and SHA are preserved immutably; **the method does not change because results look undesirable.** Any post-external change is categorized as (a) bug correction, (b) reviewer-requested analysis, or (c) explicitly exploratory — and never silently replaces the pre-registered primary result.

---

## 25. Research artifact and versioning strategy

| Artifact | Versioning | Immutable after |
|---|---|---|
| Cohort manifest | SHA-256, committed | Phase 05 |
| Exclusion list | SHA-256, committed, reason per patient | Phase 05 |
| Split manifest | SHA-256, committed | Phase 05 (**freeze**) |
| Preprocessing output | Content-addressed by param hash | per-version |
| Checkpoints | Hashed, run-ID named | Gate C |
| Calibration params / conformal quantile | JSON, hashed | Gate E |
| Prediction artifacts | Parquet, one row per patient × mechanism × condition | Gate E / Gate F |
| Statistical results | JSON, versioned | Gate F |
| Figures/tables | Generated from the above; regeneration is a CI target | Gate F |

**Regeneration test.** At Gate F, delete `paper/figures/` and `paper/tables/`, run one command, and confirm byte-identical (or numerically identical) regeneration from frozen result files. A figure that cannot be regenerated does not go in the paper.

---

## 26. Publication pipeline

The project ends at **publication**, not at "training complete."

Phase 13 results freeze → Phase 14 manuscript + reproducibility package → Phase 15 submission, review, revision, camera-ready, code release, archival.

**Maintained continuously from Phase 00 — not reconstructed from memory in the final month:** bibliography (BibTeX, in-repo) · dataset table · cohort-flow diagram · method description (written as each phase completes) · experiment registry · limitation log · decision log · **negative-results log** · exclusion log · figure registry · table registry.

**Framing discipline.** The manuscript is an empirical trustworthiness/reliability study. It is not a new-architecture paper. Reviewer-facing differentiation against GMMAS, Elyassirad et al., Yogananda et al., RISEN, and FoundBioNet is drafted in Phase 14 from the table in §5 above.

**Before submission:** re-check TRIPOD+AI and CLAIM 2024 for updates (both were current as of the SPEC's August 2026 preparation, and both are actively maintained); complete a fresh novelty/literature check; and make no "first" claim that this check does not support.

---

## 27. Risk register summary

Full register with likelihood/impact/detection/prevention/mitigation/owner/trigger: `docs/research/RISK_REGISTER.md`.

**Critical** — patient leakage · cross-dataset overlap (esp. UCSF-PDGM/BraTS-2021) · external-test peeking · preprocessing/normalization leakage · wrong modality→channel mapping · wrong patient split · label-definition mismatch across cohorts · architecture scope creep · post-hoc threshold manipulation.

**High** — EGD DUA delay · corrupted/incomplete TCIA downloads · insufficient class counts after exclusions (esp. 1p/19q, n=63 pre-exclusion) · GPU OOM · remote GPU downtime · preprocessing failure · very wide CIs at extreme coverage · non-monotonic selective curves · calibration collapse · high abstention · poor external discrimination.

**Stated explicitly:** the last five "high" items are **scientific outcomes, not engineering failures.** Non-monotonic curves refute C5; calibration collapse answers RQ3; poor external discrimination refutes C3. Each is a *result*. The register records them so they are recognized as findings rather than debugged away.

---

## 28. Definition of Done — whole project

The project is complete when **all** hold:

1. Every RQ1–RQ4 has a stated answer supported by a named artifact.
2. Every claim C1–C6 is explicitly **supported or refuted**, with the pre-registered falsification criterion applied as written.
3. All 108 result cells (6 mechanisms × 18 conditions) are computed, or their absence is justified in writing.
4. Every number in the manuscript traces through the §19 provenance chain to a raw patient ID.
5. Figures and tables regenerate from frozen result files by one command.
6. The leakage regression test passes on the final manifests; UTSW ∩ external = ∅; UCSF-PDGM ∩ BraTS-2021 = ∅.
7. Gate E was passed exactly once, with a signed freeze manifest, and no method change followed it.
8. TRIPOD+AI and CLAIM 2024 checklists are complete, with a freshness re-check dated within 30 days of submission.
9. Negative results are reported, not buried.
10. The reproducibility package (code, configs, manifests, environment lock, run records) is released and independently re-runnable from the README by someone who was not on the project.
11. The manuscript is submitted, reviewed, revised, and accepted — or a documented decision to stop is recorded.

---

## 29. Open decisions

Twelve real contradictions/ambiguities were found between and within the source documents. They are **recorded, not silently resolved** — full alternatives, consequences, and recommendations in `docs/research/DECISION_LOG.md`.

| ID | Decision | Must resolve by | Blocking? |
|---|---|---|---|
| D-001 | Team model: solo (SPEC) vs. 3 active (master prompt) | **Resolved** — A/B/C + solo fallback | no |
| D-002 | Split conformal vs. conformal risk control — used interchangeably but different procedures | Phase 07 | **yes** |
| D-003 | Abstention operationalization: score threshold vs. non-singleton prediction set | Phase 05 | **yes** |
| D-004 | C4 tolerance band is an example, not a number — **C4 is not falsifiable until frozen** | Phase 05 | **yes** |
| D-005 | Compute budget vs. N=5 ensemble | **Resolved** — train-once/evaluate-many, 9 runs (§18) | no |
| D-006 | Baseline-5 comparator scope — unbounded reimplementation risk | Phase 06 | yes |
| D-007 | 1p/19q has an RQ but no budget line | Phase 05 | yes |
| D-008 | Missingness is simulated, not natural — construct validity | Phase 14 (reporting) | no |
| D-009 | All SPEC label counts provisional until verified from files | Phase 03 | **yes** |
| D-010 | Forward-dated citations need verify-before-cite | Phase 14 | no |
| D-011 | BraTS pretraining: permitted but not required — recommend none | Phase 06 | yes |
| D-012 | Naturally-missing sequences vs. completeness inclusion criterion | Phase 03 | yes |

---

## 30. Critical path

**Published in two forms**, per the solo-degradation requirement.

**(a) Three-person path (A + B + C active).**

```
P00 genesis (3d)
  → P02 EGD DUA SUBMITTED (day 1; ~4–8 weeks external latency, runs underneath everything)
  → P01 storage+GPU validation (4d)
  → P02 UTSW + UCSF download & verify (5d, B)
  → P03 overlap/leakage audit (7d, B+A)          ← D-009, D-012 resolve here
  → P04 preprocessing + visual QC (12d, mostly overnight CPU; QC is B)
  → P05 cohort freeze + pre-registration (4d, A) ← D-003, D-004, D-007 resolve here
  → P06 baseline model (14d, A)                  ← D-006, D-011 resolve here
  → P07 calibration + uncertainty (14d)          ← D-002 resolves here
  → P08 missing-modality (10d)
  → P09 selective internal (7d)  ∥  P10 ablations + stats (14d)
  → P11 external freeze + GATE E (3d, A only)
  → P12 external evaluation (4d)
  → P13 final stats/figures/freeze (10d)
  → P14 manuscript + repro package (21d)
  → P15 submission → publication (contingent)
```
Approximately **~34 weeks** to submission, with EGD's DUA fully absorbed by parallel work.

**(b) Solo-degraded path (A only).** Adds roughly **+7 weeks**, concentrated in three places: the Phase 03 ID audit (+5d — no independent second check; substitute Codex re-derivation), Phase 04 visual QC (+8d, **DEGRADED** — a single reader on MRI quality control, which must be declared in Limitations), and Phase 13/14 result and table verification (+10d — Codex independent-recompute substitutes for C's human audit). Total ≈ **41 weeks**. **The project remains completable.** No irreplaceable component is owned by B, C, or D–F.

**Longest-latency item is not compute.** It is the EGD data-use agreement. It is submitted on day 1 of Phase 02 and everything else is arranged to proceed without it.

---

*Governed by the SPEC. Amendments to scientific content require a SPEC change recorded in `DECISION_LOG.md`. Engineering improvements do not.*
