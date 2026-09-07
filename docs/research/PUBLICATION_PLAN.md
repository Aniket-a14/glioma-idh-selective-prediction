# PUBLICATION PLAN

The project ends at **publication**, not at "training complete."

---

## 1. Venue

**Target type** (SPEC header): single original-research paper, journal or MICCAI-tier conference.

| Tier | Venue | Fit |
|---|---|---|
| 1 | *Radiology: Artificial Intelligence* | Best fit — published both the UCSF-PDGM dataset paper and CLAIM 2024; explicitly receptive to reliability/calibration studies and to negative results |
| 1 | *Neuro-Oncology Advances* | Published Yogananda et al. on the same dataset family; clinically framed |
| 2 | *npj Precision Oncology* | Broader, molecular-oncology framing |
| 2 | MICCAI / ISBI | Faster, but page limits fight the reporting-checklist requirements; a rebuttal cycle rather than a revision cycle |

**Recommendation:** *Radiology: AI* first. Its audience already accepts that external calibration collapse is a finding worth publishing, which matters because this paper may report exactly that. Decide finally in Phase 14 when the result's shape is known — a strongly negative result may fit a clinically-framed venue better than a methods-framed one.

---

## 2. Framing discipline

The manuscript is an **empirical trustworthiness/reliability study**. It is not a new-architecture paper, and the backbone must never be presented as a contribution.

The frozen one-sentence description (SPEC §8.3) anchors the abstract:

> *"This project provides the first systematic risk–coverage analysis and empirical coverage characterization of inference-time calibrated selective prediction for MRI-based glioma IDH classification, testing — rather than assuming — whether abstaining on low-confidence cases genuinely improves reliability, and whether conformal coverage remains close to nominal, under missing MRI sequences and cross-institutional domain shift."*

**The word "first" does not ship without a fresh novelty check** dated close to submission (**D-010**).

**If the result is negative**, the framing does not become apologetic. "Selective prediction degrades under cross-institutional shift for glioma IDH classification, and here is precisely how" is a stronger clinical contribution than a marginal AUROC improvement, and it is what the study was pre-registered to be able to report.

---

## 3. Required differentiation

Drafted in Phase 14, from the master plan §5 table. Each of the five must be addressed explicitly in Related Work and again in Discussion.

| Work | The sentence that must appear |
|---|---|
| **Elyassirad et al. 2026** | *The* closest competitor. Their conformal abstention uses a single fixed operating point; we provide the risk–coverage sweep, AURC, the missing-modality axis, and calibration metrics they do not report. Must be cited in the abstract's positioning. |
| **GMMAS** (Liu et al. 2026) | Verified from full text: its uncertainty gates *training-time pseudo-label filtering only* and never an inference-time decision. No abstention, no risk–coverage, no coverage test. |
| **Yogananda et al. 2025** | Same dataset family (UTSW, UCSF, EGD). Differentiation must be argued on **mechanism** — abstention plus risk–coverage — not on data novelty. Their paper lists missing-modality as its own unaddressed limitation. |
| **RISEN** (Liang et al. 2026) | Imputation-based, always predicts. Our contrast: zero-and-possibly-abstain vs. impute-and-always-answer. |
| **FoundBioNet** (MICCAI 2025) | Cite as the discrimination ceiling we approach but do not attempt to beat; we trade raw AUC for a trust mechanism. |

**The pattern worth naming** (SPEC §6): the field has separately solved discrimination, missing-modality robustness, and calibration reporting — but no paper closes the loop into an inference-time decision that uses uncertainty to *withhold* a prediction and tests whether that remains trustworthy under the two conditions the field's own evidence shows break both discrimination and calibration.

---

## 4. Reporting checklists

| Checklist | Status | Owner |
|---|---|---|
| **TRIPOD+AI** (BMJ 2024;385:e078378) | Primary structure for the whole prediction-model report. **Supersedes TRIPOD 2015, which must not be used.** | C |
| **CLAIM 2024** (Radiology:AI 2024;6(4):e240300) | Imaging-specific items: acquisition protocol, reference-standard definition, model/code/data availability | C |
| **PROBAST+AI** (BMJ 2025;388:e082505) | Risk-of-bias companion, methods appendix. Marked *"not verified"* in the SPEC — verify before citing (**D-010**) | C |
| CONSORT-AI / SPIRIT-AI | **NOT APPLICABLE.** Prospective trials only. Must not be cited as if they applied. | — |

Both TRIPOD+AI and CLAIM 2024 were current as of the SPEC's preparation and are actively maintained: **re-check for updates immediately before submission** (SI-15). Completed checklists ship as `paper/checklists/`.

---

## 5. Continuously maintained artifacts

Started at Phase 00, updated as each phase completes. **Not reconstructed from memory in the final month.**

| Artifact | Location | Updated |
|---|---|---|
| Bibliography (BibTeX) | `paper/bibliography/` | on every literature touch |
| Dataset table | `paper/tables/table1_cohorts.md` | Phase 03 |
| Cohort-flow diagram | `paper/figures/fig1_flow.*` | Phases 03, 05 |
| Method description | `paper/methods/` | **as each phase completes** |
| Experiment registry | `experiments/REGISTRY.md` | every run |
| Limitation log | `paper/LIMITATIONS.md` | continuously |
| **Negative-results log** | `paper/NEGATIVE_RESULTS.md` | **the moment a claim is refuted** |
| Exclusion log | `manifests/exclusions_*.json` | Phases 03, 04 |
| Figure / table registry | `paper/REGISTRY.md` | Phase 13 |
| Decision log | `docs/research/DECISION_LOG.md` | continuously |

**`NEGATIVE_RESULTS.md` is written when the result appears, not at write-up time.** This is the practical defence against retroactively softening a refuted claim.

---

## 6. Phase 14–15 sequence

**Phase 14 — manuscript + reproducibility package**
1. Results freeze verified (Gate F): all figures/tables regenerate by one command.
2. Draft Methods from the per-phase method notes; Results from frozen result files only — **no number transcribed by hand**.
3. Draft Discussion including every refuted claim, stated plainly.
4. Limitations: simulated missingness (**D-008**), 1p/19q underpowering, internal test size, single-institution training, any solo-degraded QC (**D-001**), any disclosed protocol deviation.
5. Complete TRIPOD+AI and CLAIM 2024 checklists.
6. Verify-before-cite pass over the whole bibliography (**D-010**).
7. Fresh novelty/literature check; adjust the "first" claim or drop it.
8. Internal technical review (A + C); independent recomputation of headline numbers from frozen artifacts.
9. Build the reproducibility package; **acceptance test — someone not on the project regenerates every figure and table from the README.**

**Phase 15 — submission through publication**
1. Venue selection finalized; format the submission package.
2. Submit. Record the submission SHA and tag the repository.
3. Reviewer-response cycle. Additional experiments only if legitimately requested — run under the REVIEWER class, **labelled post-hoc, never replacing the pre-registered primary result.**
4. Revision; camera-ready.
5. Code release at the publication tag; archival DOI (Zenodo or equivalent) if the venue or dataset terms permit.
6. Final check: every claim in the published paper traces through the provenance chain to a raw patient ID.

---

## 7. Authorship and contribution

Recorded as work happens, not negotiated at the end. CRediT taxonomy: conceptualization, data curation, formal analysis, investigation, methodology, software, validation, visualization, writing. Person A's use of Claude and Codex is disclosed per the venue's AI-tool policy — checked at Phase 14, since these policies change.
