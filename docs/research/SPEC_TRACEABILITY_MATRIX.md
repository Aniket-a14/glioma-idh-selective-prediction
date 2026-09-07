# SPEC TRACEABILITY MATRIX

Prevents requirements from disappearing during implementation. Every research question, falsifiable claim, and SPEC-mandated requirement resolves to a dataset, condition, metric, statistical test, artifact, phase, and a specific manuscript table or figure.

**Closure rule:** no row may have an empty cell, and no artifact may exist without a row pointing at it. Checked at Gate D (per phase) and Gate F (whole project).

---

## Part 1 — Research questions

| RQ | Dataset(s) | Model / mechanism | Condition(s) | Primary metric | Statistical test | Artifact | Phase | Manuscript |
|---|---|---|---|---|---|---|---|---|
| **RQ1** — does rejecting low-confidence cases monotonically lower selective risk & AURC vs. always-predict, under missingness and shift? | UTSW internal test; UCSF-PDGM; EGD | M1/M2 (always-predict) vs. M3/M4/M5 (selective) | all 18 (6 modality × 3 cohort) | Selective risk @ matched coverage; AURC; RC monotonicity | Paired bootstrap on ΔAURC and Δselective-risk; BH-corrected | `artifacts/predictions/*.parquet` → `results/rq1_*.json` | 09, 10, 12, 13 | **Fig 2** (RC curves, 2×2 panel), **Table 3** (AURC ± CI) |
| **RQ2** — does empirical coverage stay near nominal under missingness and shift? | UTSW internal test; UCSF-PDGM; EGD | M5 conformal, α ∈ {0.05, 0.10, 0.20} | all 18 | Empirical − nominal coverage deviation | Bootstrap CI on deviation vs. frozen ±5pp band (**D-004**) | `results/rq2_coverage.json` | 09, 12, 13 | **Fig 3** (nominal vs. empirical), **Table 4** |
| **RQ3** — does calibration degrade internal → external? | UTSW internal test vs. UCSF-PDGM, EGD | M1 raw, M2 temperature-scaled | `full` + missing, both cohort tiers | ECE; Brier; reliability | Bootstrap CI on ΔECE, ΔBrier (internal vs. external) | `results/rq3_calibration.json` | 07, 12, 13 | **Fig 4** (reliability diagrams), **Table 5** |
| **RQ4** — does selective behavior hold for 1p/19q? *(exploratory)* | UTSW (1p19q subset); UCSF-PDGM (410/501); EGD (259) | Frozen-encoder probe head (**D-007**) | `full` + `−T1CE` only | AURC; selective risk; coverage | Bootstrap CI only — **no inferential claim** | `results/rq4_1p19q_exploratory.json` | 10, 12, 13 | **Supp. Table S3**, labelled exploratory |

---

## Part 2 — Falsifiable claims

Each row carries the pre-registered refutation criterion **verbatim**, so the decision to support or refute is mechanical rather than interpretive.

| Claim | Refuted if (verbatim, SPEC §1.4) | Dataset | Condition | Metric | Test | Artifact | Phase | Manuscript |
|---|---|---|---|---|---|---|---|---|
| **C1** selective < always-predict risk, internally | *"Selective risk at any fixed coverage ≥ always-predict risk; risk–coverage curve is flat or increasing as coverage decreases."* | UTSW internal test | `full` | Selective risk @ φ ∈ {0.9,0.8,0.7,0.6,0.5}; AURC | Paired bootstrap, M5 vs. M1/M2 | `results/c1.json` | 09 | Fig 2a, Table 3 |
| **C2** advantage survives missing modalities | *"Selective-risk advantage over always-predict disappears or reverses when 1–2 sequences are dropped."* | UTSW internal test | 5 missing conditions | Δ selective risk @ matched φ | Paired bootstrap; BH across 5 | `results/c2.json` | 09 | Fig 2b, Table 3 |
| **C3** advantage survives external shift | *"No selective-risk advantage on UCSF-PDGM/EGD relative to always-predict, at matched coverage."* | UCSF-PDGM; EGD | `full` + missing | Δ selective risk @ matched φ | Paired bootstrap; BH | `results/c3.json` | 12 | Fig 2c–d, Table 3 |
| **C4** coverage deviation is characterizable | *"The deviation cannot be reliably characterized — e.g., empirical coverage estimates are too noisy/unstable (given sample size) to distinguish 'coverage preserved' from 'coverage degraded' at the pre-registered tolerance."* | UTSW; UCSF-PDGM; EGD | all 18 | \|empirical − nominal\| vs. **±5pp** | Bootstrap CI half-width vs. band | `results/c4.json` | 09, 12 | Fig 3, Table 4 |
| **C5** RC curves stay monotonic | *"Curves become non-monotonic under shift/missingness, mirroring documented failures in retinal/CXR imaging."* | all three cohorts | all 18 | Σ max(0, R(φᵢ) − R(φⱼ)) for φᵢ<φⱼ | Bootstrap CI on total violation magnitude | `results/c5_monotonicity.json` | 09, 12 | Fig 2 (violation markers), Table 3 |
| **C6** abstention tracks error | *"Abstained cases are no more likely to be erroneous than randomly selected cases of equal size."* | all three cohorts | all 18 | Error rate in rejected vs. matched-size random subset; rejected-but-correct rate | Permutation test | `results/c6.json` | 09, 12 | **Table 6**, Fig 5 |

---

## Part 3 — SPEC requirements → phase

| SPEC § | Requirement | Status | Phase | Artifact |
|---|---|---|---|---|
| §2.1, §2.3 | UCSF-PDGM BraTS-2021 overlap resolved before "external" | MISSING | 03 | `manifests/exclusions_ucsf_brats.json` + hash |
| §2.7, §9.1 | EGD DUA initiated immediately | MISSING | **02, day 1** | `docs/research/protocols/DATA_ACCESS_LOG.md` |
| §9.1 | Per-marker counts verified from files, not trusted (**D-009**) | MISSING | 03 | `manifests/label_verification.md` |
| §4.1 | 3D SegResNet-style MONAI backbone; no architecture search | MISSING | 06 | `src/glioma_selective/models/` |
| §4.3 | Auxiliary segmentation head, tumor-aware pooling (confirmatory) | MISSING | 06 | same |
| §4.4 | Modality dropout in training | MISSING | 08 | `training/modality_dropout.py` |
| §4.4 | Inference: systematic subset sweep, **zeroed not imputed** | MISSING | 08 | `evaluation/modality_conditions.py` |
| §4.5 | Thresholds/normalization fitted only on UTSW | MISSING | 05, 07 | `manifests/normalization_stats.json` |
| §4.6 | Four mechanisms: softmax+temp, MC-dropout, ensemble, conformal | MISSING | 07 | `calibration/`, `uncertainty/` |
| §4.7 | Coverage, selective risk, RC curve, AURC | MISSING | 09 | `selective/` |
| §4.8 | Five baselines incl. tumor-aware comparator (**D-006**) | MISSING | 06, 09 | `results/baselines/` |
| §4.9 | Six ablation axes | MISSING | 10 | `results/ablations/` |
| §5.1 | Patient-level splitting after de-duplication | MISSING | 05 | `manifests/splits.json` + hash |
| §5.2 | Primary/secondary metric hierarchy preserved | MISSING | 13 | `evaluation/` refuses AUROC alone |
| §5.4 | Class imbalance: stratified splits + class-balanced loss; PR-AUC always reported | MISSING | 05, 06 | config + `results/` |
| §5.4 | Ambiguous labels excluded, not imputed; count documented | MISSING | 03 | exclusion manifest |
| §5.4 | Rejected-but-correct rate reported (C6 cost of abstention) | MISSING | 09 | `results/c6.json` |
| §5.5 | Bootstrap ≥1000, DeLong, paired bootstrap/permutation, BH | MISSING | 13 | `statistics/` |
| §5.6 | Registration, HD-BET skull-strip, N4, ~1mm resample, z-score from **train only** | MISSING | 04 | `preprocessing/` |
| §5.7 | IDH label definition harmonized across cohorts; assay/era differences flagged | MISSING | 03 | `manifests/label_definitions.md` |
| §5.8 | TRIPOD+AI and CLAIM 2024; freshness re-check before submission | MISSING | 14 | `paper/checklists/` |
| §8.2 | Differentiation vs. GMMAS, Elyassirad, Yogananda, RISEN, FoundBioNet | MISSING | 14 | manuscript Related Work |
| §1.5, §8.2 | Negative results preserved and reported | MISSING | ongoing | `paper/NEGATIVE_RESULTS.md` |

**Status legend:** EXISTS AND VALID · EXISTS BUT NEEDS MODIFICATION · **MISSING** · NOT APPLICABLE · BLOCKED · REQUIRES HUMAN DECISION.
Everything is MISSING at plan time: the repository was empty apart from the two source documents. Nothing existing is being rebuilt, because nothing exists.

---

## Part 4 — Reverse trace (manuscript → evidence)

Every planned manuscript element must trace back. Populated as figures are produced; empty right-hand cells at Gate F are a blocking defect.

| Element | Content | Generated from | Answers |
|---|---|---|---|
| Fig 1 | Cohort flow diagram (CONSORT-style) | `manifests/*` | §5.1 provenance |
| Fig 2 | Risk–coverage curves, 2×2 (complete/missing × internal/external) | `results/c1.json c2.json c3.json c5_*.json` | RQ1; C1, C2, C3, C5 |
| Fig 3 | Nominal vs. empirical coverage, per condition | `results/rq2_coverage.json` | RQ2; C4 |
| Fig 4 | Reliability diagrams, internal vs. external | `results/rq3_calibration.json` | RQ3 |
| Fig 5 | Abstention–error enrichment | `results/c6.json` | C6 |
| Table 1 | Cohort characteristics | `manifests/cohort_manifest.json` | §2 |
| Table 2 | Exclusions with reasons | `manifests/exclusions_*.json` | §5.1 |
| Table 3 | AURC + selective risk @ matched coverage, all mechanisms × conditions | `results/` | RQ1; C1–C3, C5 |
| Table 4 | Coverage deviation vs. ±5pp band | `results/c4.json` | RQ2; C4 |
| Table 5 | Discrimination + calibration (AUROC, AUPRC, ECE, Brier) | `results/` | RQ3; §5.2 |
| Table 6 | Abstention analysis incl. rejected-but-correct rate | `results/c6.json` | C6; §5.4 |
| Supp S1 | Ablations (six axes) | `results/ablations/` | §4.9 |
| Supp S2 | Auxiliary segmentation Dice/HD95 | `results/segmentation.json` | §4.3, §5.2 |
| Supp S3 | 1p/19q exploratory | `results/rq4_*.json` | RQ4 |
| Supp S4 | TRIPOD+AI and CLAIM 2024 checklists | `paper/checklists/` | §5.8 |
