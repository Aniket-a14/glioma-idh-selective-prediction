# Phase 10 scientific validation 3: R7 and R8 against the literature

Written 2026-11-18. Phase 10 asks that the confirmatory ablations be compared with the literature they are meant to reproduce, as a check on our implementation, not as a contribution (`PHASE_10_ABLATIONS_INTERNAL_STATS.md`, validation 3). R7 is whole-brain pooling (H1, tumour-aware pooling ablation). R8 is two-stage independent segmentation and classification (H2, joint versus independent).

**Status of the sources: search snippets only.** Two web searches on 2026-11-18 returned abstracts and summaries. Nobody has opened the full texts, so every number below is unverified under D-010 and must not be cited in the manuscript until Person C (or the Research Lead) checks it against the paper. This file records what to check, not what is established.

## What the literature is expected to show, and what we see

| Hypothesis | Literature direction (from snippets) | Our internal result (UTSW test, n = 124, 35 mutant) | Consistent? |
|---|---|---|---|
| H1: tumour-aware pooling beats whole-brain pooling | No direct head-to-head found in the search. Segmentation-based tumour input is common in IDH pipelines (for example Yogananda et al., T2-only and multi-contrast 3D nnU-Net classifiers, AUC 0.86 to 0.96 across training sets, per the Bioengineering 2023 snippet). | E1: AUROC(R7) - AUROC(R2) = +0.010 (-0.026, 0.047); E2: AURC(R7) - AURC(R2) = +0.017 (-0.024, 0.070), the worse direction for R7 | AURC direction matches the expectation (tumour-aware better), AUROC direction does not; both intervals include 0, so the data neither confirm nor contradict it |
| H2: joint training matches or beats two-stage | GMMAS ablation (Liu et al., arXiv:2501.17758, per snippet): multi-task variants above single-task baselines (AUC about 0.97 against 0.93). A fully automatic two-stage pipeline (arXiv:2005.11965, per snippet) reports IDH AUC 0.94 on TCIA and 0.86 on its own institutional data. The snippets state no controlled head-to-head. | E3: AUROC(R8) - AUROC(R2) = +0.010 (-0.029, 0.051); E4: AURC(R8) - AURC(R2) = +0.022 (-0.004, 0.052), the worse direction for R8 | AURC direction matches the expectation (joint better); AUROC does not; all intervals include 0 |

## Reading

Our AUROC values (R2 0.878, R7 0.888, R8 0.889) sit inside the 0.86 to 0.96 range the snippets report for segmentation-based IDH classifiers, so nothing here suggests the pipeline is broken. At n = 124 with 35 mutant, the AUROC intervals are about +/-0.04, so a difference of the size the literature suggests (a few points) is not detectable; the check can find a gross implementation error (it did not), not confirm the effect. The literature comparisons are across datasets and architectures, not controlled, so the match is by order of magnitude only.

## To close this item

1. Someone opens the full text of each source named above, confirms the numbers and the cohort and metric definitions, and replaces the snippet-level wording; unverifiable sources are dropped (D-010).
2. Check whether any paper reports a controlled whole-brain versus tumour-region comparison for IDH (the searches did not find one); if none exists, say so in the manuscript's limitations for H1.
3. Record the result in `PHASE10_INTERNAL_RESULTS.md` ("Open for Phase 10"). The R7 and R8 values are not a contribution of this study and are reported briefly.

Sources opened as search results only: Yogananda et al. (Bioengineering 2023, PMC10525372), Liu et al. GMMAS (arXiv:2501.17758), the two-stage pipeline of arXiv:2005.11965, the multi-task whole-volume model (PMC9925710, arXiv:2010.04425).
