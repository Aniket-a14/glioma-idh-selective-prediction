# Calibrated Selective Prediction for MRI-Based Glioma IDH Classification under Missing Modalities and Cross-Institutional Domain Shift

### Project Specification — Final Year Research Project (Deep Research Pass)

**Prepared:** August 11, 2026
**Target publication type:** Single original-research paper (journal or MICCAI-tier conference; e.g., *Radiology: AI*, *Neuro-Oncology Advances*, *npj Precision Oncology*, or MICCAI/ISBI proceedings)
**Team size:** Solo researcher (student project)
**Research framing:** Empirical trustworthiness/reliability study, NOT a new architecture paper
**Foundation:** This document consolidates three prior deep-research passes (broad literature/feasibility review; final research-design and novelty-validation phase; targeted hostile novelty-verdict phase). It does not repeat their searches; it freezes their conclusions into an implementation-ready specification.

---

## 1. Problem Statement

### 1.1 In plain language

Doctors increasingly want to know a glioma's molecular subtype — specifically whether it carries an **IDH mutation** — because this drives diagnosis, prognosis, and treatment planning under the WHO 2021 classification. Getting this from a biopsy is invasive. Getting it from an MRI scan with AI is attractive, but AI models that always output a confident-looking prediction are dangerous in practice: when the scan is missing one of its usual sequences, or when the patient was scanned at a different hospital than the one the model was trained on, the model's confidence often does not track its actual accuracy. It can be badly wrong while still "sounding" sure.

This project asks a narrower, more honest question: instead of forcing the model to answer every case, **can we teach it to recognize when it shouldn't answer** — and abstain, flagging the case for a human or a lab test instead — in exactly the two situations where MRI-based AI is known to struggle: missing scan sequences, and scans from a different hospital? We are not trying to build a new kind of neural network. We are trying to find out, rigorously, whether "knowing when not to predict" actually works for this problem, or whether — as has happened in other areas of medical imaging — it breaks down exactly when it's needed most.

### 1.2 Formal statement

Let $x = (x_{T1}, x_{T1CE}, x_{T2}, x_{FLAIR})$ denote a (possibly incomplete) multiparametric preoperative MRI study for a glioma patient, with true IDH status $y \in \{0,1\}$ (wildtype/mutant). We consider a **selective classifier** $(f, g)$, where $f(x) \to \hat{p}(y=1\mid x) \in [0,1]$ is a calibrated probability estimator and $g(x) \to \{0,1\}$ is a rejection function such that the system predicts $\hat{y} = \mathbb{1}[f(x) > 0.5]$ when $g(x)=1$ (accept) and abstains when $g(x)=0$ (reject). Coverage is $\phi = \mathbb{E}[g(x)]$; selective risk is $R(f,g) = \frac{\mathbb{E}[\ell(f(x),y)\cdot g(x)]}{\mathbb{E}[g(x)]}$ for a loss $\ell$ (0–1 loss or a proper scoring rule). The **risk–coverage curve** traces $R(f,g_\tau)$ as the rejection threshold $\tau$ varies across confidence/nonconformity scores; **AURC** is its integral. We evaluate $(f,g)$ under four conditions formed by crossing $\{$complete MRI, missing MRI$\} \times \{$internal (UTSW), external (UCSF-PDGM / EGD)$\}$, and empirically measure how close the coverage of a conformal $g$ remains to its nominal target ($1-\alpha$) in each condition. Standard conformal guarantees rely on an exchangeability assumption between calibration and test data; domain shift and missingness are known to violate this assumption. We do not assume the guarantee holds under these conditions — we treat the extent and pattern of any coverage deviation as the object of study.

### 1.3 Research questions

- **RQ1 (primary):** Under missing MRI sequences and under cross-institutional domain shift, does a calibrated selective-prediction mechanism (conformal risk control, compared against temperature scaling and MC-dropout) produce a well-behaved risk–coverage trade-off — i.e., does rejecting low-confidence cases genuinely and monotonically lower selective risk and AURC relative to an always-predict baseline?
- **RQ2 (primary):** Does empirical coverage remain close to nominal coverage under missing modalities and cross-institutional domain shift, and how does violation of the exchangeability assumption affect coverage? This is treated strictly as an open empirical question — conformal guarantees are not assumed to hold under shift or missingness; the goal is to characterize whether and how they degrade (as documented in non-glioma imaging domains), not to confirm that they survive.
- **RQ3 (secondary):** Does calibration (ECE, Brier score, reliability) degrade from internal to external evaluation for MRI-based IDH classification in this specific dataset combination (UTSW → UCSF-PDGM/EGD), replicating or contradicting the degradation reported elsewhere (e.g., GliomaVista-IDH external Brier 0.32)?
- **RQ4 (exploratory, secondary endpoint):** Does the same selective-prediction behavior hold for 1p/19q codeletion, given its smaller label count, or must conclusions there be reported only as exploratory with wide confidence intervals?

### 1.4 Falsifiable claims

| # | Claim | Result that would prove it WRONG |
|---|---|---|
| C1 | Selective prediction (conformal) achieves lower selective risk at matched coverage than an always-predict baseline, internally. | Selective risk at any fixed coverage ≥ always-predict risk; risk–coverage curve is flat or increasing as coverage decreases. |
| C2 | Selective prediction preserves this advantage under missing modalities. | Selective-risk advantage over always-predict disappears or reverses when 1–2 sequences are dropped. |
| C3 | Selective prediction preserves this advantage under external (cross-institutional) shift. | No selective-risk advantage on UCSF-PDGM/EGD relative to always-predict, at matched coverage. |
| C4 | The magnitude and direction of any deviation between empirical and nominal coverage under domain shift and missingness can be measured and characterized (e.g., against a pre-registered tolerance band such as ±5 percentage points), without presupposing whether coverage holds or degrades. | The deviation cannot be reliably characterized — e.g., empirical coverage estimates are too noisy/unstable (given sample size) to distinguish "coverage preserved" from "coverage degraded" at the pre-registered tolerance. |
| C5 | Risk–coverage curves remain monotonic (rejecting less-confident cases never increases risk) across all four evaluation conditions. | Curves become non-monotonic under shift/missingness, mirroring documented failures in retinal/CXR imaging. |
| C6 | Abstention rate correlates with actual error rate (uncertain cases are disproportionately the wrong ones). | Abstained cases are no more likely to be erroneous than randomly selected cases of equal size. |

### 1.5 The honest verdict, stated plainly

This is **not** a paper about inventing a new CNN, Transformer, CNN–Transformer hybrid, segmentation network, fusion mechanism, or a generically "better" uncertainty method — all of those exist and are cited, not reinvented. It is also **not guaranteed to produce a positive result**, and that is by design: the central, pre-registered possibility is that selective prediction **fails** to deliver a genuine reliability benefit under shift/missingness, exactly as it has been shown to fail in other shifted medical-imaging settings (retinal fundus, chest X-ray). Either outcome — "it works and here's how well" or "it breaks down and here's exactly how" — is a legitimate, publishable, clinically informative finding. The project must not quietly become a search for the result that "looks good"; the falsification table above is the pre-registered commitment against that risk.

**Distinction that matters for framing:** A conventional ("always predict") classifier reports a probability for every case, and its accuracy is a population-average number that says nothing about any individual patient's reliability. A selective classifier is scientifically different because it makes an *instance-level* trust decision — it can say "I don't know" — and its evaluation requires a second axis (coverage) alongside accuracy. Whether that second axis behaves sensibly under the two conditions clinicians actually worry about (incomplete scans, different hospital) is an open empirical question this project answers.

---

## 2. Datasets

### 2.1 Central finding, stated directly

UTSW-Glioma (2026) is the only large, recent, IDH-labeled, four-sequence glioma cohort that is **not** entangled in the BraTS/TCGA/UCSF overlap web, making it the clean choice as the primary training set. UCSF-PDGM and EGD are usable as external cohorts, but UCSF-PDGM carries a documented partial overlap with BraTS-2021 (a shipped ID-mapping file exists specifically because of this) that MUST be resolved before it is treated as "independent," and EGD requires a non-trivial data-use agreement that should be initiated immediately, not late. 1p/19q labels are numerically thin enough (UTSW: 63 codeleted / 272 non-codeleted; further reduced by any leakage exclusions) that they can only support an exploratory secondary analysis, not a headline claim. MGMT should not appear as a primary or secondary endpoint at all — this is a documented consequence of MRI-based MGMT prediction being close to chance-level externally, not a data-availability choice.

### 2.2 Primary dataset

**UTSW-Glioma** (Reddy et al., *Scientific Data* 2026, DOI 10.1038/s41597-026-07274-4; TCIA collection DOI 10.7937/dfae-1b86). 625 patients (2006–2023), pre-contrast T1w, post-contrast T1w (T1CE), T2w, T2w-FLAIR, multi-label tumor segmentations. Molecular labels: IDH n=622 (176 mutant / 446 wildtype — the most completely labeled marker); 1p/19q n=335 (63 codeleted / 272 non-codeleted); MGMT n=281 (114 methylated / 167 unmethylated). Open access via TCIA. Not part of BraTS or TCGA — the primary reason it is chosen as the training cohort.

### 2.3 External validation dataset(s)

- **UCSF-PDGM** (Calabrese et al., *Radiology: AI* 2022, DOI 10.1148/ryai.220058). 501 patients, 3T multiparametric MRI (11 sequences available; use the four structural contrasts to match UTSW), IDH labeled for essentially all patients, 1p/19q for 410/501, grade skewed heavily toward grade IV (~80%). **Caveat (mandatory to act on):** a documented subset overlaps with BraTS-2021, and UCSF-PDGM ships a BraTS-2021 ID-mapping file specifically to allow exclusion of overlapping cases. Any overlapping subject IDs must be removed before this cohort is used as "external," and none of those overlapping subjects may appear in any BraTS-based pretraining if this cohort is to remain a valid external test set.
- **EGD (Erasmus Glioma Database)** (van der Voort et al., *Data in Brief* 2021, DOI 10.1016/j.dib.2021.107191). 774 patients, pre/post-contrast T1w, T2w, FLAIR; IDH n=467; 1p/19q n=259; grade n=716. Requires a data-use agreement through Health-RI (contact servicedesk@health-ri.nl; XNAT portal access alone is not sufficient) — **not an instant download; initiate this immediately (see Section 9).**

### 2.4 Supplementary datasets (genuinely useful, secondary role only)

- **LGG-1p19qDeletion** (TCIA). 159 patients, T1C + T2 only (3 axial slices per patient), 102 codeleted / 57 not, no IDH labels. TCGA-linked. Usable only as a dedicated, small, exploratory 1p/19q external check — not a primary cohort, and not usable for the missing-modality experiments (it never had all four sequences to begin with).
- **UPENN-GBM** (Bakas et al., *Scientific Data* 2022, DOI 10.1038/s41597-022-01560-7; TCIA DOI 10.7937/TCIA.709X-DN49). 630 patients (611 baseline pre-operative), T1/T1CE/T2/FLAIR, IDH1 and MGMT labeled, no 1p/19q. GBM-only cohort, meaning IDH is almost entirely wildtype — useful only as an optional, heavily-imbalanced supplementary external check, explicitly flagged as such if used.

### 2.5 Gated / not-recommended datasets

- **BraTS 2021 / 2023 / 2024** — usable *only* as a source of segmentation pretraining weights (if at all), never for final IDH classification claims, because it directly embeds pre-operative TCGA-GBM (135 cases) and TCGA-LGG (108 cases) with identical subject IDs to TCGA/TCIA. If any BraTS-derived pretraining is used, every subject ID that also appears in UCSF-PDGM, TCGA-GBM/LGG, or EGD must be excluded from BraTS before pretraining, or the "external" claim for those cohorts is void.
- **TCGA-GBM / TCGA-LGG** — rejected as a standalone training or "external" cohort in this project; treat as a leakage source to be actively excluded from, not built into, the pipeline.

### 2.6 Rejected datasets and why

- **IvyGAP** — only ~39 patients with imaging, too small and heterogeneous to add statistical power; rejected.
- **RHUH-GBM** — ~40 GBM patients, small, GBM-only (IDH skew), useful only as a footnote-level sanity check if time permits; not part of the core plan.
- Any dataset requiring 2D-only or single-slice input (e.g., LGG-1p19qDeletion for anything beyond its stated exploratory role) is rejected as a primary or missing-modality cohort because the 2×2 missing-modality/domain-shift design requires full 3D four-sequence volumes.

### 2.7 Permissions / access requirements summary

| Dataset | Access mechanism | Lead time | Status to assume |
|---|---|---|---|
| UTSW-Glioma | Open, TCIA download | Low | Start immediately |
| UCSF-PDGM | Open, TCIA download | Low | Start immediately, but budget time for the BraTS-ID de-duplication step |
| EGD | Data-use agreement via Health-RI/XNAT | **Non-trivial — weeks** | **Initiate in week 1, do not block other work waiting on it** |
| LGG-1p19qDeletion | Open, TCIA | Low | Optional, low priority |
| UPENN-GBM | Open (CC-style), TCIA | Low | Optional, low priority |
| BraTS 2021/2023/2024 | Open (registration) | Low | Only if segmentation pretraining is used; leakage exclusion mandatory |

---

## 3. Computation Power & Cost

### 3.1 Realistic hardware envelope

A single modern GPU with **16–24 GB VRAM** (RTX 3090/4090, A5000, or equivalent cloud instance) is sufficient. This is not a foundation-model project; the backbone (Section 4) is a modest 3D CNN, not a large pretrained transformer, so there is no need for multi-GPU training or 40+ GB cards.

### 3.2 Storage

Four MRI sequences × ~600–1,300 patients across UTSW + UCSF-PDGM + EGD, as NIfTI volumes, is on the order of **tens to ~150 GB raw**; with preprocessed/cached and augmented copies, budget **250–500 GB** of working storage. This is comfortably within a single workstation SSD or a modest cloud storage bucket.

### 3.3 Preprocessing cost

Standard pipeline: rigid co-registration to a common template, skull-stripping (e.g., HD-BET), N4 bias-field correction, resampling to ~1 mm isotropic, per-modality z-score normalization (statistics computed on training data only — see Section 5.6). This is CPU-bound and can run overnight on a normal workstation for the full cohort; it does not require GPU time.

### 3.4 Training cost

Patch-based 3D training (96³ or 128³ voxel crops with sliding-window inference) on a SegResNet/nnU-Net-scale backbone (~10–30M parameters) fits in 16–24 GB VRAM at batch size 1–2. Expect on the order of **1–3 days per major training run** on one GPU; the full ablation/experiment suite (Section 4.9) at roughly 8–12 runs implies **2–4 weeks of GPU time total**, comfortably parallelizable across idle nights/weekends on a single machine, or compressible with modest cloud rental if a deadline requires it.

### 3.5 CPU / RAM

A workstation with ≥32 GB RAM and a modern multi-core CPU is adequate for preprocessing and data loading; no specialized CPU cluster is required.

### 3.6 Number of experiments/ablations

The **minimum rigorous set** (Section 4.9) is 4 baselines/mechanisms × 4 evaluation conditions (complete/missing × internal/external) = a bounded, enumerable set of runs, not an open-ended sweep. This keeps the compute budget predictable and prevents scope creep into unnecessary architecture search.

### 3.7 Local vs. cloud

Local hardware is sufficient for the full project if a single 16–24 GB GPU is available for weeks at a time. Cloud GPU rental (a single instance, not a cluster) is a reasonable fallback only if local access is intermittent or a deadline compresses the timeline — it is not a structural requirement of the project.

### 3.8 The actual bottleneck

**The bottleneck is NOT compute.** In order of severity, the real constraints are: (1) **labels** — the 1p/19q positive count (63 in UTSW before any exclusions) is the tightest numerical constraint in the whole project and directly limits what can be claimed about that marker; (2) **external data access and cleanliness** — the EGD data-use agreement lead time and the UCSF-PDGM/BraTS de-duplication step are schedule risks, not compute risks; (3) **missing "naturally missing" modalities** — UTSW, UCSF-PDGM, and EGD are all curated four-sequence cohorts, so true missing-modality evaluation must be *simulated* (dropped at inference), which is a construct-validity limitation to state plainly, not a compute problem. Compute and GPU VRAM are comfortably sufficient throughout.

### 3.9 Realistic 6–12 month computational plan for a solo researcher

Months 1–2: preprocessing pipeline + leakage audit (CPU-bound, low GPU need). Months 2–4: baseline + calibrated baseline + selective-prediction mechanism implementation and internal validation (moderate, steady GPU use). Months 4–6: missing-modality and external-validation experiments (the bulk of GPU time, but still boundable to the enumerated experiment grid). Months 6–8: statistical analysis, ablations, robustness checks. Months 8–12: writing, revision, and any reviewer-requested additional runs (buffer built in intentionally).

---

## 4. Methodology

### 4.1 Architecture recommendation

**Selected backbone: a 3D SegResNet-style CNN encoder (MONAI-native), optionally with an auxiliary nnU-Net-style segmentation decoder for tumor-focused (tumor-aware) feature pooling; NOT a bespoke Transformer or CNN–Transformer hybrid.**

Rationale: FoundBioNet, MTS-UNET, and GMMAS already demonstrate that Swin-UNETR/foundation-model-scale backbones and TAFE-style tumor-aware modules deliver strong IDH discrimination; reproducing that architecture-side result would not be novel and would consume the compute/complexity budget better spent on the selective-prediction mechanism, which is the actual contribution. A standard, well-validated 3D CNN encoder (a) is proven to reach competitive IDH AUCs in this literature, (b) trains comfortably on one GPU, (c) is simple enough that any observed risk–coverage or calibration failure can be confidently attributed to the selective-prediction mechanism rather than to architectural idiosyncrasy, and (d) is fully reproducible in PyTorch/MONAI. A lightweight tumor-mask-guided pooling step (using the auxiliary segmentation output to focus classification features on the tumor region) is retained as a confirmatory, not novel, component — it is cheap to add and lets H1/H2-style ablations (tumor-aware vs. whole-brain, joint vs. independent) be reported as secondary, established-literature-confirming results without being the paper's claim.

**Alternatives considered and rejected as primary:** (i) 3D Swin-UNETR/foundation-model backbone (BrainSegFounder-style) — stronger raw AUC potential but adds a large-pretraining dependency and computational overhead disproportionate to a contribution that is not about the backbone; kept as an optional robustness check only if time permits. (ii) 2D ViT+text fusion (GlioMT-style) — rejected because the project needs true 3D input to support realistic per-sequence missing-modality experiments. (iii) Full 3D ViT/Swin from scratch — rejected on VRAM/compute grounds; not needed for the research question.

### 4.2 Prediction system and selective-prediction layer

**Inputs:** four co-registered, skull-stripped, normalized 3D volumes (T1, T1CE, T2, FLAIR), each patch-cropped to 96³ or 128³ voxels.
**Multimodal input handling:** channel-stacked at the input (early/mid fusion), with a learnable per-modality weighting; when a modality is deliberately dropped (Section 4.4), its channel is zeroed rather than imputed.
**Model output:** a single scalar $\hat{p}(y{=}1\mid x)$ (IDH-mutant probability) from the classification head attached to the shared encoder (optionally pooled through the tumor mask from the auxiliary segmentation head).
**Calibration:** post-hoc calibration of $\hat{p}$ via temperature scaling (baseline) and, for the primary mechanism, conformal risk control (Section 4.6).
**Threshold selection / abstention rule:** a rejection threshold $\tau$ on the conformal nonconformity score (or, for the baseline comparators, on softmax confidence / MC-dropout entropy / ensemble variance), chosen on a held-out calibration split — **never on the external test set** (see Section 4.8/5.1) — mapping to a target coverage or a target nominal error rate.
**Final inference behavior:** if $g(x)=1$, output $\hat{y}$ with $\hat{p}$; if $g(x)=0$, output "abstain — recommend molecular/histopathological confirmation," never a forced label.

**Always-predict vs. predict-or-abstain — why this distinction is scientifically load-bearing:** an always-predict classifier is evaluated by a single population-level accuracy/AUC number that says nothing about which individual patients it can be trusted on. A predict-or-abstain system introduces a second, jointly reported axis — coverage — and its entire value proposition rests on whether declining to answer on a subset of cases actually concentrates the errors in that declined subset. That is not guaranteed by construction; it is an empirical property that can succeed or fail, and testing whether it fails under shift/missingness (rather than assuming it will succeed) is the paper's actual content.

### 4.3 Segmentation and joint learning (auxiliary, not the contribution)

An auxiliary multi-label tumor segmentation head (enhancing tumor / non-enhancing-necrotic core / edema) is trained jointly with the classification head, both to provide tumor-aware pooling and to allow a confirmatory H1/H2 ablation. This is explicitly framed as reproducing established results (COM-Net, MTS-UNET, GMMAS), not as a contribution.

### 4.4 Missing-modality handling

**Training:** modality dropout — randomly zero one or more of the four input channels per training example with a fixed probability schedule, forcing the encoder to remain informative under incomplete input (following the established recipe used in GMMAS and the pediatric missing-MRI literature; not claimed as novel).
**Inference (the experimental design, not merely training-time robustness):** systematically evaluate all clinically meaningful subsets of {T1, T1CE, T2, FLAIR} — at minimum, each single-sequence drop and the common "only T1CE + FLAIR present" scenario — with **zeroing, not imputation**, at test time, since imputation would conflate the missing-modality question with an imputation-quality question the project is not designed to answer.

### 4.5 Domain shift / external validation

The model is trained and its selective-prediction thresholds are calibrated **entirely on UTSW-Glioma** (train/calibration/internal-test split). UCSF-PDGM (post-de-duplication against BraTS-2021) and EGD are held out completely — no hyperparameter, threshold, or normalization-statistic tuning may reference them — and used only once, at the end, as external test sets. This operationalizes "genuinely independent" as required by the prior novelty audits.

### 4.6 Uncertainty / calibration methodology

**Compared methods:** (1) softmax-response threshold + temperature scaling (simple, standard baseline); (2) MC-dropout predictive entropy; (3) deep-ensemble (N≈5) predictive variance; (4) **split conformal prediction / conformal risk control — selected as the PRIMARY mechanism.**

**Why conformal risk control is selected:** it is the only one of the four that provides a *distribution-free, finite-sample coverage guarantee* under an exchangeability assumption between calibration and test data — an assumption domain shift and missingness are known to violate. This makes it possible to ask a sharp, falsifiable empirical question (RQ2/C4): how close does empirical coverage remain to the nominal target when exchangeability is violated by domain shift and by simulated missingness, and in which direction/magnitude does it move? We do not assume the guarantee holds under these conditions; conformal prediction is chosen precisely because it gives the project a numerically precise, pre-specified target (nominal coverage) against which any deviation can be measured, rather than because the guarantee is expected to survive shift. Temperature scaling and MC-dropout produce confidence scores but no formal coverage target to measure deviation against. The method is implementable with standard PyTorch/MONAI code (a calibration-split nonconformity-score computation plus a quantile threshold) and does not require specialized libraries or unrealistic compute.

### 4.7 Selective prediction and risk–coverage analysis

**Coverage** $\phi$: fraction of cases the system predicts on. **Selective risk** $R(f,g)$: risk restricted to the accepted subset (Section 1.2). **Risk–coverage curve:** risk as a function of coverage as the rejection threshold sweeps from accept-all to accept-none. **AURC:** area under that curve, summarizing selective performance in one number, directly comparable across baselines/conditions. These are computed for every one of the four evaluation conditions (complete/missing × internal/external) and for every selective mechanism, and are the primary reporting device for RQ1/RQ2 and claims C1–C5.

### 4.8 Baselines

1. **Always-predict, uncalibrated** (raw softmax) — the naive floor.
2. **Always-predict, calibrated** (temperature scaling) — isolates the value of calibration alone, without selection.
3. **Selective, MC-dropout / deep-ensemble** — isolates the value of ensembling-based uncertainty as a rejection signal.
4. **Selective, conformal risk control** — the primary proposed mechanism.
5. **Reproduced published comparators, where realistically feasible:** an always-predict, tumor-aware, joint-learning model in the style of COM-Net/MTS-UNET/GMMAS (as the strongest "does not abstain" competitor, per the base-paper tiers in Section 6) — reproduced only to the extent needed to serve as a fair always-predict comparison point, not as an attempt to match published SOTA numbers exactly.

### 4.9 Ablation studies (minimum rigorous set)

| Ablation axis | Compared conditions | Answers |
|---|---|---|
| Complete vs. missing modalities | full 4-sequence input vs. each single/pair drop | C2, RQ1 |
| Internal vs. external | UTSW test split vs. UCSF-PDGM/EGD | C3, RQ2/RQ3 |
| Calibrated vs. uncalibrated | raw softmax vs. temperature-scaled | contribution of calibration alone |
| Always-predict vs. selective | baseline 1/2 vs. baseline 3/4 | core RQ1 comparison |
| Uncertainty-method choice | MC-dropout/ensemble vs. conformal | which mechanism is more defensible (user's explicit sub-question) |
| (Confirmatory, secondary) Tumor-aware vs. whole-brain; joint vs. independent seg+classify | with/without tumor-mask pooling; joint vs. two-stage | reproduces established H1/H2 literature results, reported briefly, not as a contribution |

### 4.10 Minimal 6–12 month research plan (phased)

1. **Data audit** (weeks 1–3): download UTSW-Glioma and UCSF-PDGM; initiate EGD data-use agreement immediately; verify per-marker label counts directly from files.
2. **Overlap/leakage audit** (weeks 2–4, parallel): patient-ID cross-check UTSW vs. BraTS-2021/TCGA/UCSF-PDGM (via shipped ID mapping) vs. EGD; build and freeze an exclusion list.
3. **Preprocessing pipeline** (weeks 3–6): registration, skull-strip, N4, resample, normalize; validate on a handful of cases visually.
4. **Freeze splits** (week 6): patient-level train/calibration/internal-test for UTSW; UCSF-PDGM and EGD locked as untouched external test sets.
5. **Baseline model** (weeks 6–10): always-predict backbone, uncalibrated and temperature-scaled.
6. **Calibration/uncertainty implementation** (weeks 10–14): MC-dropout, deep ensemble, conformal risk control.
7. **Missing-modality experiments** (weeks 14–18): modality-dropout training; systematic missing-sequence evaluation.
8. **Selective-prediction experiments** (weeks 18–22): risk–coverage curves, AURC, selective risk at matched coverage, all four mechanisms × four conditions.
9. **External validation** (weeks 22–26): run the frozen pipeline once on UCSF-PDGM and EGD; measure and report empirical vs. nominal coverage without presupposing whether the guarantee holds or degrades.
10. **Statistical analysis** (weeks 26–30): bootstrap CIs, DeLong tests, multiple-comparison correction.
11. **Paper writing and revision** (weeks 30–48+): draft, internal review, submission, buffer for reviewer-requested experiments.

### 4.11 Things that will kill this project

- **Patient-level leakage** (same patient in train and test, or across UTSW/UCSF/BraTS/TCGA due to unremoved overlap) — silently inflates every reported number and can invalidate the whole study if discovered post-hoc.
- **Invalid "external" validation** — using UCSF-PDGM without removing its BraTS-2021 overlap, or tuning any hyperparameter/threshold on UCSF-PDGM/EGD before the final run.
- **Tuning on the external test set** — even a single early "peek" at external performance to adjust the conformal threshold invalidates the coverage-guarantee claim (C4) entirely.
- **Too few IDH-positive/negative or 1p/19q-positive cases** after leakage exclusion — collapsing confidence intervals to the point that risk–coverage curves are not statistically meaningful; must be checked before committing to the final split sizes.
- **Overfitting the calibration/abstention threshold** to the internal calibration split in a way that does not generalize — must be checked by reporting calibration-split vs. test-split coverage discrepancy explicitly.
- **Reporting only AUC** — directly contradicts the entire premise of the project; AUC is necessary but not sufficient and must never appear without ECE/Brier/AURC/coverage alongside it.
- **Ignoring calibration** in favor of discrimination metrics — same failure mode as above.
- **Assuming, in either direction, that conformal coverage will or will not hold under domain shift/missingness without measuring it** — this is precisely RQ2/C4; presupposing the answer (whether optimistically or pessimistically) defeats the purpose of the study. The coverage deviation must be measured, not assumed.
- **Uncontrolled missing-modality assumptions** — e.g., silently imputing instead of zeroing, or evaluating only one arbitrary missing-sequence scenario instead of the systematic subset sweep in Section 4.4.

---

## 5. Statistics, Edge Cases & Reporting

### 5.1 Quantifying the leakage problem — why patient-level splitting is mandatory

BraTS 2021 embeds pre-operative TCGA-GBM (135 cases) and TCGA-LGG (108 cases) under identical subject identifiers, and UCSF-PDGM ships a dedicated BraTS-2021 ID-mapping file *because* a subset of its cases is also in BraTS-2021. Any split that is not enforced at the **patient** level (e.g., accidental slice-level or scan-level splits, or any split performed before de-duplication across UTSW/UCSF-PDGM/EGD/BraTS/TCGA) risks silently placing the same patient's data on both sides of a train/test boundary, or, more insidiously, placing a "different-named" dataset's copy of the same patient into what is reported as an "external" cohort. All splits in this project are defined by patient ID, computed *after* the cross-dataset overlap audit (Section 2, Section 9 step 2), and frozen before any model training begins.

### 5.2 Metrics — primary vs. secondary

**PRIMARY metrics** (directly answer RQ1/RQ2/falsifiable claims C1–C5): selective risk at matched coverage, AURC, risk–coverage curve shape (monotonicity), empirical vs. nominal conformal coverage.
**SECONDARY metrics** (support interpretation and the confirmatory H1–H3 ablations, and RQ3): AUROC, AUPRC, sensitivity, specificity, F1, balanced accuracy (all reported with the segmentation Dice/HD95 for the auxiliary task), Brier score, ECE, reliability diagrams.

### 5.3 Sample size and statistical power — honest discussion

With IDH n≈622 in UTSW (176 mutant / 446 wildtype) split across train/calibration/internal-test, and further reduced by any BraTS/TCGA-overlap exclusions, the internal test set will likely be in the low hundreds — adequate for AUROC/AUC-type comparisons with moderate confidence intervals, but risk–coverage curves computed at fine-grained coverage increments (e.g., 5% steps) on subsets this size will have visibly wide confidence bands at the extremes of coverage (very low or very high). 1p/19q (63 codeleted, pre-exclusion) is underpowered for anything beyond a descriptive, wide-CI exploratory analysis — this must be stated plainly in the paper, not glossed over. External sets (UCSF-PDGM IDH-labeled ~501, EGD IDH-labeled 467) give reasonable external power for IDH specifically, somewhat mitigating the internal-set limitation for the RQ2/RQ3 external questions.

### 5.4 Edge cases

- **Class imbalance:** IDH ~176:446 and 1p/19q ~63:272 — use stratified patient-level splits and class-balanced loss (e.g., focal loss or class weighting); always report PR-AUC alongside ROC-AUC given the imbalance.
- **Ambiguous molecular labels:** where source labels conflict or are marked uncertain in the original clinical record, exclude rather than impute a class — document the exclusion count.
- **Missing modalities beyond the simulated design:** if any UTSW/UCSF/EGD case is naturally missing a sequence (rather than only via simulated dropout), handle it identically to the simulated-missing pipeline and flag it as a naturally-occurring instance in reporting.
- **Severe domain shift:** if UCSF-PDGM or EGD performance collapses to near-chance, this is a valid — and reportable — outcome (supports C3/RQ1 falsification), not a bug to be engineered away post hoc.
- **Calibration failure:** if ECE/Brier worsen substantially externally, report this directly (it replicates the GliomaVista-IDH finding of external Brier 0.32) rather than selectively reporting only favorable calibration conditions.
- **High abstention rates:** if the conformal mechanism rejects an unexpectedly large fraction of cases to hit its nominal coverage under shift, report the coverage-vs-accuracy trade-off transparently rather than silently loosening the threshold to make abstention "look reasonable."
- **High uncertainty but correct prediction:** explicitly report the rate at which rejected cases would have been correctly classified had they not been rejected — this is the concrete cost of abstention and directly informs claim C6.

### 5.5 Confidence intervals and statistical testing

Bootstrap (patient-level resampling, ≥1,000 iterations) 95% CIs for AUROC, AUPRC, AURC, selective risk at fixed coverage, ECE, and Brier score. DeLong's test for paired AUROC comparisons between mechanisms on the same test set. Paired bootstrap or permutation tests for AURC/selective-risk differences between mechanisms. Benjamini–Hochberg correction across the family of ablation comparisons in Section 4.9 to control the false-discovery rate given the number of pairwise tests.

### 5.6 Preprocessing and MRI-specific technical details

Rigid inter-sequence co-registration; skull-stripping (e.g., HD-BET); N4 bias-field correction; resampling to a common isotropic resolution (~1 mm); per-modality intensity normalization (z-score) computed **exclusively from training-split statistics** and then applied unchanged to calibration/internal-test/external data — this is a mandatory leakage control, since computing normalization statistics on pooled train+test (or, worse, train+external) data would leak external-distribution information into the model's effective input space and silently invalidate the domain-shift evaluation.

### 5.7 Dataset/version consistency and molecular-label definitions

IDH status must be defined identically (IDH1/IDH2 mutation by sequencing or established IHC+sequencing algorithm, per WHO 2021 criteria) across UTSW, UCSF-PDGM, and EGD before pooling any statistics; document each cohort's exact labeling methodology in the paper's methods section, and flag any cohort-specific differences in assay/era (e.g., older cases assessed under pre-2021 WHO criteria) as a potential source of label heterogeneity, not silently normalized away.

### 5.8 Reporting standards

- **TRIPOD+AI** (Collins et al., *BMJ* 2024;385:e078378, DOI 10.1136/bmj-2023-078378, published 16 April 2024) — the current, updated reporting guideline for AI/ML clinical prediction models; explicitly supersedes the 2015 TRIPOD checklist, which should no longer be used. This project should follow TRIPOD+AI for the overall prediction-model reporting structure (verified current as of this specification).
- **CLAIM 2024 Update** (Tejani, Klontzas, CLAIM 2024 Update Panel et al., *Radiology: Artificial Intelligence* 2024;6(4):e240300, DOI 10.1148/ryai.240300, published 29 May 2024) — the current medical-imaging-AI-specific checklist; use alongside TRIPOD+AI for imaging-specific items (acquisition protocol, reference-standard definition, model/code/data availability).
- **CONSORT-AI / SPIRIT-AI** — relevant only to prospective clinical trials of AI interventions; **not applicable** to this retrospective, non-interventional study, and should not be cited as if they were.
- Both TRIPOD+AI and CLAIM 2024 were verified current at the time of this specification (August 2026); re-check for any newer update immediately before manuscript submission, since these guidelines are actively maintained.

---

## 6. Base Papers — Tiered by How Closely They Match, Newest First

### Tier 1 — Closest matches to the complete research problem

**1. GMMAS** — Liu et al., "Towards a Multimodal MRI-Based Foundation Model for Multi-Level Feature Exploration…" *Medicine Advances* 2026, DOI 10.1002/med4.70064 (also arXiv 2501.17758, preprint version). **Peer-reviewed** (published version). Dataset: pooled BraTS + TCIA + independent Xiangya Hospital cohort (~1,962 mpMRI cases pooled; external Xiangya cohort reported with per-cohort AUCs). MRI: T1/T1CE/T2/FLAIR. Task: joint segmentation + IDH/1p19q/MGMT/grade. Architecture: CNN-Transformer hybrid with aleatoric task-weighting and MC-dropout epistemic uncertainty. Uncertainty method: MC-dropout, used for **training-time pseudo-label filtering only**. Calibration method: Tumor-CutMix label smoothing; reports ECE/reliability curves. Abstention/selective prediction: **NO** — verified from full text, uncertainty never gates an inference-time decision. Risk–coverage/AURC: **NO**. Missing-modality handling: YES, via a distillation+contrastive adaptation module (always predicts). External validation: YES (Xiangya cohort). Main results: internal IDH AUC 0.982, external IDH AUC ~0.924; 1p/19q external ~0.896–0.902. Limitations: no formal coverage guarantee, no inference-time trust mechanism, no leakage audit against TCGA-linked public subsets. **Similarity to our proposal:** highest of any paper — matches on tumor-aware joint learning, multimodal fusion, missing-modality robustness, some uncertainty, external validation. **Difference:** no inference-time abstention, no risk–coverage/AURC, no formal coverage-guarantee testing under shift. **Use as:** the primary "always-predict SOTA" comparison baseline (Section 4.8, baseline 5) and the paper's central related-work foil.

**2. Elyassirad et al.** — "Uncertainty-Aware IDH Mutation Status Classification with Conformal Prediction," *Journal of Imaging Informatics in Medicine* 2026;39:1217–1224, DOI 10.1007/s10278-025-01580-w. **Peer-reviewed.** Dataset: UCSF (train/calibrate) → UPenn (external test). MRI: T1/T1CE/T2/FLAIR (complete-sequence inclusion criterion). Task: IDH classification only (no segmentation). Architecture: 3D CNN + logistic-regression-style ensemble with conformal prediction. Uncertainty method: split conformal prediction. Calibration: **NO** ECE/Brier/reliability reporting. Abstention: YES, but at a **single fixed operating point** (nonconformity threshold 0.01 → coverage 0.9917, 22.16% of external cases flagged uncertain); removing flagged cases raised retained-subset AUROC/AUPRC from 0.7980/0.2583 to 0.8592/0.5217. Risk–coverage curve/AURC: **NO** — no sweep across thresholds. Missing-modality handling: **NO** — all four sequences required by design. Domain shift: YES (UCSF→UPenn). Main result: external AUROC dropped from ~internal levels to 0.734 pre-filtering. Limitations: single operating point, no missing-modality test, no calibration metrics beyond conformal coverage itself. **Similarity:** the single most dangerous paper for this project's novelty — same task, same core mechanism (conformal), same domain-shift framing. **Difference:** no risk–coverage/AURC sweep, no missing-modality axis, no ECE/Brier. **Use as:** the primary conformal-method baseline/comparator; the paper's method (single-threshold conformal) is the most literal ablation this project must extend and outperform on the risk–coverage/AURC and missing-modality dimensions to justify publication.

### Tier 2 — Papers matching two or more major dimensions

**3. RISEN** — Liang et al., *European Radiology* 2026, DOI 10.1007/s00330-026-12622-4. **Peer-reviewed.** 2,170 patients, 5 clinical institutions + one public dataset. Task: glioma grading + IDH via a robust incomplete-sequence-estimation network (imputation-based). Missing-modality: YES (its central contribution). Uncertainty/abstention/risk–coverage: **NO** — always predicts after imputing. External validation: YES (multi-institution). **Use as:** the strongest published missing-modality-robust IDH baseline; a fair "imputation-based always-predict" comparator against this project's "zero-and-possibly-abstain" approach.

**4. Yogananda et al.** — "Bridging the clinical gap: Confidence informed IDH prediction in brain gliomas using MRI and deep learning," *Neuro-Oncology Advances* 2025;7(1):vdaf142, DOI 10.1093/noajnl/vdaf142. **Peer-reviewed.** 2,481 glioma cases, 8 institutions (explicitly including UTSW, UCSF, EGD, UPenn — the same cohort family this project uses). Task: IDH classification with a Bayesian-logistic-regression-derived confidence score. Calibration: YES — Brier score 0.0125 reported, well-calibrated. Abstention/selective prediction: **NO** — every case is labeled (fully automated majority-vote pipeline); the confidence score is reported as "an additional layer of assurance," never thresholded to withhold a prediction. Missing-modality: explicitly listed as an **unaddressed limitation** in the paper's own discussion. Risk–coverage/AURC: **NO**. **Similarity:** uses the same dataset family and a calibrated confidence score. **Difference:** never abstains, never tests missing modalities, no risk–coverage framework. **Use as:** the strongest calibration-only baseline, and the paper that MUST be explicitly cited and differentiated from given the identical dataset overlap — the differentiation must be argued on mechanism (abstention + risk–coverage), not on data novelty.

**5. FoundBioNet** — Farahani et al., MICCAI 2025, DOI 10.1007/978-3-032-04981-0_25 (arXiv 2508.06756). **Peer-reviewed.** 1,705 patients / 6 datasets. Tumor-aware (TAFE + Cross-Modality Differential modules) on a SWIN-UNETR/BrainSegFounder backbone. IDH only. No missing-modality handling, no uncertainty, no calibration. External IDH AUCs ~90.58/88.08/65.41/80.31% across EGD/TCGA/IvyGAP/RHUH/UPenn. **Use as:** the strongest tumor-aware/foundation-style accuracy benchmark to cite as the discrimination ceiling this project is not trying to beat, only to approach while adding trustworthiness.

### Tier 3 — Papers matching one major dimension but providing an essential methodological comparison

**6. MTS-UNET** — arXiv 2503.06828. **Preprint.** 3D joint segmentation + IDH + 1p/19q + grade, TAFE+CMD modules, BrainSegFounder-Tiny backbone (62M params, 96³ crops). No missing-modality, no uncertainty. **Use as:** the closest tumor-aware joint-learning architecture reference for the auxiliary segmentation head design (Section 4.3), clearly labeled as a preprint.

**7. GlioMT** — *npj Digital Medicine* 2025, DOI 10.1038/s41746-025-01530-4. **Peer-reviewed.** 2D multimodal ViT+BERT, 1,053 patients, external IDH AUC 0.915 (TCGA)/0.981 (UCSF), 1p/19q AUC 0.854/0.806 on small external subsets (86/103 cases). No segmentation, no missing-modality, no uncertainty/calibration. **Use as:** the strongest multimodal-transformer external-validation benchmark and a caution about small external-subset confidence intervals (directly informs Section 5.3).

**8. Zadorozhny et al.** — "Rescuing referral failures during automated diagnosis of domain-shifted medical images," arXiv:2311.16766. **Preprint.** Not glioma-specific (retinal fundus, chest X-ray). Documents that predictive-uncertainty-based referral/selective prediction produces **non-monotonic referral curves and performance drops of up to ~50% at high referral rates (>70%)** under covariate shift. **Use as:** the key outside-domain evidence motivating RQ1/RQ2 as a genuinely open (not pre-answered) empirical question, and the direct precedent for what a "failed" result (C5 falsified) would look like.

**9. Liang, Peng & Sun** — "Selective Classification Under Distribution Shifts," *Transactions on Machine Learning Research* 2024. **Peer-reviewed (TMLR).** General methodological formalization of selective classification failure/behavior under covariate and label shift, outside medical imaging. **Use as:** the theoretical grounding for why exchangeability-breaking shift is expected to threaten conformal coverage guarantees (directly underlies C4/RQ2), and as the general (non-glioma) related-work anchor.

**10. Kim et al.** — "Diagnostic Performance of Deep Learning Models for MGMT Promoter Methylation Prediction," *Cancers* 2022, DOI 10.3390/cancers14194827, PMID 36230750. **Peer-reviewed.** 420 model variants tested; 337/420 (80.2%) not significantly different from chance; BraTS-2021 challenge winner dropped to AUROC 0.562/accuracy 0.548 on the external SNUH cohort (n=400). **Use as:** the evidentiary basis for excluding MGMT entirely from this project's scope (Section 2.1, Section 8), and as a cautionary precedent about external-validation collapse for MRI-based molecular prediction generally.

### Pattern worth naming in the paper

Across every Tier 1–3 paper, a consistent pattern holds: **the field has separately solved (a) discrimination (FoundBioNet, GlioMT reach AUCs ≥0.90 externally), (b) missing-modality robustness (RISEN, GMMAS), and (c) point-estimate calibration/uncertainty reporting (Yogananda et al., GMMAS's ECE/reliability curves) — but no paper closes the loop into an inference-time decision that uses that uncertainty to withhold a prediction, and evaluates whether doing so remains trustworthy specifically under the two conditions (missing sequences, cross-institutional shift) that the field's own evidence shows break both discrimination and calibration.** Elyassirad et al. comes closest by adding a single-threshold conformal abstention step, but stops short of the systematic risk–coverage characterization and the missing-modality axis. This consistent gap — established components, un-integrated into a tested trust decision — is what remains meaningful to evaluate, independent of whether the eventual answer is positive or negative.

---

## 7. Reference Papers — 2024 Onward Only, Newest First Within Each Theme

*(Preprint status marked explicitly; "not verified" used where a detail could not be confirmed in this pass.)*

**MRI-based glioma molecular prediction / IDH classification**
- Liu et al., GMMAS, *Medicine Advances* 2026, DOI 10.1002/med4.70064 — peer-reviewed — the closest competing full system; core related-work comparator.
- Elyassirad et al., conformal IDH, *J Imaging Inform Med* 2026, DOI 10.1007/s10278-025-01580-w — peer-reviewed — closest single-mechanism competitor.
- Yogananda et al., confidence-informed IDH, *Neuro-Oncology Advances* 2025, DOI 10.1093/noajnl/vdaf142 — peer-reviewed — same dataset family, calibration-only comparator.
- "AI-vs-physician IDH" (GliomaVista-IDH), *npj Digital Medicine* 2026, DOI 10.1038/s41746-026-02695-2 — peer-reviewed — motivating evidence of external calibration collapse (Brier 0.32).
- Foundation-model IDH benchmark, arXiv 2606.23172, 2026 — **preprint** — benchmarks foundation-model embeddings for IDH calibration under shift (external ECE ≈0.07); complementary motivating evidence.
- FoundBioNet, Farahani et al., MICCAI 2025, DOI 10.1007/978-3-032-04981-0_25 — peer-reviewed — accuracy-ceiling benchmark.
- GlioMT, *npj Digital Medicine* 2025, DOI 10.1038/s41746-025-01530-4 — peer-reviewed — multimodal transformer benchmark.
- MTS-UNET, arXiv 2503.06828, 2025 — **preprint** — architecture reference for the auxiliary segmentation head.
- Shen Wen et al., one-stage multi-task network, *Biomed Signal Process Control* 2025, S1746809425004343 — peer-reviewed — joint seg+molecular competing method.
- CMAF / "From Anatomy to Genomics," *Bioengineering* 2025, DOI 10.3390/bioengineering12090979 — peer-reviewed — joint seg+molecular competing method.
- van der Voort et al. (COM-Net), *Neuro-Oncology* 2023, DOI 10.1093/neuonc/noac166 — peer-reviewed — foundational 3D joint-learning reference (pre-2024, retained as necessary foundational work).
- Chakrabarty et al., 2.5D hybrid multi-task, *Neuro-Oncology Advances* 2023, DOI vdad023 — peer-reviewed — foundational multi-center IDH/1p19q reference.
- IDH/1p19q pooled meta-analysis, *European Radiology* 2025, DOI 10.1007/s00330-025-11898-2 (arXiv 2411.02426) — peer-reviewed — establishes literature-wide pooled sensitivity/specificity baselines.

**Missing-modality / incomplete-MRI learning**
- RISEN, Liang et al., *European Radiology* 2026, DOI 10.1007/s00330-026-12622-4 — peer-reviewed — strongest recent missing-modality IDH/grading system.
- SSL-MISS-Net, *npj Precision Oncology* 2025, DOI 10.1038/s41698-025-01112-3 — peer-reviewed — incomplete sequences AND incomplete labels.
- GMENet, arXiv 2605.23183, 2026 — **preprint** — generative mixture-of-experts for incomplete sequences.
- Pediatric missing-MRI segmentation/prognosis, *npj Precision Oncology* 2026, DOI 10.1038/s41698-025-01269-x — peer-reviewed — evidence that modality-dropout training is an established, low-risk recipe (≤0.04 Dice drop).

**Uncertainty and calibration in medical imaging (general, non-glioma)**
- Zadorozhny et al., referral failures under domain shift, arXiv 2311.16766 — **preprint** — key negative-result precedent for selective prediction under shift.
- Liang, Peng & Sun, "Selective Classification Under Distribution Shifts," TMLR 2024 — peer-reviewed — theoretical grounding.

**Selective prediction / abstention / reject-option and conformal prediction / risk control**
- Elyassirad et al. 2026 (as above) — the field's only glioma-specific conformal-abstention paper.
- CONSeg, arXiv 2502.21158 / AJNR 2025, DOI 10.3174/ajnr.A8914 — **preprint/peer-reviewed (AJNR)** — conformal *segmentation* uncertainty (not classification abstention) — a related but distinct application of conformal methods in this domain.

**Domain shift / domain generalization / external validation**
- GliomaVista-IDH physician comparison (as above) — direct evidence of external calibration collapse.
- Elyassirad et al. 2026 (as above) — direct evidence of external AUROC collapse (0.90→0.734).

**Tumor-aware / ROI-aware learning; segmentation+molecular classification**
- FoundBioNet, MTS-UNET, CMAF, Shen Wen et al., GMMAS (all above) — establish tumor-aware joint learning as a solved architectural problem this project deliberately does not re-solve.

**Dataset papers**
- Reddy et al., UTSW-Glioma, *Scientific Data* 2026, DOI 10.1038/s41597-026-07274-4 — peer-reviewed — primary dataset.
- Calabrese et al., UCSF-PDGM, *Radiology: AI* 2022, DOI 10.1148/ryai.220058 — peer-reviewed — external dataset (pre-2024, retained as necessary).
- van der Voort et al., EGD, *Data in Brief* 2021, DOI 10.1016/j.dib.2021.107191 — peer-reviewed — external dataset (pre-2024, retained as necessary).
- Kim et al., MGMT unpredictability, *Cancers* 2022, DOI 10.3390/cancers14194827, PMID 36230750 — peer-reviewed — basis for MGMT exclusion (pre-2024, retained as necessary).

**Reporting standards**
- Collins et al., TRIPOD+AI, *BMJ* 2024;385:e078378, DOI 10.1136/bmj-2023-078378 — peer-reviewed — primary reporting checklist for this project.
- Tejani, Klontzas et al., CLAIM 2024 Update, *Radiology: AI* 2024;6(4):e240300, DOI 10.1148/ryai.240300 — peer-reviewed — imaging-specific reporting checklist.
- Moons et al., PROBAST+AI, *BMJ* 2025;388:e082505 — peer-reviewed — risk-of-bias/applicability companion tool to TRIPOD+AI; recommended for the paper's methods appendix, "not verified" beyond the citation surfaced in this pass (bibliographic detail only, not independently read in full).

*Note: several foundational items pre-date 2024 (COM-Net 2023, Chakrabarty 2023, UCSF-PDGM 2022, EGD 2021, Kim et al. MGMT 2022) and are retained only because they are structurally necessary (dataset papers, the MGMT-exclusion evidence, and the canonical 3D joint-learning baseline) — consistent with the instruction to prioritize 2024-onward but not omit essential foundational work.*

---

## 8. Where the Novelty Actually Is

### 8.1 Being direct about what is exhausted

The following are **NOT** available as novelty claims for this paper, because each is independently and repeatedly established in the literature synthesized above: generic glioma detection; generic IDH classification from MRI; CNN-based classification; Transformer-based classification; CNN–Transformer hybrid architectures; multimodal MRI fusion; tumor-aware/ROI-aware learning; uncertainty estimation (as a reported number); calibration (as a reported number); missing-modality robustness (as an always-predict property); external validation (as a single-cohort test); and joint segmentation+molecular-classification multi-task learning. Claiming novelty on any of these, individually, invites an immediate and correct rejection.

### 8.2 Where genuine, achievable novelty remains

The surviving gap is narrow and specific: **no paper performs inference-time calibrated selective prediction/abstention for MRI-based glioma IDH classification, formally characterized via risk–coverage/AURC analysis, evaluated jointly under BOTH missing MRI modalities AND genuine cross-institutional domain shift, with explicit empirical measurement of how close empirical coverage remains to nominal coverage under those conditions — without assuming in advance that the guarantee either holds or degrades.** Elyassirad et al. (2026) reaches the single closest point — conformal abstention with domain shift — but stops at one operating point, omits the missing-modality axis entirely, and reports no risk–coverage curve, AURC, or calibration metrics beyond raw coverage. GMMAS integrates more components (joint learning, missing-modality robustness, some calibration) but never uses its uncertainty for an inference-time decision at all.

**Is this genuinely novel enough, or merely a combination of known techniques?** The techniques (conformal prediction, temperature scaling, MC-dropout, risk–coverage analysis) are all standard and none is invented here. The novelty is empirical, not methodological: whether the *specific, clinically motivated failure modes* of MRI-based glioma genotyping (missing sequences; institutional shift) cause selective prediction to behave well or to fail — as it is documented to fail in other shifted medical-imaging tasks (Zadorozhny et al., non-monotonic referral curves, up to ~50% performance drops at high referral rates). This question cannot be answered by citation; it requires the specific experiment. A credible negative result (coverage guarantee void under shift, non-monotonic risk–coverage curves) is pre-registered as an equally valid, publishable outcome — which is the strongest available evidence that this is a genuine scientific question rather than an engineering exercise dressed up as one.

**Strongest reviewer objections and responses:**
- *"Elyassirad et al. already did conformal IDH abstention with external validation — this is done."* → Their evaluation is a single operating point with no risk–coverage sweep, no AURC, no missing-modality axis, and no calibration metrics (ECE/Brier); this project's contribution is precisely the systematic characterization they do not provide, on both failure axes jointly, not just one.
- *"GMMAS already does uncertainty, missing-modality robustness, and calibration together — this is done."* → Verified from full text: GMMAS's uncertainty is used exclusively for training-time pseudo-label selection and task weighting; it never gates an inference-time prediction. There is no abstention, no risk–coverage curve, and no coverage-guarantee test anywhere in GMMAS.
- *"Selective prediction under distribution shift is already a mature, well-understood technique (per Zadorozhny et al., Liang/Peng/Sun) — applying it to a new domain is not novel."* → Correct that the technique is mature; the contribution is the domain-specific empirical finding for glioma IDH, including the possibility (consistent with prior negative results elsewhere) that it fails here too — which is itself new, actionable knowledge for anyone building a deployable glioma-genotyping tool.
- *"MGMT/1p19q data exist — why not predict all three markers for a stronger paper?"* → MGMT is excluded on documented chance-level external evidence (Kim et al. 2022); adding it would weaken, not strengthen, the paper. 1p/19q is retained only as an explicitly labeled exploratory secondary analysis given its small positive count (Section 5.3), to avoid overclaiming on underpowered data.

### 8.3 The recommended single sentence describing this project

**"This project provides the first systematic risk–coverage analysis and empirical coverage characterization of inference-time calibrated selective prediction for MRI-based glioma IDH classification, testing — rather than assuming — whether abstaining on low-confidence cases genuinely improves reliability, and whether conformal coverage remains close to nominal, under missing MRI sequences and cross-institutional domain shift."**

---

## 9. Immediate Next Steps

**Do now, in this order:**
1. **Dataset acquisition + patient-level label audit.** Download UTSW-Glioma from TCIA; download UCSF-PDGM from TCIA; independently verify (do not trust this document alone) the exact per-marker IDH/1p19q/MGMT counts by parsing the actual clinical-metadata files. Simultaneously (do not wait), submit the EGD data-use agreement request via Health-RI (servicedesk@health-ri.nl) — this has the longest external lead time in the project.
2. **Overlap/leakage audit.** Cross-check UTSW patient IDs against BraTS-2021, TCGA-GBM, TCGA-LGG, and UCSF-PDGM (using the UCSF-PDGM/BraTS-2021 ID-mapping file) for any accidental duplication; build a written, versioned exclusion list before any modeling work begins.
3. **Freeze train/validation/external-test cohorts.** Patient-level stratified split of UTSW into train/calibration/internal-test; lock UCSF-PDGM (post-exclusion) and EGD as untouched external test sets with no access for tuning.
4. **Baseline implementation.** Build the 3D SegResNet-style backbone with the auxiliary segmentation head; train the always-predict, uncalibrated model; confirm it reaches a sane internal AUROC before adding any trust machinery.
5. **Calibration.** Add temperature scaling; report ECE/Brier/reliability on the internal test split.
6. **Selective prediction.** Implement MC-dropout, deep-ensemble, and conformal risk control mechanisms; compute risk–coverage curves and AURC internally first.
7. **Missing-modality experiments.** Add modality-dropout training; run the systematic missing-sequence evaluation grid (Section 4.4) internally.
8. **Domain-shift experiments.** Run the fully frozen pipeline, once, on UCSF-PDGM and EGD; measure and report empirical vs. nominal coverage (without presupposing the guarantee holds or fails) and calibration degradation.
9. **Statistical analysis.** Bootstrap CIs, DeLong tests, multiple-comparison correction, across all baselines × conditions.
10. **Paper writing.** Structure around TRIPOD+AI and CLAIM 2024, explicitly positioning against GMMAS and Elyassirad et al. as the two closest works, per Section 6/8.

**What should NOT be done yet:** do not touch UCSF-PDGM or EGD for any purpose other than the final, single evaluation run in step 8 — no early "sanity checks" on external data, however tempting, since any such peek compromises the external-validity and coverage-guarantee claims that are the paper's core contribution. Do not begin architecture experimentation beyond the single selected backbone (Section 4.1) — architecture search is explicitly out of scope and would consume time better spent on the selective-prediction experiments. Do not add MGMT prediction under any circumstance without new, strong, externally validated evidence overturning Kim et al. (2022).

### Final recommendation: **GO.**

The targeted, hostile novelty pass found no paper — including the two closest, GMMAS and Elyassirad et al. 2026 — that performs the specific integrated evaluation this project proposes. The remaining gap is real, narrowly scoped, honestly falsifiable, and implementable by a solo researcher on a single 16–24 GB GPU within a 6–12 month timeline using UTSW-Glioma as a clean primary dataset and UCSF-PDGM/EGD as genuinely independent external cohorts once leakage exclusions are applied. **Freeze this topic. Do not widen the scope to chase additional novelty; the risk in this project is scope creep, not insufficient novelty.**
