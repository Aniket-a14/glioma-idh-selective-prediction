# Phase 10 scientific validation 3: R7 and R8 against the literature

Written 2026-11-18. Phase 10 asks that the confirmatory ablations be compared with the literature they are meant to reproduce, as a check on our implementation, not as a contribution (`PHASE_10_ABLATIONS_INTERNAL_STATS.md`, validation 3). R7 is whole-brain pooling (H1, tumour-aware pooling ablation). R8 is two-stage independent segmentation and classification (H2, joint versus independent).

**Status of the sources (updated 2026-11-18, later the same day).** Three sources were checked against primary text: arXiv:2005.11965 (abstract page), arXiv:2501.17758 (abstract and HTML text; two appendix tables only through a model summary of the page, marked below) and the Yogananda et al. 2023 abstract (via Europe PMC; the PMC page itself was blocked by a bot check). Full-paper tables and methods of the first and third were not read. Anything not marked verified stays unverified under D-010 and must not be cited in the manuscript.

## What the sources say, and what we see

| Source | What was verified | Bearing on H1 / H2 |
|---|---|---|
| Decuyper et al., MIDL 2020, arXiv:2005.11965 (verified, abstract) | A fully automatic 3D pipeline: a 3D U-Net segments the tumour, the tumour ROI is extracted and fed to a multi-task classifier (grade, IDH, 1p/19q). Whole-tumour Dice 90%. IDH AUC 0.94 on TCIA/BraTS 2019 test data (628 patients in the dataset), 0.86 on an independent 110-patient Ghent set. | A segment-then-classify design with a tumour ROI; no whole-brain or joint comparison. Gives the AUC range for design H2 (R8) |
| Yogananda et al., Bioengineering 2023, DOI 10.3390/bioengineering10091045 (verified, abstract via Europe PMC) | nnU-Net 2D networks that classify IDH and segment the tumour at the same time; T2-only AUC 0.86 (TCIA) and 0.89 (TCIA+EGD), multi-contrast AUC 0.94 and 0.96; tested on over 1100 held-out cases including 360 from UT Southwestern and 495 from UCSF. | Compares T2-only with multi-contrast input, not tumour-region with whole-brain input; no H1 or H2 comparison. Note it also reports on UTSW and UCSF, our two cohorts (differentiation work for the manuscript) |
| Liu et al., GMMAS, arXiv:2501.17758 (verified text, v2 of 25 May 2025; the plan says 2026, check the publication year) | Verbatim: the multi-task model with uncertainty weighting outperformed the single-task models in each task and a plain multi-task model. IDH AUC 0.969 in Table III after global feature fusion, 0.982 with semi-supervised learning. Appendix Table A6 values (single segmentation Dice 0.913, single classification AUC 0.928, multi-task 0.940 and 0.969) come from a model summary, not from text I read verbatim. **Its "two-stage" means two semi-supervised training stages (pseudo-labelling, then consistency regularisation), not segment-then-classify.** | A joint multi-task versus single-task ablation; **not** a comparison with a two-stage segment-then-classify pipeline, so it does not speak to H2 as R8 defines it |

Our results, for the record: E1 AUROC(R7) - AUROC(R2) = +0.010 (-0.026, 0.047); E2 AURC(R7) - AURC(R2) = +0.017 (-0.024, 0.070); E3 AUROC(R8) - AUROC(R2) = +0.010 (-0.029, 0.051); E4 AURC(R8) - AURC(R2) = +0.022 (-0.004, 0.052). All four intervals include 0.

## Reading

Our AUROC values (R2 0.878, R7 0.888, R8 0.889) sit inside the 0.86 to 0.96 range the verified abstracts report for segmentation-based IDH classifiers on mixed cohorts, so nothing here suggests the pipeline is broken. That is the check Phase 10 asked for (an implementation sanity check, not a contribution). **None of the verified sources is a controlled comparison of whole-brain with tumour-aware pooling (H1) or of joint with independent segmentation and classification (H2)**, so the literature gives no direction for E1 to E4 to be consistent or inconsistent with; the datasets and architectures differ. At n = 124 with 35 mutant the AUROC intervals are about +/-0.04, so a difference of a few points is not detectable. Report R7 and R8 briefly as confirmatory ablations whose intervals include 0.

## To close

1. Done 2026-11-18: abstract-level check of the three sources above. Still open and not needed for Gate D: read the full methods and tables of arXiv:2005.11965 and the 2023 paper, and the exact Table A6 of arXiv:2501.17758, before any number is quoted in the manuscript.
2. No source found with a controlled whole-brain versus tumour-region IDH comparison; say so in the manuscript's limitations for H1 (and for H2 that no controlled joint versus two-stage comparison was found).
3. Record the result in `PHASE10_INTERNAL_RESULTS.md` ("Open for Phase 10").
