# Benjamini-Hochberg family: the table to confirm (Gate E criterion 7)

Written 2026-11-17. `STATISTICAL_ANALYSIS_PLAN.md` section 6 says the family composition is "proposed, to confirm at the
freeze". This file lists every member so the confirmation is one read-through. It changes no choice; the composition is
the SAP's. Raw p-values for the UTSW members are in `PHASE10_INTERNAL_RESULTS.md`; no adjusted p-value is written for the
pre-registered family before Phase 13 (D-052).

One family, q = 0.05, paired bootstrap p (two-sided, D-052) unless noted. Block, comparison, and what exists today:

| Block | Comparison (all `full` input unless stated) | UTSW | UCSF-PDGM | EGD |
|---|---|---|---|---|
| A (3 per cohort) | AURC(M5) vs AURC(M3); M5 vs M4; M3 vs M4 | computed (A1 to A3) | pending | pending |
| B (5 per cohort) | AURC(M5, c) minus AURC(M5, full) for c in drop_t1, drop_t1ce, drop_t2, drop_flair, t1ce_flair_only | computed (B1 to B5) | pending | pending |
| C (1 per external cohort) | AURC(M5, external) minus AURC(M5, UTSW), unpaired | not applicable | pending | pending |
| D (2 per cohort) | ECE(M1) minus ECE(M2); Brier(M1) minus Brier(M2) | computed (D1, D2) | pending | pending |
| E (4 per cohort) | AUROC(R7) minus AUROC(R2) and AURC(R7) minus AURC(R2); the same for R8 (AUROC by DeLong) | computed (E1 to E4) | pending | pending |

Counts: UTSW 14, UCSF-PDGM 15, EGD 15 (14 plus block C). **Without EGD: 14 + 15 = 29. With EGD: 44.** This matches the
SAP table ("Tests with EGD 44", "without 29"). Today 14 are computed and 15 are `pending_external` in `bh_family` of
`phase10_analysis.json`; the EGD rows are not listed there yet.

Outside the family (SAP section 6): C1 to C6 decision rules, the 1p/19q probe (exploratory), reliability diagrams,
descriptive tables, and the M6 comparison (added 2026-11-17, descriptive, not a pre-registered claim).

## What you confirm

1. The blocks and counts above are the family (A to E, per cohort).
2. M6 stays outside the family.
3. Whether the family is 29 or 44 at the first external evaluation. That depends on EGD timing and is decision D-057
   (open): if EGD is in the first external run the family is 44; if it is run later as a separate frozen evaluation
   (`EXTERNAL_VALIDATION_PROTOCOL.md` section 5) the first family is 29 and the EGD tests belong to the addendum.

The BH pass itself runs once, at Phase 13, over the family you confirm (D-052).
