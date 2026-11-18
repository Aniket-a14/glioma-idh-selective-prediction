# Phase 13 final adjudication and RQ answers (T13.2, T13.3, T13.6)

Written 2026-11-18. Claude-owned. Every number is read from a frozen aggregate file; nothing is recomputed here.

**Status: provisional until Gate F.** T13.9 (independent recomputation by Codex, degraded under D-001) is complete and every discrepancy is resolved (see below); the Research Lead signs Gate F.

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

## Regeneration test and provenance spot-check (acceptance criteria 6 and 8)

Regeneration: `build_paper_artifacts` was run twice by the Research Lead (flag set for the command) into `build/paper_artifacts_ext_a` and `..._b` with the external analysis; 38 files each (Figures 1 to 5 with UCSF-PDGM variants, Tables 1 to 6, `CLAIMS.json`, registry rows). Every file is byte-identical except `REGISTRY_ROWS.md`, which embeds the output directory name; after normalising that name it is identical too. The test ran into `build/`, not `paper/` (parked, human-owned).

Provenance, three numbers traced table to analysis JSON to raw frozen parquet (UCSF `full`, R2, T = 1.1247554, conformal quantile 0.77727 from UTSW calibration): (1) Table 4 carried-over coverage at alpha 0.05, 0.98515 (200 of 202 sets cover): recomputed from `primary_seed0/full.parquet` as 0.9851485, equal. (2) Table 3 AURC (mean over cutoffs) 0.0505275: recomputed 0.0505275, equal to 1e-16. (3) Table 3 selective risk at coverage 0.5, 0.0297 (3 errors in the 101 most confident): recomputed 3 of 101 = 0.0297. These are my own checks, not the independent verification.

## Independent verification, T13.9 (degraded: second agent, D-001)

Codex recomputed the UCSF-PDGM numbers blind: its compute step could not read the author's code or results, and wrote `T139_EXTERNAL_RESULTS_CODEX.json` (SHA-256 `6f5afd01…`) before comparison. Report: `T139_EXTERNAL_REPORT_CODEX.md`. Of 2060 numbers compared, 1985 agree; 75 disagree; 159 further numbers have no reference in the author's files (per-condition AUROC, ECE, Brier, trapezoid intervals, C5 p-values: never reported, so nothing in a table depends on them). All 24 per-condition C3 to C6 status categories match.

Every disagreement is explained; none moves a reported value, a status or a rejection:

- **Oracle AURC, 6 numbers (D-061).** A contract ambiguity about ties. The reported values stay.
- **C6 permutation p-values, 60.** 48 are float-versus-exact encoding of the same p (difference near 1e-20); the rest are permutation Monte Carlo (for example 16 against 23 exceedances out of 10001 at coverage 0.8). Seeds are not fixed by the contracts, so the schedule differs; every adjusted p stays below 0.05 in both implementations, so every C6 status is unchanged.
- **C4 interval endpoints, 4, and block C1 raw p, 1 (8/29 against 554/2001).** Seed and stream layout. Codex, told the author's schedule after the comparison, reproduced the C4 endpoints (-0.1960396, 0.0861386) and the C1 interval and p (554/2001) exactly.
- **Pooled BH, 3.** Follow from the C1 raw p and DeLong floating-point differences; BH itself is exact on both sides.
- **Temperature, 1.** Independent bisection 1.1247554289 against the frozen fit 1.1247554245 (4.4e-9), inside the contract's 1e-6.
- **Overall C3, 1.** A labelling bug in Codex's own summary (worst over conditions instead of the primary `full`); per-condition statuses agree.

Reading: no real disagreement in any reported number. The seed schedule is a documentation gap, not a numerical one: the contracts should state the external seed schedule (the author's is in `results_summary.seed_schedule`). The paper should disclose that verification was by a second agent.

## Not yet done

- Same-day `NEGATIVE_RESULTS.md` entries for C2, C4, C6 (Research Lead places them).
- Wide intervals at the coverage extremes are shown in the figures as computed; none were hidden by grid coarsening (to be checked on the rebuilt figures).
- Gate F signature and the `results-freeze` tag (Research Lead).
