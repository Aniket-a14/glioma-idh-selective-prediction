# Phase 12 external results: UCSF-PDGM (adjudication, T12.9)

Written 2026-11-18, after both frozen runs and `scripts/analyze_external.py` (flag set by the Research Lead). Claude-owned adjudication. Aggregate numbers only; no per-patient data.

**Inputs.** Run 1 `ucsf_pdgm_gate_e_20261118` (R1 to R6, manifest `2af464b0…`, pinned `2fd9513`). Run 2 `ucsf_pdgm_gate_e_r7r8_20261118` (R7, R8 stage 2, manifest `e28757de…`, pinned `b3aa794`, D-060). Primary run R2 `01M46999FB083AX4WW0067YM13`, checkpoint hash `1d0c5302…`, T = 1.1247554245437905 fitted on the UTSW calibration split only. 202 patients, 6 modality conditions, 2000 bootstrap draws, 10000 permutations, seed 0. Analysis written to `external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_20261118/phase09_external_analysis.json` and `phase10_external_analysis.json` (write-once, sidecars verified at write).

**Status.** Single-agent adjudication. Second-agent recomputation of these numbers (T13.9, degraded under D-001) is not done yet; nothing below is final until it is.

## Claim verdicts (frozen rules, PHASE09_INTERNAL_RESULTS.md wording)

| Claim | External verdict | Basis |
|---|---|---|
| C3 | **supported** on `full` (headline) | `full`: D(phi) at the five coverage levels 0.9 to 0.5 is -0.027, -0.042, -0.069, -0.088, -0.124; every upper 95% limit below 0 (largest -0.006). Secondary per condition: supported for `drop_flair` and `t1ce_flair_only`; inconclusive for `drop_t1`, `drop_t1ce`, `drop_t2` (upper limit above 0 at coverage 0.9 or 0.8). Worst over conditions is inconclusive. |
| C4 | **refuted** | Frozen rule: refuted if any condition has a coverage-deviation interval with half-width above 0.07. All six conditions are refuted at alpha 0.1 and 0.2 (half-widths 0.079 to 0.16). At alpha 0.05, five conditions pass and `drop_t1ce` is refuted (half-width 0.136). The 0.05-band secondary reading also refutes. `full`, alpha 0.05: empirical coverage 0.985, deviation interval [-0.034, +0.050], label "preserved" under the 0.07 band. |
| C5 | **supported** | All six conditions: every adjacent-pair point estimate at or below 0 and no lower 95% limit above 0. |
| C6 | **inconclusive** (worst over conditions) | `full`, `drop_flair`, `drop_t2`, `t1ce_flair_only` supported (BH-adjusted enrichment p < 0.05 at all coverage levels). `drop_t1` and `drop_t1ce` inconclusive (some adjusted p above 0.05, no observed enrichment at or below 0). Not refuted: no observed enrichment is at or below 0 in any condition. |

Internal verdicts for comparison (UTSW, 124 patients): C1 supported, C2 refuted, C4 refuted, C5 inconclusive, C6 refuted. External C4 agrees with internal; C5 and C6 are better outside than inside; C2 (modality-drop) was an internal-only claim and is not re-tested.

## Headline numbers, `full` condition, R2 (M2, temperature-scaled)

- AUROC 0.929 (Hanley-McNeil 95% [0.888, 0.970]; bootstrap [0.892, 0.960]). Internal was 0.878. External is higher than internal; the cohorts differ in label prevalence (UCSF 0.396 mutant vs 0.282 UTSW test) and acquisition, so do not read this as better generalisation.
- ECE 0.106 temperature-scaled, 0.097 raw. Brier 0.121 (raw 0.118). Temperature scaling again does not lower ECE (D-058).
- AURC 0.0505 (bootstrap [0.029, 0.081]); always-predict risk 0.153; oracle AURC 0.0128. Selective risk at coverage 0.5 is 0.030.
- Split conformal (M5, quantiles carried over from UTSW), `full`: alpha 0.05 empirical coverage 0.985 (singleton fraction correct 0.969, abstention 0.52); alpha 0.1 coverage 0.931 (abstention 0.24); alpha 0.2 coverage 0.738 with 33 empty sets (nominal 0.80, deviation -0.069).
- M4 (variance ranking) has a higher AURC than M2 in every condition (0.119 vs 0.050 on `full`). That is the D-059 definition (rank by -Var, error of the ensemble-mean classifier), and an independent recomputation from the member probabilities in the parquet files confirmed the alignment: patient order is identical across the five members and an ensemble-mean confidence gives AURC 0.052. Not a bug.
- M6 comparator (R1) is worse than M2 in every condition (AURC 0.092 vs 0.050 on `full`; always-predict risk 0.233).

## Ablations (second run, D-060; R2 vs R7 vs R8 on `full`)

| Run | AUROC | AURC | ECE (M2) | Brier |
|---|---|---|---|---|
| R2 | 0.929 | 0.051 | 0.106 | 0.121 |
| R7 (whole-brain) | 0.904 | 0.090 | 0.117 | 0.137 |
| R8 (two-stage) | 0.927 | 0.076 | 0.135 | 0.135 |

Block E: E1 (R7 vs R2 AUROC, DeLong) point -0.024, p = 0.048; E3 (R8 vs R2 AUROC) point -0.002, p = 0.894; E2 and E4 (AURC comparisons) favour R2 with permutation p = 2/2001 and 28/667. These are unadjusted; the single BH pass over all 29 tests (D-052) runs in Phase 13 and E1 at p = 0.048 will not survive it.

## Family blocks A to D (unadjusted, point estimates)

A1 -0.0002 (p 594/667), A2 -0.069 (p 2/2001), A3 -0.069 (p 2/2001); B1 +0.007, B2 +0.260 (p 2/2001), B3 -0.011, B4 +0.051 (p 2/667), B5 +0.013; C1 -0.025, interval [-0.078, +0.021] (unpaired, p 554/2001); D1 -0.009, D2 -0.0034 (p 2/2001). Block definitions are in `freeze_spec.json`; they are not interpreted here. Interpretation waits for the single BH pass in Phase 13.

## Required actions

1. C4 is refuted again on a new cohort: same-day entry in `paper/NEGATIVE_RESULTS.md` (project rule, negative results are recorded the day they are found). Proposed text is below; the file is human-owned, so it waits for the Research Lead.
2. Second-agent recomputation (T13.9), then Phase 13 combine, single BH over 29, final adjudication, figures.

**Proposed `NEGATIVE_RESULTS.md` entry (2026-11-18).** C4 (coverage deviation characterisable within the pre-registered tolerance) is refuted on UCSF-PDGM under the frozen 0.07 half-width rule. At alpha 0.1 and 0.2 every condition's deviation interval is wider than the band (half-widths 0.079 to 0.16 with n = 202), so the sample is too small to say whether coverage is preserved or degraded; at alpha 0.05 five of six conditions pass. Not re-run, not re-scoped.
