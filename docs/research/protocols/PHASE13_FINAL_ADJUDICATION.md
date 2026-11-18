# Phase 13 final adjudication and RQ answers (T13.2, T13.3, T13.6)

Written 2026-11-18. Claude-owned. Every number is read from a frozen aggregate file; nothing is recomputed here.

**Status: provisional.** Single-agent. T13.9 (independent recomputation by Codex, degraded under D-001) is running; nothing here is final until every discrepancy it finds is resolved and the Research Lead signs Gate F.

**Sources.** Internal: `01M46999FB083AX4WW0067YM13/phase09_analysis.json`, `phase10_analysis.json` (UTSW test, 124 patients, 35 mutant). External: `external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_20261118/phase09_external_analysis.json`, `phase10_external_analysis.json` (UCSF-PDGM, 202 patients, 80 mutant; manifests `2af464b0…` and `e28757de…`). Combined: `phase13/phase13_final_analysis.json` (written by `scripts/finalize_results.py`, SHA-256 in its sidecar). EGD was not evaluated (D-057): the family is 29 tests, not 44.

## Claim adjudication (verbatim criteria: SPEC section 1.4; frozen rules: SAP and `PHASE09_INTERNAL_RESULTS.md`)

| Claim | Internal (UTSW) | External (UCSF-PDGM) |
|---|---|---|
| C1 selective prediction beats always-predict, internal | **supported** | not applicable |
| C2 advantage survives missing modalities | **refuted** (`drop_t1ce`) | not re-tested (internal claim) |
| C3 advantage survives external shift | not applicable | **supported** on `full`; worst over the five missing-modality conditions is inconclusive (`drop_t1`, `drop_t1ce`, `drop_t2`) |
| C4 coverage deviation can be characterised within the 0.07 band | **refuted** | **refuted** |
| C5 risk-coverage curves are monotonic | inconclusive | **supported** in all six conditions |
| C6 abstention is enriched for errors | **refuted** (`drop_t1ce`) | inconclusive (`drop_t1`, `drop_t1ce`); not refuted |

Refuted claims are stated as refuted: C2, C4 (both cohorts), C6 (internal). Each needs a same-day `paper/NEGATIVE_RESULTS.md` entry (acceptance criterion 9). Internal C2, C4, C6 drafts are in `PHASE09_INTERNAL_RESULTS.md`; the external C4 text is in `PHASE12_EXTERNAL_RESULTS.md`. The Research Lead places them (`paper/` is human-owned).

## One Benjamini-Hochberg pass, 29 tests, q = 0.05 (D-052)

7 of 29 rejected. Adjusted p in brackets.

- UTSW: B2, AURC(M5, `drop_t1ce`) minus AURC(M5, `full`) (0.005).
- UCSF-PDGM: A2 (AURC M5 minus M4, 0.005), A3 (M3 minus M4, 0.005), B2 (`drop_t1ce`, 0.005), B4 (`drop_flair`, 0.012), D2 (Brier M1 minus M2, point -0.0034, 0.005), E2 (AURC R7 minus R2, 0.005).

Not rejected: every UTSW block A, D and E member; all UCSF A1, B1, B3, B5, C1, D1, E1 (adjusted 0.156), E3, E4 (0.152). The permutation floor is p = 2/2001; several rejected members sit on it, so their adjusted p is the floor times 29 over rank, not a measured small value.

## RQ answers

**RQ1 (risk-coverage under missingness and shift).** On complete input, rejecting low-confidence cases lowers selective risk below always-predict at every coverage level 0.5 to 0.9, in both cohorts (C1 supported; C3 supported on `full`). UCSF `full`: always-predict risk 0.153, selective risk 0.030 at coverage 0.5, AURC 0.0505 (bootstrap 0.029 to 0.081). The curves are monotone in every external condition (C5 supported) but only inconclusive internally. The advantage does not hold under every missing sequence: dropping T1ce removes it internally (C2 refuted) and the external AURC with T1ce missing is 0.310 against always-predict risk 0.451. Mechanism comparison: M5 (conformal ranking), M1, M2 share a ranking and are indistinguishable from M3 (UCSF A1 point -0.0002, adjusted p 0.96); the ensemble-variance ranking M4 is worse than M5 on UCSF (A2, A3 rejected). Answer: yes on full input, with a T1ce exception; conformal risk control adds nothing over temperature-scaled confidence in ranking.

**RQ2 (coverage close to nominal; effect of broken exchangeability).** Measured, not assumed. UCSF `full`, carried-over UTSW quantiles: alpha 0.05 gives coverage 0.985 (nominal 0.95; deviation interval -0.034 to +0.050, preserved under the 0.07 band); alpha 0.1 gives 0.931 (interval -0.078 to +0.080, indeterminate); alpha 0.2 gives 0.738 (nominal 0.80, deviation -0.069, 33 of 202 prediction sets empty). The 0.07 band cannot be met at alpha 0.1 or 0.2 in any condition at n = 202, so C4 is refuted: the sample is too small to tell preserved from degraded. Missing modalities widen this (alpha 0.05, `drop_t1ce`: half-width 0.136). Direction: coverage is above nominal at alpha 0.05 and 0.1 and below at 0.2 on `full`; no consistent degrade-only pattern.

**RQ3 (calibration internal to external).** No degradation observed. ECE (M2) 0.122 (bootstrap 0.090 to 0.194) internal, 0.106 (0.091 to 0.160) external; Brier (M2) 0.139 (0.104 to 0.177) internal, 0.121 (0.101 to 0.145) external. Intervals overlap; there is no family test for this contrast, so this is descriptive. Temperature scaling does not lower ECE on either cohort (D-058), and the Brier gain of raw over scaled on UCSF is 0.0034 (D2). The external AUROC is higher than internal (0.929 against 0.878); label prevalence differs (0.396 against 0.282), so it is not evidence of better generalisation. This contradicts the degradation reported elsewhere (for example GliomaVista-IDH) rather than replicating it, for this cohort pair. EGD was not evaluated.

**RQ4 (1p/19q, exploratory).** Internal only, D-007, no inferential claim: frozen-R2-encoder probe AUROC 0.787 on 66 labelled UTSW test patients (14 co-deleted); inside IDH-mutant patients 0.673 with interval (0.441, 0.870) that includes 0.5 (`PHASE10_INTERNAL_RESULTS.md`). No external 1p/19q evaluation was run. Conclusions on 1p/19q stay exploratory with wide intervals.

## Ablations (H1 to H3, family block E)

R7 (whole-brain pooling) and R8 (two-stage) are not distinguishable from R2 on UTSW (E1 to E4 adjusted p between 0.26 and 0.81). On UCSF R7 is worse on AURC (0.090 against 0.051, E2 adjusted 0.005) and its AUROC difference is not significant after adjustment (E1 0.904 against 0.929, adjusted 0.156); R8 is not distinguishable (AUROC 0.927, AURC 0.076, E4 adjusted 0.152). The tumour-aware pooling choice is supported only by the R7 AURC contrast on one cohort.

## Not yet done

- Independent verification (T13.9) and resolution of every discrepancy.
- Figures and tables with the external analysis, regeneration test, provenance spot-check of at least three numbers (acceptance criteria 5, 6, 8).
- Same-day `NEGATIVE_RESULTS.md` entries for C2, C4, C6 (Research Lead places them).
- Wide intervals at the coverage extremes are shown in the figures as computed; none were hidden by grid coarsening (to be checked on the rebuilt figures).
- Gate F signature and the `results-freeze` tag (Research Lead).
