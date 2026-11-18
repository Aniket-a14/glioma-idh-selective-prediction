# T13.9 independent external recomputation

**BLOCKED — real disagreements found; scientific changes stopped.**
D-001 degraded solo fallback: a second agent, not a second human.

Numbers compared: **2060**; ok: **1985**; discrepancies: **75**. Additional saved numeric outputs without an allowed reference: **159**, listed separately and excluded from the comparison denominator. They are not counted as agreement.
Status/coverage-label comparisons: 64/65 category matches. All 24 per-condition C3–C6 categories agree; overall primary C3 does not, due to OWN_C3_AGGREGATION. Raw inconclusive strings differ ('inconclusive at this n' versus 'inconclusive'); table retains both.

## Independence and scope

Compute finished and exclusively created the results JSON before any author result was opened. Only permitted contracts, decision entries, freeze_spec and the earlier independent script were read; no prohibited analysis source, analyze script, person_c_recompute.py or phase13 result was opened. The allowed result files were first opened in the later comparison step. Compare adds mappings and a report only; it never alters the blinded JSON or scientific compute functions. Separate post-unblinding diagnostics above explain index schedules, not replace the blinded numbers. No patient IDs or patient rows are output.

Blinded results SHA-256: `6f5afd01c65a1cb7ab5641d23719a65c9ad7629e06a19d3e3d29745c50f3a167`.
Pre-comparison script SHA-256: `cd22dfe61ccf4a72ed89272f06388b0615c523878c472c127666471b759eb6c4` (comparison function was still a stub; final script adds compare only).
Parquet inputs: 40; all present sidecars verified; absent sidecars: 0.
No environment authorization flag was set; no /Volumes write, source, test, config, other document change, commit or merge was performed.

## Discrepancy causes

**C4_MC** (4 numeric discrepancies). Four lower interval endpoints exceed .01. Mine uses seed 0 and successive complete calibration/test matrices, shared across cells. Reference declares seed=10000+100*condition_index+alpha_index. Diagnostic on full/alpha=.2 using seed 10002 and interleaving calibration and test draws reproduces reference endpoints exactly (-0.1960396039603961, 0.0861386138613861); sequential matrices give a different endpoint. Cause: Monte Carlo/index-schedule difference, not a quantile/coverage formula disagreement. Results left unchanged.

**C6_MC_OR_ENCODING** (60 numeric discrepancies). Mine permutes the original patient-ordered loss vector at seed 0 once per condition and shares permutations across the grid. Author declares seed+coverage_index on its descending grid. Counts vary with seed and equivalent permutation layouts; matching seed alone did not reproduce the full permutation index scheme (12/30 counts matched in a diagnostic). Differences in integer exceedance counts are Monte Carlo noise; exact equality is still required and fails. Additionally author raw p is a rounded float, and its adjusted p is an exact fraction of that decimal rather than of the original integer-count rational. Even equal exceedance counts therefore fail exact-rational equality. Example full/0.5 BH: mine=5/30003, author=4999500049995001/30000000000000000000. This encoding difference has negligible numeric size but is retained as a strict discrepancy. No claim category changes. The author's full permutation index scheme remains unverified because its implementation was not read.

**OWN_C3_AGGREGATION** (0 numeric discrepancies). Own overall_claims.C3 incorrectly takes the worst over primary full and all secondary missing-modality conditions (inconclusive). Author keeps primary full C3=supported and secondary_worst_status=inconclusive. Per-condition categories and the separately mapped secondary worst agree. This is an own aggregation/labeling bug, not a risk-estimation disagreement. Stopped; not patched after unblinding. Claim statuses therefore do not all match overall.

**POOLED_PROPAGATION** (3 numeric discrepancies). Pooled BH differences propagate Block C1's raw-p difference or tiny DeLong floating-point differences. BH is exact Fraction arithmetic on the saved p-values; no p-value was replaced with the reference. The reference column is recalculated from author raw p-values, not a claim to have read phase13_final_analysis.json (never opened).

**TEMPERATURE_SOLVER** (1 numeric discrepancies). Independent inverse-temperature bisection gives 1.1247554289138795, frozen fit 1.1247554245437905 (difference 4.370089e-9). K5 allows 1e-6 on T, but this task asks 1e-9 on point estimates; strict failure is retained. Calibration metrics/quantiles are compared separately.

**UNPAIRED_STREAMS** (1 numeric discrepancies). Block C1 raw p is 8/29 versus 554/2001. Blinded code draws the UCSF matrix then UTSW matrix successively from default_rng(0). A separate diagnostic restarting default_rng(0) for each cohort reproduced the author lower=-0.07786734507784494, upper=0.02122924640373 and p=554/2001 exactly. Reusing the same seeded stream for both cohort matrices makes the matrices dependent, contrary to SAP section 4's independent-resamples instruction. This is an inferred author stream-construction bug, verified by aggregate reproduction, not source inspection. No compute change was made. Research Lead review is required; practical differences are small but exact p fails.

**UNRESOLVED_STOP** (6 numeric discrepancies). Unexpected disagreement: stop for Research Lead review.

## Frozen rules applied

- **C3**: D-035: refuted if any D(phi) >= 0; supported if all upper 95% limits < 0; otherwise inconclusive at this n. Full primary; missing conditions secondary; worst across conditions also reported.
- **C4**: D-004, D-045, D-050, D-058: supported iff every two-stage coverage-deviation interval half-width <= .07; otherwise refuted. Preserved iff interval inside +/- band; degraded iff wholly below -band or above +band; otherwise indeterminate. Also report .05 band. D-058 permits negative calibration findings, no refit.
- **C5**: D-035, D-050: adjacent difference = risk at lower coverage minus risk at higher coverage. Refuted if any lower 95% limit > 0; supported if all point differences <= 0; otherwise inconclusive at this n. Bootstrap intervals, not permutation inference.
- **C6**: D-035, D-050: rejected error rate minus overall error rate. Refuted if any observed difference <= 0; supported if every one-sided permutation p, BH-adjusted across five coverages, < .05; otherwise inconclusive at this n. Permutation p=(1+count)/(10000+1).
- **loss**: D-059: M1/M2/M3/M5 use deterministic R2 errors; M4 uses ensemble-mean errors. Threshold >= .5 per updated metric contract. M6 uses its own classifier.
- **family**: D-052, D-060: 15 external members plus 14 UTSW members, one pooled BH pass at q=.05 in compare only. Block C independent cohorts; R7/R8 from supplementary frozen run.

## Resampling and calibration provenance

```json
{
  "bootstrap_iterations": 2000,
  "permutations": 10000,
  "seed": 0,
  "row_order": "patient_id ascending",
  "paired": "default_rng(0).integers(0,202,(2000,202)), reused everywhere",
  "C4": "default_rng(0), calibration matrix first then independent external matrix; fixed fitted temperature, refit quantiles only",
  "C6": "default_rng(0), 10000 permutation(loss) vectors per condition, shared over grid; reset per condition",
  "unpaired_C": "default_rng(0), external matrix first then independent UTSW matrix",
  "author_seed_index_match": "Unknown until compare; only S4 internal seed scheme explicitly fixed in permitted contracts",
  "draw_matrix_sha256": "2c3b6b00a187fdaa39c008ae45962130b19d8fa5706eb99a21e66674b67f6583"
}
```

Author seed schedule (read only after compute):

```json
{
  "conformal_carried_over_at_condition_alpha": "seed + 10000 + condition_index * 100 + alpha_index",
  "conformal_refit_at_condition_alpha": "seed + 20000 + condition_index * 100 + alpha_index",
  "monotonicity_at_condition_mechanism": "seed + condition_index * 6 + mechanism_index",
  "paired_bootstrap_indices": "seed",
  "permutation_at_coverage_index": "seed + coverage_index (0 through 4)",
  "random_confidence": "seed"
}
```

Paired seed-0 patient bootstrap matches the author empirically across paired family intervals and exact bootstrap p-values. C4, C6 and unpaired C index schemes did not match; intervals use the requested .01 absolute tolerance, point estimates 1e-9, rational p and BH strict equality. Finite DeLong p uses 1e-9. No tolerance is relaxed after seeing results.

Calibration uses conditions/full.parquet; predictions.parquet was also verified. Its logits differ by at most 4.38690185546875e-05; its fitted T=1.124756091252605. The condition-sweep calibration fit matches the written frozen specification within K5's 1e-6 solver tolerance. Neither uses external rows. Author R7/R8 M2 metrics require their own UTSW calibration files, which were not among the requested inputs; ablation ECE/Brier here are explicitly raw M1.

## Every compared number

| Number | Yours | Reference | Yours minus reference | Status | Tolerance / cause |
|---|---:|---:|---:|---|---|
| temperature | 1.1247554289138795 | 1.1247554245437905 | 4.370088957372786e-09 | DISCREPANCY | 1e-9 TEMPERATURE_SOLVER |
| quantiles.0.05 | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| quantiles.0.1 | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| quantiles.0.2 | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| calibration_coverage.0.05 | 0.9596774193548387 | 0.9596774193548387 | 0.0 | ok | 1e-9  |
| calibration_coverage.0.1 | 0.9112903225806451 | 0.9112903225806451 | 0.0 | ok | 1e-9  |
| calibration_coverage.0.2 | 0.8064516129032258 | 0.8064516129032258 | 0.0 | ok | 1e-9  |
| conditions.full.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.full.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.auroc | 0.9285860655737705 | 0.9285860655737705 | 0.0 | ok | 1e-9  |
| conditions.full.auprc | 0.897789537045756 | 0.8977895370457563 | -2.220446049250313e-16 | ok | 1e-9  |
| conditions.full.calibration.M1.ece | 0.09663086735740267 | 0.09663086735740269 | -1.3877787807814457e-17 | ok | 1e-9  |
| conditions.full.calibration.M1.brier | 0.11781259301521835 | 0.11781259301521835 | 0.0 | ok | 1e-9  |
| conditions.full.calibration.M2.ece | 0.1056412353146365 | 0.10564123474020824 | 5.744282549624558e-10 | ok | 1e-9  |
| conditions.full.calibration.M2.brier | 0.1211958169662402 | 0.12119581683994994 | 1.262902560306145e-10 | ok | 1e-9  |
| conditions.full.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.05052748456692471 | 0.050527484566924706 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.full.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.028780791496715117 | 0.028780791496715113 | 3.469446951953614e-18 | ok | .01  |
| conditions.full.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.0805371023026979 | 0.08053710230269788 | 1.3877787807814457e-17 | ok | .01  |
| conditions.full.mechanisms.M1.aurc_trapezoid.point | 0.050147619847779525 | 0.050147619847779525 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.risk_0.5.upper | 0.0892396786848489 | 0.0892396786848489 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.7.point | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.7.lower | 0.035211267605633804 | 0.035211267605633804 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.risk_0.8.upper | 0.1656441717791411 | 0.1656441717791411 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.9.point | 0.12637362637362637 | 0.12637362637362637 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.risk_0.9.lower | 0.07692307692307693 | 0.07692307692307693 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.risk_0.9.upper | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.5.point | -0.12376237623762376 | -0.12376237623762376 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.5.lower | -0.1634634051640458 | -0.1634634051640458 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.5.upper | -0.06626453907526683 | -0.06626453907526683 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.6.point | -0.08789157604285018 | -0.08789157604285018 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.6.lower | -0.13098530145697496 | -0.13098530145697496 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.6.upper | -0.043495374127576716 | -0.043495374127576716 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.7.point | -0.06895830428113234 | -0.06895830428113234 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.7.lower | -0.11468818756875689 | -0.11468818756875689 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.7.upper | -0.03649312334402464 | -0.03649312334402464 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.8.point | -0.04235423542354236 | -0.04235423542354236 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.8.lower | -0.07804839021734485 | -0.07804839021734485 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.8.upper | -0.015155543332111016 | -0.015155543332111016 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.9.point | -0.027091720161027094 | -0.027091720161027094 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M1.D_0.9.lower | -0.05066818157225557 | -0.05066818157225557 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M1.D_0.9.upper | -0.006146478230961268 | -0.006146478230961268 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.05052748456692471 | 0.050527484566924706 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.full.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.028780791496715117 | 0.028780791496715113 | 3.469446951953614e-18 | ok | .01  |
| conditions.full.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.0805371023026979 | 0.08053710230269788 | 1.3877787807814457e-17 | ok | .01  |
| conditions.full.mechanisms.M2.aurc_trapezoid.point | 0.050147619847779525 | 0.050147619847779525 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.risk_0.5.upper | 0.0892396786848489 | 0.0892396786848489 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.7.point | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.7.lower | 0.035211267605633804 | 0.035211267605633804 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.risk_0.8.upper | 0.1656441717791411 | 0.1656441717791411 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.9.point | 0.12637362637362637 | 0.12637362637362637 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.risk_0.9.lower | 0.07692307692307693 | 0.07692307692307693 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.risk_0.9.upper | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.5.point | -0.12376237623762376 | -0.12376237623762376 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.5.lower | -0.1634634051640458 | -0.1634634051640458 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.5.upper | -0.06626453907526683 | -0.06626453907526683 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.6.point | -0.08789157604285018 | -0.08789157604285018 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.6.lower | -0.13098530145697496 | -0.13098530145697496 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.6.upper | -0.043495374127576716 | -0.043495374127576716 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.7.point | -0.06895830428113234 | -0.06895830428113234 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.7.lower | -0.11468818756875689 | -0.11468818756875689 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.7.upper | -0.03649312334402464 | -0.03649312334402464 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.8.point | -0.04235423542354236 | -0.04235423542354236 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.8.lower | -0.07804839021734485 | -0.07804839021734485 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.8.upper | -0.015155543332111016 | -0.015155543332111016 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.9.point | -0.027091720161027094 | -0.027091720161027094 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M2.D_0.9.lower | -0.05066818157225557 | -0.05066818157225557 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M2.D_0.9.upper | -0.006146478230961268 | -0.006146478230961268 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.05075400219484429 | 0.05075400219484429 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.029326191693565998 | 0.029326191693565994 | 3.469446951953614e-18 | ok | .01  |
| conditions.full.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.08078713178335015 | 0.08078713178335015 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.aurc_trapezoid.point | 0.05037413747569911 | 0.05037413747569911 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.risk_0.5.upper | 0.07920792079207921 | 0.07920792079207921 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.6.point | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.6.lower | 0.024193548387096774 | 0.024193548387096774 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.7.point | 0.09154929577464789 | 0.09154929577464789 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.7.lower | 0.04225352112676056 | 0.04225352112676056 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.risk_0.7.upper | 0.14084507042253522 | 0.14084507042253522 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.risk_0.8.upper | 0.1656441717791411 | 0.1656441717791411 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.9.point | 0.12637362637362637 | 0.12637362637362637 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.risk_0.9.lower | 0.08140677257525085 | 0.08140677257525085 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.risk_0.9.upper | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.5.point | -0.12376237623762376 | -0.12376237623762376 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.5.lower | -0.16831683168316833 | -0.16831683168316833 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.5.upper | -0.07101136691339043 | -0.07101136691339043 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.6.point | -0.09608829735432559 | -0.09608829735432559 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.6.lower | -0.13382973543255966 | -0.13382973543255966 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.6.upper | -0.046745658172374624 | -0.046745658172374624 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.7.point | -0.06191605076000557 | -0.06191605076000557 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.7.lower | -0.10438819477830776 | -0.10438819477830776 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.7.upper | -0.028573420722354 | -0.028573420722354 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.8.point | -0.04235423542354236 | -0.04235423542354236 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.8.lower | -0.07572423909057574 | -0.07572423909057574 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.8.upper | -0.013995844028847348 | -0.013995844028847348 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.9.point | -0.027091720161027094 | -0.027091720161027094 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M3.D_0.9.lower | -0.04852573169404853 | -0.04852573169404853 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M3.D_0.9.upper | -0.0037086444300167987 | -0.0037086444300167987 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.1198174572895907 | 0.1198174572895907 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.07281638905739213 | 0.07281638905739213 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.1730346578294826 | 0.1730346578294826 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.aurc_trapezoid.point | 0.11943759257044552 | 0.11943759257044552 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.5.point | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.5.lower | 0.06861079383209595 | 0.06861079383209595 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.risk_0.5.upper | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.6.point | 0.1721311475409836 | 0.1721311475409836 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.6.lower | 0.10569105691056911 | 0.10569105691056911 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.risk_0.6.upper | 0.2459016393442623 | 0.2459016393442623 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.7.point | 0.15492957746478872 | 0.15492957746478872 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.7.lower | 0.09859154929577464 | 0.09859154929577464 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.risk_0.7.upper | 0.22610587899543336 | 0.22610587899543336 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.8.point | 0.17901234567901234 | 0.17901234567901234 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.8.lower | 0.11728395061728394 | 0.11728395061728394 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.risk_0.8.upper | 0.24074074074074073 | 0.24074074074074073 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.9.point | 0.17032967032967034 | 0.17032967032967034 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.risk_0.9.lower | 0.11538461538461539 | 0.11538461538461539 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.risk_0.9.upper | 0.22527472527472528 | 0.22527472527472528 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.5.point | -0.024752475247524747 | -0.024752475247524747 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.5.lower | -0.07426955930887208 | -0.07426955930887208 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.5.upper | 0.03960396039603961 | 0.03960396039603961 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.6.point | 0.01866580100633014 | 0.01866580100633014 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.6.lower | -0.028649167395747962 | -0.028649167395747962 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.6.upper | 0.05791747657372696 | 0.05791747657372696 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.7.point | 0.0014642309301352574 | 0.0014642309301352574 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.7.lower | -0.028768261441528775 | -0.028768261441528775 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.7.upper | 0.04239297169153533 | 0.04239297169153533 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.8.point | 0.025546999144358873 | 0.025546999144358873 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.8.lower | 0.0009167583425009063 | 0.0009167583425009063 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.8.upper | 0.041559711526708204 | 0.041559711526708204 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.9.point | 0.016864323795016872 | 0.016864323795016872 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M4.D_0.9.lower | 0.003699271026003703 | 0.003699271026003703 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M4.D_0.9.upper | 0.021760417800021747 | 0.021760417800021747 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.05052748456692471 | 0.050527484566924706 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.full.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.028780791496715117 | 0.028780791496715113 | 3.469446951953614e-18 | ok | .01  |
| conditions.full.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.0805371023026979 | 0.08053710230269788 | 1.3877787807814457e-17 | ok | .01  |
| conditions.full.mechanisms.M5.aurc_trapezoid.point | 0.050147619847779525 | 0.050147619847779525 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.risk_0.5.upper | 0.0892396786848489 | 0.0892396786848489 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.7.point | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.7.lower | 0.035211267605633804 | 0.035211267605633804 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.risk_0.8.upper | 0.1656441717791411 | 0.1656441717791411 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.9.point | 0.12637362637362637 | 0.12637362637362637 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.risk_0.9.lower | 0.07692307692307693 | 0.07692307692307693 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.risk_0.9.upper | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.5.point | -0.12376237623762376 | -0.12376237623762376 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.5.lower | -0.1634634051640458 | -0.1634634051640458 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.5.upper | -0.06626453907526683 | -0.06626453907526683 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.6.point | -0.08789157604285018 | -0.08789157604285018 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.6.lower | -0.13098530145697496 | -0.13098530145697496 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.6.upper | -0.043495374127576716 | -0.043495374127576716 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.7.point | -0.06895830428113234 | -0.06895830428113234 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.7.lower | -0.11468818756875689 | -0.11468818756875689 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.7.upper | -0.03649312334402464 | -0.03649312334402464 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.8.point | -0.04235423542354236 | -0.04235423542354236 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.8.lower | -0.07804839021734485 | -0.07804839021734485 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.8.upper | -0.015155543332111016 | -0.015155543332111016 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.9.point | -0.027091720161027094 | -0.027091720161027094 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M5.D_0.9.lower | -0.05066818157225557 | -0.05066818157225557 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M5.D_0.9.upper | -0.006146478230961268 | -0.006146478230961268 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.09205372202438773 | 0.09205372202438773 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.05755344115300282 | 0.057553441153002816 | 6.938893903907228e-18 | ok | .01  |
| conditions.full.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.13724323050348053 | 0.13724323050348056 | -2.7755575615628914e-17 | ok | .01  |
| conditions.full.mechanisms.M6.aurc_trapezoid.point | 0.09147779809536118 | 0.09147779809536116 | 1.3877787807814457e-17 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.5.point | 0.0891089108910891 | 0.0891089108910891 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.5.lower | 0.039603960396039604 | 0.039603960396039604 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.risk_0.5.upper | 0.1485148514851485 | 0.1485148514851485 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.6.point | 0.09016393442622951 | 0.09016393442622951 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.6.lower | 0.04878048780487805 | 0.04878048780487805 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.risk_0.6.upper | 0.1557377049180328 | 0.1557377049180328 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.7.point | 0.11267605633802817 | 0.11267605633802817 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.7.lower | 0.06338028169014084 | 0.06338028169014084 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.risk_0.7.upper | 0.1724437260536397 | 0.1724437260536397 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.8.point | 0.15432098765432098 | 0.15432098765432098 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.8.lower | 0.09259259259259259 | 0.09259259259259259 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.risk_0.8.upper | 0.2208929788684388 | 0.2208929788684388 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.9.point | 0.1978021978021978 | 0.1978021978021978 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.risk_0.9.lower | 0.1428376268540203 | 0.1428376268540203 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.risk_0.9.upper | 0.2623311115114392 | 0.2623311115114392 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.always_predict_risk | 0.23267326732673269 | 0.23267326732673269 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.n_errors | 47 | 47 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.5.point | -0.14356435643564358 | -0.14356435643564358 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.5.lower | -0.19917692011919638 | -0.19917692011919638 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.5.upper | -0.08503203261502619 | -0.08503203261502619 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.6.point | -0.14250933290050316 | -0.14250933290050316 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.6.lower | -0.18535951955851326 | -0.18535951955851326 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.6.upper | -0.08804605220618027 | -0.08804605220618027 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.7.point | -0.11999721098870451 | -0.11999721098870451 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.7.lower | -0.16169292985636594 | -0.16169292985636594 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.7.upper | -0.0718083251987171 | -0.0718083251987171 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.8.point | -0.0783522796724117 | -0.0783522796724117 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.8.lower | -0.11234814432363482 | -0.11234814432363482 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.8.upper | -0.044006356936506695 | -0.044006356936506695 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.9.point | -0.03487106952453489 | -0.03487106952453489 | 0.0 | ok | 1e-9  |
| conditions.full.mechanisms.M6.D_0.9.lower | -0.05576107061255575 | -0.05576107061255575 | 0.0 | ok | .01  |
| conditions.full.mechanisms.M6.D_0.9.upper | -0.009143537304550142 | -0.009143537304550142 | 0.0 | ok | .01  |
| conditions.full.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.full.conformal.0.05.coverage | 0.9851485148514851 | 0.9851485148514851 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.abstention_rate | 0.5247524752475248 | 0.5247524752475248 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.full_count | 106 | 106 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.singleton_count | 96 | 96 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.singleton_true_label_fraction | 0.96875 | 0.96875 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.deviation.point | 0.03514851485148518 | 0.03514851485148518 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.05.deviation.lower | -0.03910891089108903 | -0.03415841584158408 | -0.004950495049504955 | ok | .01  |
| conditions.full.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.full.conformal.0.05.deviation.half_width | 0.04455445544554454 | 0.04207920792079206 | 0.0024752475247524774 | ok | .01  |
| conditions.full.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.full.conformal.0.1.coverage | 0.9306930693069307 | 0.9306930693069307 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.abstention_rate | 0.24257425742574257 | 0.24257425742574257 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.full_count | 49 | 49 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.singleton_count | 153 | 153 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.singleton_true_label_fraction | 0.9084967320261438 | 0.9084967320261438 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.deviation.point | 0.03069306930693072 | 0.03069306930693072 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.1.deviation.lower | -0.08316831683168324 | -0.07821782178217829 | -0.004950495049504955 | ok | .01  |
| conditions.full.conformal.0.1.deviation.upper | 0.08019801980198016 | 0.08019801980198016 | 0.0 | ok | .01  |
| conditions.full.conformal.0.1.deviation.half_width | 0.0816831683168317 | 0.07920792079207922 | 0.0024752475247524774 | ok | .01  |
| conditions.full.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.full.conformal.0.2.coverage | 0.7376237623762376 | 0.7376237623762376 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.abstention_rate | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.empty_count | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.singleton_count | 169 | 169 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.singleton_true_label_fraction | 0.8816568047337278 | 0.8816568047337278 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.deviation.point | -0.06237623762376243 | -0.06237623762376243 | 0.0 | ok | 1e-9  |
| conditions.full.conformal.0.2.deviation.lower | -0.2110148514851486 | -0.1960396039603961 | -0.014975247524752489 | DISCREPANCY | .01 C4_MC |
| conditions.full.conformal.0.2.deviation.upper | 0.0762376237623762 | 0.0861386138613861 | -0.00990099009900991 | ok | .01  |
| conditions.full.conformal.0.2.deviation.half_width | 0.1436262376237624 | 0.1410891089108911 | 0.0025371287128712894 | ok | .01  |
| conditions.full.oracle_aurc | 0.023551612587001277 | 0.0128083489181176 | 0.010743263668883677 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.full.c5_adjacent.0.5-0.6.point | -0.03587080019477358 | -0.03587080019477358 | 0.0 | ok | 1e-9  |
| conditions.full.c5_adjacent.0.5-0.6.lower | -0.06707850339113608 | -0.06707850339113608 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.5-0.6.upper | 0.007141697776335013 | 0.007141697776335013 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.6-0.7.point | -0.018933271761717843 | -0.018933271761717843 | 0.0 | ok | 1e-9  |
| conditions.full.c5_adjacent.0.6-0.7.lower | -0.045466016292192865 | -0.045466016292192865 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.6-0.7.upper | 0.01127299808514821 | 0.01127299808514821 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.7-0.8.point | -0.02660406885758998 | -0.02660406885758998 | 0.0 | ok | 1e-9  |
| conditions.full.c5_adjacent.0.7-0.8.lower | -0.06007650843331594 | -0.06007650843331594 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.7-0.8.upper | -0.0027816981415875433 | -0.0027816981415875433 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.8-0.9.point | -0.015262515262515264 | -0.015262515262515264 | 0.0 | ok | 1e-9  |
| conditions.full.c5_adjacent.0.8-0.9.lower | -0.044753510378510386 | -0.044753510378510386 | 0.0 | ok | .01  |
| conditions.full.c5_adjacent.0.8-0.9.upper | 0.0067171191488131195 | 0.0067171191488131195 | 0.0 | ok | .01  |
| conditions.full.c6_enrichment.0.5.observed | 0.12376237623762379 | 0.12376237623762379 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.5.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.5.rejected_but_correct_rate | 0.7227722772277227 | 0.7227722772277227 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.5.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.6.observed | 0.13403465346534651 | 0.13403465346534651 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.6.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.6.rejected_but_correct_rate | 0.7125 | 0.7125 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.6.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.7.observed | 0.1632013201320132 | 0.1632013201320132 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.7.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.7.rejected_but_correct_rate | 0.6833333333333333 | 0.6833333333333333 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.7.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.8.observed | 0.17153465346534655 | 0.17153465346534655 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.8.p_value | 23/10001 | 0.0015998400159984002 | 34999999999999997999/50005000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.8.rejected_but_correct_rate | 0.675 | 0.675 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.8.p_adjusted | 115/40004 | 7999200079992001/4000000000000000000 | 34999999999999997999/40004000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.9.observed | 0.24653465346534656 | 0.24653465346534656 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.9.p_value | 48/10001 | 0.0035996400359964 | 30000000000000009/25002500000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.9.rejected_but_correct_rate | 0.6 | 0.6 | 0.0 | ok | 1e-9  |
| conditions.full.c6_enrichment.0.9.p_adjusted | 48/10001 | 8999100089991/2500000000000000 | 30000000000000009/25002500000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.full.auroc_bootstrap_95_interval.lower | 0.8919764827064027 | 0.8919764827064027 | 0.0 | ok | .01  |
| conditions.full.auroc_bootstrap_95_interval.upper | 0.9595573115690432 | 0.9595573115690432 | 0.0 | ok | .01  |
| conditions.full.auroc_hanley_mcneil_95_interval.lower | 0.8875476030185966 | 0.8875476033423028 | -3.237061729777224e-10 | ok | .01  |
| conditions.full.auroc_hanley_mcneil_95_interval.upper | 0.9696245281289445 | 0.9696245278052383 | 3.237061729777224e-10 | ok | .01  |
| conditions.full.auroc_valid_draws | 2000 | 2000 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.n_errors | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.always_predict_risk | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.05755315126837404 | 0.057553151268374035 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.03401188999848717 | 0.03401188999848717 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.0901407019406821 | 0.09014070194068212 | -1.3877787807814457e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.aurc_trapezoid.point | 0.057148779147993684 | 0.057148779147993684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.5.point | 0.04950495049504951 | 0.04950495049504951 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.5.lower | 0.009900990099009901 | 0.009900990099009901 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.risk_0.5.upper | 0.09920455637796684 | 0.09920455637796684 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.7.point | 0.07746478873239436 | 0.07746478873239436 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.7.lower | 0.041666666666666664 | 0.041666666666666664 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.risk_0.8.upper | 0.16666666666666666 | 0.16666666666666666 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.9.point | 0.14835164835164835 | 0.14835164835164835 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.risk_0.9.lower | 0.09340659340659341 | 0.09340659340659341 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.risk_0.9.upper | 0.2032967032967033 | 0.2032967032967033 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.always_predict_risk | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.n_errors | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.5.point | -0.11386138613861387 | -0.11386138613861387 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.5.lower | -0.16336633663366334 | -0.16336633663366334 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.6.point | -0.09779256614186009 | -0.09779256614186009 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.6.lower | -0.142889197456331 | -0.142889197456331 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.6.upper | -0.053558675539685144 | -0.053558675539685144 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.7.point | -0.08590154790126901 | -0.08590154790126901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.7.lower | -0.11923362162868509 | -0.11923362162868509 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.7.upper | -0.04134648720153706 | -0.04134648720153706 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.8.point | -0.05225522552255227 | -0.05225522552255227 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.8.lower | -0.08446400195575113 | -0.08446400195575113 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.8.upper | -0.020229800757853578 | -0.020229800757853578 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.9.point | -0.01501468828201502 | -0.01501468828201502 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M1.D_0.9.lower | -0.03808073115003807 | -0.03808073115003807 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M1.D_0.9.upper | 0.004144487400245043 | 0.004144487400245043 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.05755315126837404 | 0.057553151268374035 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.03401188999848717 | 0.03401188999848717 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.0901407019406821 | 0.09014070194068212 | -1.3877787807814457e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.aurc_trapezoid.point | 0.057148779147993684 | 0.057148779147993684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.5.point | 0.04950495049504951 | 0.04950495049504951 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.5.lower | 0.009900990099009901 | 0.009900990099009901 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.risk_0.5.upper | 0.09920455637796684 | 0.09920455637796684 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.7.point | 0.07746478873239436 | 0.07746478873239436 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.7.lower | 0.041666666666666664 | 0.041666666666666664 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.risk_0.8.upper | 0.16666666666666666 | 0.16666666666666666 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.9.point | 0.14835164835164835 | 0.14835164835164835 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.risk_0.9.lower | 0.09340659340659341 | 0.09340659340659341 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.risk_0.9.upper | 0.2032967032967033 | 0.2032967032967033 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.always_predict_risk | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.n_errors | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.5.point | -0.11386138613861387 | -0.11386138613861387 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.5.lower | -0.16336633663366334 | -0.16336633663366334 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.6.point | -0.09779256614186009 | -0.09779256614186009 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.6.lower | -0.142889197456331 | -0.142889197456331 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.6.upper | -0.053558675539685144 | -0.053558675539685144 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.7.point | -0.08590154790126901 | -0.08590154790126901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.7.lower | -0.11923362162868509 | -0.11923362162868509 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.7.upper | -0.04134648720153706 | -0.04134648720153706 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.8.point | -0.05225522552255227 | -0.05225522552255227 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.8.lower | -0.08446400195575113 | -0.08446400195575113 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.8.upper | -0.020229800757853578 | -0.020229800757853578 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.9.point | -0.01501468828201502 | -0.01501468828201502 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M2.D_0.9.lower | -0.03808073115003807 | -0.03808073115003807 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M2.D_0.9.upper | 0.004144487400245043 | 0.004144487400245043 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.06088963120805249 | 0.06088963120805249 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.034689011831165795 | 0.034689011831165795 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.09556201265474044 | 0.09556201265474046 | -1.3877787807814457e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.aurc_trapezoid.point | 0.06048525908767213 | 0.06048525908767213 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.5.point | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.5.lower | 0.0196078431372549 | 0.0196078431372549 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.risk_0.5.upper | 0.10891089108910891 | 0.10891089108910891 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.6.point | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.6.lower | 0.024390243902439025 | 0.024390243902439025 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.risk_0.6.upper | 0.10655737704918032 | 0.10655737704918032 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.7.point | 0.07746478873239436 | 0.07746478873239436 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.7.lower | 0.035211267605633804 | 0.035211267605633804 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.risk_0.7.upper | 0.13390602234094162 | 0.13390602234094162 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.8.point | 0.11728395061728394 | 0.11728395061728394 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.risk_0.8.upper | 0.17177914110429449 | 0.17177914110429449 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.9.point | 0.14835164835164835 | 0.14835164835164835 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.risk_0.9.lower | 0.09836065573770492 | 0.09836065573770492 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.risk_0.9.upper | 0.20334942084942056 | 0.20334942084942056 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.always_predict_risk | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.n_errors | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.5.point | -0.10396039603960397 | -0.10396039603960397 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.5.lower | -0.1584158415841584 | -0.1584158415841584 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.5.upper | -0.05445544554455446 | -0.05445544554455446 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.6.point | -0.1059892874533355 | -0.1059892874533355 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.6.lower | -0.15038143158578152 | -0.15038143158578152 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.6.upper | -0.05680895958448305 | -0.05680895958448305 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.7.point | -0.08590154790126901 | -0.08590154790126901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.7.lower | -0.12399072653744247 | -0.12399072653744247 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.7.upper | -0.042420498651977875 | -0.042420498651977875 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.8.point | -0.04608238601637943 | -0.04608238601637943 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.8.lower | -0.08383726920749335 | -0.08383726920749335 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.8.upper | -0.018946339078352276 | -0.018946339078352276 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.9.point | -0.01501468828201502 | -0.01501468828201502 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M3.D_0.9.lower | -0.03699341983887831 | -0.03699341983887831 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M3.D_0.9.upper | 0.005875312806005867 | 0.005875312806005867 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.11203365770934595 | 0.11203365770934595 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.06917869969577967 | 0.06917869969577965 | 1.3877787807814457e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.1656063485452943 | 0.16560634854529427 | 2.7755575615628914e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.aurc_trapezoid.point | 0.11164153928958319 | 0.11164153928958319 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.5.point | 0.13861386138613863 | 0.13861386138613863 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.5.lower | 0.06930693069306931 | 0.06930693069306931 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.risk_0.5.upper | 0.21364458404721082 | 0.21364458404721082 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.6.point | 0.16393442622950818 | 0.16393442622950818 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.6.lower | 0.0967741935483871 | 0.0967741935483871 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.risk_0.6.upper | 0.23577235772357724 | 0.23577235772357724 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.7.point | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.7.lower | 0.1056338028169014 | 0.1056338028169014 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.risk_0.7.upper | 0.2323943661971831 | 0.2323943661971831 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.8.point | 0.1728395061728395 | 0.1728395061728395 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.8.lower | 0.1165644171779141 | 0.1165644171779141 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.risk_0.8.upper | 0.23170731707317074 | 0.23170731707317074 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.9.point | 0.16483516483516483 | 0.16483516483516483 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.risk_0.9.lower | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.risk_0.9.upper | 0.21978021978021978 | 0.21978021978021978 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.always_predict_risk | 0.15841584158415842 | 0.15841584158415842 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.n_errors | 32 | 32 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.5.point | -0.019801980198019792 | -0.019801980198019792 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.5.lower | -0.07503640069889342 | -0.07503640069889342 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.5.upper | 0.03281158998252766 | 0.03281158998252766 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.6.point | 0.005518584645349767 | 0.005518584645349767 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.6.lower | -0.04366580100633014 | -0.04366580100633014 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.6.upper | 0.04766260162601622 | 0.04766260162601622 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.7.point | 0.0035559894017570814 | 0.0035559894017570814 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.7.lower | -0.026723957607028306 | -0.026723957607028306 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.7.upper | 0.040315158276390935 | 0.040315158276390935 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.8.point | 0.014423664588681079 | 0.014423664588681079 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.8.lower | -0.010267693436010278 | -0.010267693436010278 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.8.upper | 0.03404247945119714 | 0.03404247945119714 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.9.point | 0.006419323251006415 | 0.006419323251006415 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M4.D_0.9.lower | -0.010608203677510614 | -0.010608203677510614 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M4.D_0.9.upper | 0.017989503868419632 | 0.017989503868419632 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.05755315126837404 | 0.057553151268374035 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.03401188999848717 | 0.03401188999848717 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.0901407019406821 | 0.09014070194068212 | -1.3877787807814457e-17 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.aurc_trapezoid.point | 0.057148779147993684 | 0.057148779147993684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.5.point | 0.04950495049504951 | 0.04950495049504951 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.5.lower | 0.009900990099009901 | 0.009900990099009901 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.risk_0.5.upper | 0.09920455637796684 | 0.09920455637796684 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.risk_0.6.upper | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.7.point | 0.07746478873239436 | 0.07746478873239436 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.7.lower | 0.041666666666666664 | 0.041666666666666664 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.risk_0.7.upper | 0.13380281690140844 | 0.13380281690140844 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.8.point | 0.1111111111111111 | 0.1111111111111111 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.8.lower | 0.06172839506172839 | 0.06172839506172839 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.risk_0.8.upper | 0.16666666666666666 | 0.16666666666666666 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.9.point | 0.14835164835164835 | 0.14835164835164835 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.risk_0.9.lower | 0.09340659340659341 | 0.09340659340659341 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.risk_0.9.upper | 0.2032967032967033 | 0.2032967032967033 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.always_predict_risk | 0.16336633663366337 | 0.16336633663366337 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.n_errors | 33 | 33 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.5.point | -0.11386138613861387 | -0.11386138613861387 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.5.lower | -0.16336633663366334 | -0.16336633663366334 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.6.point | -0.09779256614186009 | -0.09779256614186009 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.6.lower | -0.142889197456331 | -0.142889197456331 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.6.upper | -0.053558675539685144 | -0.053558675539685144 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.7.point | -0.08590154790126901 | -0.08590154790126901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.7.lower | -0.11923362162868509 | -0.11923362162868509 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.7.upper | -0.04134648720153706 | -0.04134648720153706 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.8.point | -0.05225522552255227 | -0.05225522552255227 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.8.lower | -0.08446400195575113 | -0.08446400195575113 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.8.upper | -0.020229800757853578 | -0.020229800757853578 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.9.point | -0.01501468828201502 | -0.01501468828201502 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M5.D_0.9.lower | -0.03808073115003807 | -0.03808073115003807 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M5.D_0.9.upper | 0.004144487400245043 | 0.004144487400245043 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.06542083211693928 | 0.06542083211693928 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.038883893966476374 | 0.038883893966476374 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.10091504575021557 | 0.10091504575021557 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.aurc_trapezoid.point | 0.06493068409223582 | 0.06493068409223582 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.risk_0.5.upper | 0.08823529411764706 | 0.08823529411764706 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.6.lower | 0.024390243902439025 | 0.024390243902439025 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.risk_0.6.upper | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.7.point | 0.1056338028169014 | 0.1056338028169014 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.7.lower | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.risk_0.7.upper | 0.15492957746478872 | 0.15492957746478872 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.8.point | 0.12345679012345678 | 0.12345679012345678 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.8.lower | 0.0736196319018405 | 0.0736196319018405 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.risk_0.8.upper | 0.18295488553045025 | 0.18295488553045025 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.9.point | 0.17582417582417584 | 0.17582417582417584 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.risk_0.9.lower | 0.11538461538461539 | 0.11538461538461539 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.risk_0.9.upper | 0.23087431693989016 | 0.23087431693989016 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.always_predict_risk | 0.19801980198019803 | 0.19801980198019803 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.n_errors | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.5.point | -0.16831683168316833 | -0.16831683168316833 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.5.lower | -0.21287128712871287 | -0.21287128712871287 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.5.upper | -0.10891089108910892 | -0.10891089108910892 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.6.point | -0.13244603148839473 | -0.13244603148839473 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.6.lower | -0.17717957132062537 | -0.17717957132062537 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.6.upper | -0.08277732982182408 | -0.08277732982182408 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.7.point | -0.09238599916329662 | -0.09238599916329662 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.7.lower | -0.14112397155208478 | -0.14112397155208478 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.7.upper | -0.05772157524528191 | -0.05772157524528191 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.8.point | -0.07456301185674125 | -0.07456301185674125 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.8.lower | -0.10665108177484416 | -0.10665108177484416 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.8.upper | -0.04130347850735993 | -0.04130347850735993 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.9.point | -0.02219562615602219 | -0.02219562615602219 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.mechanisms.M6.D_0.9.lower | -0.04858013273854858 | -0.04858013273854858 | 0.0 | ok | .01  |
| conditions.drop_t1.mechanisms.M6.D_0.9.upper | -0.0027385843983543543 | -0.0027385843983543543 | 0.0 | ok | .01  |
| conditions.drop_t1.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.coverage | 0.9851485148514851 | 0.9851485148514851 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.abstention_rate | 0.5792079207920792 | 0.5792079207920792 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.full_count | 117 | 117 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.singleton_count | 85 | 85 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.singleton_true_label_fraction | 0.9647058823529412 | 0.9647058823529412 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.deviation.point | 0.03514851485148518 | 0.03514851485148518 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.05.deviation.lower | -0.03910891089108903 | -0.03415841584158408 | -0.004950495049504955 | ok | .01  |
| conditions.drop_t1.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.drop_t1.conformal.0.05.deviation.half_width | 0.04455445544554454 | 0.04207920792079206 | 0.0024752475247524774 | ok | .01  |
| conditions.drop_t1.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.coverage | 0.9257425742574258 | 0.9257425742574258 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.abstention_rate | 0.24752475247524752 | 0.24752475247524752 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.full_count | 50 | 50 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.singleton_count | 152 | 152 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.singleton_true_label_fraction | 0.9013157894736842 | 0.9013157894736842 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.deviation.point | 0.025742574257425765 | 0.025742574257425765 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.1.deviation.lower | -0.09306930693069304 | -0.09306930693069304 | 0.0 | ok | .01  |
| conditions.drop_t1.conformal.0.1.deviation.upper | 0.08019801980198016 | 0.08019801980198016 | 0.0 | ok | .01  |
| conditions.drop_t1.conformal.0.1.deviation.half_width | 0.0866336633663366 | 0.0866336633663366 | 0.0 | ok | .01  |
| conditions.drop_t1.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.coverage | 0.7475247524752475 | 0.7475247524752475 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.abstention_rate | 0.13861386138613863 | 0.13861386138613863 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.empty_count | 28 | 28 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.singleton_count | 174 | 174 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.singleton_true_label_fraction | 0.867816091954023 | 0.867816091954023 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.deviation.point | -0.05247524752475252 | -0.05247524752475252 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.conformal.0.2.deviation.lower | -0.24554455445544554 | -0.22079207920792088 | -0.024752475247524663 | DISCREPANCY | .01 C4_MC |
| conditions.drop_t1.conformal.0.2.deviation.upper | 0.06138613861386133 | 0.06633663366336628 | -0.004950495049504955 | ok | .01  |
| conditions.drop_t1.conformal.0.2.deviation.half_width | 0.15346534653465344 | 0.14356435643564358 | 0.009900990099009854 | ok | .01  |
| conditions.drop_t1.oracle_aurc | 0.02668855994510342 | 0.014540481087361468 | 0.012148078857741952 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.drop_t1.c5_adjacent.0.5-0.6.point | -0.016068819996753775 | -0.016068819996753775 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c5_adjacent.0.5-0.6.lower | -0.04597056390399671 | -0.04597056390399671 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.5-0.6.upper | 0.011722206865652087 | 0.011722206865652087 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.6-0.7.point | -0.011891018240591078 | -0.011891018240591078 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c5_adjacent.0.6-0.7.lower | -0.050565689217270844 | -0.050565689217270844 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.6-0.7.upper | 0.0069268067420918955 | 0.0069268067420918955 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.7-0.8.point | -0.033646322378716745 | -0.033646322378716745 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c5_adjacent.0.7-0.8.lower | -0.05668484571953644 | -0.05668484571953644 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.7-0.8.upper | -0.0010290955000624752 | -0.0010290955000624752 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.8-0.9.point | -0.03724053724053725 | -0.03724053724053725 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c5_adjacent.0.8-0.9.lower | -0.0626119251119251 | -0.0626119251119251 | 0.0 | ok | .01  |
| conditions.drop_t1.c5_adjacent.0.8-0.9.upper | -0.010319928698687652 | -0.010319928698687652 | 0.0 | ok | .01  |
| conditions.drop_t1.c6_enrichment.0.5.observed | 0.11386138613861388 | 0.11386138613861388 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.5.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.5.rejected_but_correct_rate | 0.7227722772277227 | 0.7227722772277227 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.5.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.6.observed | 0.14913366336633663 | 0.14913366336633663 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.6.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.6.rejected_but_correct_rate | 0.6875 | 0.6875 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.6.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.7.observed | 0.20330033003300327 | 0.20330033003300327 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.7.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.7.rejected_but_correct_rate | 0.6333333333333333 | 0.6333333333333333 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.7.p_adjusted | 5/30003 | 4999500049995001/30000000000000000000 | -1667/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.8.observed | 0.21163366336633663 | 0.21163366336633663 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.8.p_value | 2/10001 | 0.00019998000199980003 | -10003/1000100000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.8.rejected_but_correct_rate | 0.625 | 0.625 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.8.p_adjusted | 5/20002 | 19998000199980003/80000000000000000000 | -10003/800080000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.9.observed | 0.13663366336633662 | 0.13663366336633662 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.9.p_value | 838/10001 | 0.0811918808119188 | 65000000000000203/25002500000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.9.rejected_but_correct_rate | 0.7 | 0.7 | 0.0 | ok | 1e-9  |
| conditions.drop_t1.c6_enrichment.0.9.p_adjusted | 838/10001 | 202979702029797/2500000000000000 | 65000000000000203/25002500000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.n_errors | 91 | 91 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.always_predict_risk | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.31038238353450354 | 0.31038238353450354 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.23500765013410016 | 0.2350076501341001 | 5.551115123125783e-17 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.3962888931648692 | 0.3962888931648692 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.aurc_trapezoid.point | 0.3092672967783031 | 0.3092672967783031 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.5.point | 0.31683168316831684 | 0.31683168316831684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.5.lower | 0.21782178217821782 | 0.21782178217821782 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.5.upper | 0.39603960396039606 | 0.39603960396039606 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.6.point | 0.3442622950819672 | 0.3442622950819672 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.6.lower | 0.25203252032520324 | 0.25203252032520324 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.6.upper | 0.4355094726062467 | 0.4355094726062467 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.7.point | 0.39436619718309857 | 0.39436619718309857 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.7.lower | 0.30985915492957744 | 0.30985915492957744 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.7.upper | 0.4859154929577465 | 0.4859154929577465 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.8.point | 0.4444444444444444 | 0.4444444444444444 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.8.lower | 0.36809815950920244 | 0.36809815950920244 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.8.upper | 0.5214723926380368 | 0.5214723926380368 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.9.point | 0.44505494505494503 | 0.44505494505494503 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.9.lower | 0.3770491803278688 | 0.3770491803278688 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.risk_0.9.upper | 0.5164835164835165 | 0.5164835164835165 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.always_predict_risk | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.n_errors | 91 | 91 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.5.point | -0.13366336633663367 | -0.13366336633663367 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.5.lower | -0.21287128712871284 | -0.21287128712871284 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.5.upper | -0.07318724519510779 | -0.07318724519510779 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.6.point | -0.1062327544229833 | -0.1062327544229833 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.6.lower | -0.16277973958931283 | -0.16277973958931283 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.6.upper | -0.04788455904766813 | -0.04788455904766813 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.7.point | -0.05612885232185194 | -0.05612885232185194 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.7.lower | -0.09915806721517223 | -0.09915806721517223 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.7.upper | -0.0020722670858635663 | -0.0020722670858635663 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.8.point | -0.006050605060506087 | -0.006050605060506087 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.8.lower | -0.04308917002811396 | -0.04308917002811396 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.8.upper | 0.02982520474269651 | 0.02982520474269651 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.9.point | -0.0054401044500054785 | -0.0054401044500054785 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M1.D_0.9.lower | -0.026973118953021482 | -0.026973118953021482 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M1.D_0.9.upper | 0.0193776520509193 | 0.0193776520509193 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.31038238353450354 | 0.31038238353450354 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.23500765013410016 | 0.2350076501341001 | 5.551115123125783e-17 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.3962888931648692 | 0.3962888931648692 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.aurc_trapezoid.point | 0.3092672967783031 | 0.3092672967783031 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.5.point | 0.31683168316831684 | 0.31683168316831684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.5.lower | 0.21782178217821782 | 0.21782178217821782 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.5.upper | 0.39603960396039606 | 0.39603960396039606 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.6.point | 0.3442622950819672 | 0.3442622950819672 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.6.lower | 0.25203252032520324 | 0.25203252032520324 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.6.upper | 0.4355094726062467 | 0.4355094726062467 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.7.point | 0.39436619718309857 | 0.39436619718309857 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.7.lower | 0.30985915492957744 | 0.30985915492957744 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.7.upper | 0.4859154929577465 | 0.4859154929577465 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.8.point | 0.4444444444444444 | 0.4444444444444444 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.8.lower | 0.36809815950920244 | 0.36809815950920244 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.8.upper | 0.5214723926380368 | 0.5214723926380368 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.9.point | 0.44505494505494503 | 0.44505494505494503 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.9.lower | 0.3770491803278688 | 0.3770491803278688 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.risk_0.9.upper | 0.5164835164835165 | 0.5164835164835165 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.always_predict_risk | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.n_errors | 91 | 91 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.5.point | -0.13366336633663367 | -0.13366336633663367 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.5.lower | -0.21287128712871284 | -0.21287128712871284 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.5.upper | -0.07318724519510779 | -0.07318724519510779 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.6.point | -0.1062327544229833 | -0.1062327544229833 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.6.lower | -0.16277973958931283 | -0.16277973958931283 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.6.upper | -0.04788455904766813 | -0.04788455904766813 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.7.point | -0.05612885232185194 | -0.05612885232185194 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.7.lower | -0.09915806721517223 | -0.09915806721517223 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.7.upper | -0.0020722670858635663 | -0.0020722670858635663 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.8.point | -0.006050605060506087 | -0.006050605060506087 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.8.lower | -0.04308917002811396 | -0.04308917002811396 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.8.upper | 0.02982520474269651 | 0.02982520474269651 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.9.point | -0.0054401044500054785 | -0.0054401044500054785 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M2.D_0.9.lower | -0.026973118953021482 | -0.026973118953021482 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M2.D_0.9.upper | 0.0193776520509193 | 0.0193776520509193 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.2901795900889756 | 0.2901795900889756 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.22003429582720319 | 0.22003429582720319 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.3696369610921511 | 0.3696369610921511 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.aurc_trapezoid.point | 0.2890645033327752 | 0.2890645033327752 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.5.point | 0.26732673267326734 | 0.26732673267326734 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.5.lower | 0.19607843137254902 | 0.19607843137254902 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.5.upper | 0.38613861386138615 | 0.38613861386138615 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.6.point | 0.3442622950819672 | 0.3442622950819672 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.6.lower | 0.2601626016260163 | 0.2601626016260163 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.6.upper | 0.4435483870967742 | 0.4435483870967742 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.7.point | 0.39436619718309857 | 0.39436619718309857 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.7.lower | 0.31690140845070425 | 0.31690140845070425 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.7.upper | 0.48951048951048953 | 0.48951048951048953 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.8.point | 0.4444444444444444 | 0.4444444444444444 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.8.lower | 0.37031356509884117 | 0.37031356509884117 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.8.upper | 0.5215528667727027 | 0.5215528667727027 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.9.point | 0.45604395604395603 | 0.45604395604395603 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.9.lower | 0.3825136612021858 | 0.3825136612021858 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.risk_0.9.upper | 0.521978021978022 | 0.521978021978022 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.always_predict_risk | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.n_errors | 91 | 91 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.5.point | -0.18316831683168316 | -0.18316831683168316 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.5.lower | -0.23030722189866046 | -0.23030722189866046 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.5.upper | -0.08910891089108913 | -0.08910891089108913 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.6.point | -0.1062327544229833 | -0.1062327544229833 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.6.lower | -0.15642535065181848 | -0.15642535065181848 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.6.upper | -0.04082129524427852 | -0.04082129524427852 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.7.point | -0.05612885232185194 | -0.05612885232185194 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.7.lower | -0.09705759308325196 | -0.09705759308325196 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.7.upper | 0.004188746339422619 | 0.004188746339422619 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.8.point | -0.006050605060506087 | -0.006050605060506087 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.8.lower | -0.04063673835004497 | -0.04063673835004497 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.8.upper | 0.03356339468302653 | 0.03356339468302653 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.9.point | 0.005548906539005527 | 0.005548906539005527 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M3.D_0.9.lower | -0.022216048843219732 | -0.022216048843219732 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M3.D_0.9.upper | 0.022576433467522583 | 0.022576433467522583 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.39304284185871213 | 0.39304284185871213 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.2961564734881671 | 0.2961564734881671 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.4909794040904188 | 0.4909794040904188 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.aurc_trapezoid.point | 0.3921238143123932 | 0.3921238143123932 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.5.point | 0.38613861386138615 | 0.38613861386138615 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.5.lower | 0.291158800346054 | 0.291158800346054 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.5.upper | 0.48514851485148514 | 0.48514851485148514 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.6.point | 0.3524590163934426 | 0.3524590163934426 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.6.lower | 0.27049180327868855 | 0.27049180327868855 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.6.upper | 0.44264608672659955 | 0.44264608672659955 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.7.point | 0.38028169014084506 | 0.38028169014084506 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.7.lower | 0.2937062937062937 | 0.2937062937062937 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.7.upper | 0.45774647887323944 | 0.45774647887323944 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.8.point | 0.3765432098765432 | 0.3765432098765432 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.8.lower | 0.30246913580246915 | 0.30246913580246915 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.8.upper | 0.4512887176417773 | 0.4512887176417773 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.9.point | 0.36813186813186816 | 0.36813186813186816 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.9.lower | 0.3005464480874317 | 0.3005464480874317 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.risk_0.9.upper | 0.44021739130434784 | 0.44021739130434784 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.always_predict_risk | 0.3712871287128713 | 0.3712871287128713 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.n_errors | 75 | 75 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.5.point | 0.014851485148514865 | 0.014851485148514865 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.5.lower | -0.05445544554455445 | -0.05445544554455445 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.5.upper | 0.08415841584158412 | 0.08415841584158412 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.6.point | -0.018828112319428658 | -0.018828112319428658 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.6.lower | -0.06614186008764811 | -0.06614186008764811 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.6.upper | 0.044880943342879995 | 0.044880943342879995 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.7.point | 0.00899456142797378 | 0.00899456142797378 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.7.lower | -0.03688467438293125 | -0.03688467438293125 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.7.upper | 0.05202414201333457 | 0.05202414201333457 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.8.point | 0.005256081163671933 | 0.005256081163671933 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.8.lower | -0.029155971152670806 | -0.029155971152670806 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.8.upper | 0.04100965652120764 | 0.04100965652120764 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.9.point | -0.0031552605810031276 | -0.0031552605810031276 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M4.D_0.9.lower | -0.025812232862630513 | -0.025812232862630513 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M4.D_0.9.upper | 0.020512422990338872 | 0.020512422990338872 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.31038238353450354 | 0.31038238353450354 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.23500765013410016 | 0.2350076501341001 | 5.551115123125783e-17 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.3962888931648692 | 0.3962888931648692 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.aurc_trapezoid.point | 0.3092672967783031 | 0.3092672967783031 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.5.point | 0.31683168316831684 | 0.31683168316831684 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.5.lower | 0.21782178217821782 | 0.21782178217821782 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.5.upper | 0.39603960396039606 | 0.39603960396039606 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.6.point | 0.3442622950819672 | 0.3442622950819672 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.6.lower | 0.25203252032520324 | 0.25203252032520324 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.6.upper | 0.4355094726062467 | 0.4355094726062467 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.7.point | 0.39436619718309857 | 0.39436619718309857 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.7.lower | 0.30985915492957744 | 0.30985915492957744 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.7.upper | 0.4859154929577465 | 0.4859154929577465 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.8.point | 0.4444444444444444 | 0.4444444444444444 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.8.lower | 0.36809815950920244 | 0.36809815950920244 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.8.upper | 0.5214723926380368 | 0.5214723926380368 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.9.point | 0.44505494505494503 | 0.44505494505494503 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.9.lower | 0.3770491803278688 | 0.3770491803278688 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.risk_0.9.upper | 0.5164835164835165 | 0.5164835164835165 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.always_predict_risk | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.n_errors | 91 | 91 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.5.point | -0.13366336633663367 | -0.13366336633663367 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.5.lower | -0.21287128712871284 | -0.21287128712871284 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.5.upper | -0.07318724519510779 | -0.07318724519510779 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.6.point | -0.1062327544229833 | -0.1062327544229833 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.6.lower | -0.16277973958931283 | -0.16277973958931283 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.6.upper | -0.04788455904766813 | -0.04788455904766813 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.7.point | -0.05612885232185194 | -0.05612885232185194 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.7.lower | -0.09915806721517223 | -0.09915806721517223 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.7.upper | -0.0020722670858635663 | -0.0020722670858635663 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.8.point | -0.006050605060506087 | -0.006050605060506087 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.8.lower | -0.04308917002811396 | -0.04308917002811396 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.8.upper | 0.02982520474269651 | 0.02982520474269651 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.9.point | -0.0054401044500054785 | -0.0054401044500054785 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M5.D_0.9.lower | -0.026973118953021482 | -0.026973118953021482 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M5.D_0.9.upper | 0.0193776520509193 | 0.0193776520509193 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.5892212150002819 | 0.5892212150002819 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.4911316433684857 | 0.4911316433684857 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.6820245931577362 | 0.6820245931577363 | -1.1102230246251565e-16 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.aurc_trapezoid.point | 0.5878120394292594 | 0.5878120394292595 | -1.1102230246251565e-16 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.5.point | 0.6237623762376238 | 0.6237623762376238 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.5.lower | 0.5392156862745098 | 0.5392156862745098 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.5.upper | 0.7254901960784313 | 0.7254901960784313 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.6.point | 0.6147540983606558 | 0.6147540983606558 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.6.lower | 0.5327868852459017 | 0.5327868852459017 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.6.upper | 0.7049180327868853 | 0.7049180327868853 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.7.point | 0.6267605633802817 | 0.6267605633802817 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.7.lower | 0.5422535211267606 | 0.5422535211267606 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.7.upper | 0.704225352112676 | 0.704225352112676 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.8.point | 0.5987654320987654 | 0.5987654320987654 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.8.lower | 0.5246913580246914 | 0.5246913580246914 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.8.upper | 0.6790123456790124 | 0.6790123456790124 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.9.point | 0.5934065934065934 | 0.5934065934065934 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.9.lower | 0.5136612021857924 | 0.5136612021857924 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.risk_0.9.upper | 0.6612021857923497 | 0.6612021857923497 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.always_predict_risk | 0.5693069306930693 | 0.5693069306930693 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.n_errors | 115 | 115 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.5.point | 0.054455445544554504 | 0.054455445544554504 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.5.lower | -0.004950495049504955 | -0.004950495049504955 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.5.upper | 0.13181906425936707 | 0.13181906425936707 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.6.point | 0.0454471676675865 | 0.0454471676675865 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.6.lower | -0.004076042850186636 | -0.004076042850186636 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.6.upper | 0.11149581421556787 | 0.11149581421556787 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.7.point | 0.057453632687212486 | 0.057453632687212486 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.7.lower | 0.007587103340615776 | 0.007587103340615776 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.7.upper | 0.09970715381397299 | 0.09970715381397299 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.8.point | 0.02945850140569617 | 0.02945850140569617 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.8.lower | 0.0009763476347635165 | 0.0009763476347635165 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.8.upper | 0.06765829360713847 | 0.06765829360713847 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.9.point | 0.02409966271352415 | 0.02409966271352415 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.mechanisms.M6.D_0.9.lower | -0.0013345646400345075 | -0.0013345646400345075 | 0.0 | ok | .01  |
| conditions.drop_t1ce.mechanisms.M6.D_0.9.upper | 0.04335914856122612 | 0.04335914856122612 | 0.0 | ok | .01  |
| conditions.drop_t1ce.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.coverage | 0.9158415841584159 | 0.9158415841584159 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.abstention_rate | 0.6831683168316832 | 0.6831683168316832 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.full_count | 138 | 138 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.singleton_count | 64 | 64 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.singleton_true_label_fraction | 0.734375 | 0.734375 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.deviation.point | -0.03415841584158408 | -0.03415841584158408 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.05.deviation.lower | -0.23712871287128712 | -0.22240099009900988 | -0.01472772277227724 | DISCREPANCY | .01 C4_MC |
| conditions.drop_t1ce.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.drop_t1ce.conformal.0.05.deviation.half_width | 0.14356435643564358 | 0.13620049504950496 | 0.00736386138613862 | ok | .01  |
| conditions.drop_t1ce.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.coverage | 0.7277227722772277 | 0.7277227722772277 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.abstention_rate | 0.3069306930693069 | 0.3069306930693069 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.full_count | 62 | 62 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.singleton_count | 140 | 140 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.singleton_true_label_fraction | 0.6071428571428571 | 0.6071428571428571 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.deviation.point | -0.17227722772277232 | -0.17227722772277232 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.1.deviation.lower | -0.3900990099009901 | -0.3803217821782178 | -0.009777227722772286 | ok | .01  |
| conditions.drop_t1ce.conformal.0.1.deviation.upper | -0.0038366336633670153 | -0.008910891089108919 | 0.005074257425741904 | ok | .01  |
| conditions.drop_t1ce.conformal.0.1.deviation.half_width | 0.19313118811881155 | 0.18570544554455445 | 0.007425742574257099 | ok | .01  |
| conditions.drop_t1ce.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.coverage | 0.4504950495049505 | 0.4504950495049505 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.abstention_rate | 0.17326732673267325 | 0.17326732673267325 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.empty_count | 35 | 35 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.singleton_count | 167 | 167 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.singleton_true_label_fraction | 0.5449101796407185 | 0.5449101796407185 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.deviation.point | -0.34950495049504954 | -0.34950495049504954 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.conformal.0.2.deviation.lower | -0.45841584158415843 | -0.4485148514851486 | -0.009900990099009854 | ok | .01  |
| conditions.drop_t1ce.conformal.0.2.deviation.upper | -0.205940594059406 | -0.21089108910891097 | 0.004950495049504955 | ok | .01  |
| conditions.drop_t1ce.conformal.0.2.deviation.half_width | 0.1262376237623762 | 0.11881188118811882 | 0.007425742574257391 | ok | .01  |
| conditions.drop_t1ce.oracle_aurc | 0.2029457896284678 | 0.12259832379770286 | 0.08034746583076494 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.drop_t1ce.c5_adjacent.0.5-0.6.point | -0.02743061191365037 | -0.02743061191365037 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c5_adjacent.0.5-0.6.lower | -0.09129283250784329 | -0.09129283250784329 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.5-0.6.upper | 0.015323682600400065 | 0.015323682600400065 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.6-0.7.point | -0.05010390210113136 | -0.05010390210113136 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c5_adjacent.0.6-0.7.lower | -0.08532067122290363 | -0.08532067122290363 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.6-0.7.upper | -0.018164622262982943 | -0.018164622262982943 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.7-0.8.point | -0.050078247261345854 | -0.050078247261345854 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c5_adjacent.0.7-0.8.lower | -0.07349432527338537 | -0.07349432527338537 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.7-0.8.upper | -0.015674910729276702 | -0.015674910729276702 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.8-0.9.point | -0.0006105006105006083 | -0.0006105006105006083 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c5_adjacent.0.8-0.9.lower | -0.035612535612535634 | -0.035612535612535634 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c5_adjacent.0.8-0.9.upper | 0.029365589155977655 | 0.029365589155977655 | 0.0 | ok | .01  |
| conditions.drop_t1ce.c6_enrichment.0.5.observed | 0.13366336633663362 | 0.13366336633663362 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.5.p_value | 3/10001 | 0.00029997000299970003 | -3/1000100000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.5.rejected_but_correct_rate | 0.4158415841584159 | 0.4158415841584158 | 5.551115123125783e-17 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.5.p_adjusted | 15/20002 | 29997000299970003/40000000000000000000 | -3/400040000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.6.observed | 0.16200495049504954 | 0.16200495049504954 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.6.p_value | 3/10001 | 9.999000099990002e-05 | 99999999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.6.rejected_but_correct_rate | 0.38749999999999996 | 0.3875 | -5.551115123125783e-17 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.6.p_adjusted | 15/20002 | 4999500049995001/10000000000000000000 | 24999999999999994999/100010000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.7.observed | 0.13283828382838286 | 0.13283828382838286 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.7.p_value | 112/10001 | 0.010298970102989701 | 9000000000000000299/10001000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.7.rejected_but_correct_rate | 0.41666666666666663 | 0.4166666666666667 | -5.551115123125783e-17 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.7.p_adjusted | 560/30003 | 10298970102989701/600000000000000000 | 9000000000000000299/6000600000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.8.observed | 0.02450495049504947 | 0.02450495049504947 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.8.p_value | 4255/10001 | 0.43195680431956807 | -6500000000000026807/1000100000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.8.rejected_but_correct_rate | 0.525 | 0.525 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.8.p_adjusted | 4255/10001 | 43195680431956807/100000000000000000 | -6500000000000026807/1000100000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.9.observed | 0.04950495049504949 | 0.04950495049504949 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.9.p_value | 4005/10001 | 0.41175882411758824 | -1412499999999999853/125012500000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t1ce.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.9.rejected_but_correct_rate | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t1ce.c6_enrichment.0.9.p_adjusted | 4255/10001 | 43195680431956807/100000000000000000 | -6500000000000026807/1000100000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.039554363128503425 | 0.03955436312850342 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.0205919389858565 | 0.020591938985856498 | 3.469446951953614e-18 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.06658511751467668 | 0.06658511751467668 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.aurc_trapezoid.point | 0.03923576691244617 | 0.03923576691244617 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.risk_0.5.upper | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.6.point | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.6.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.risk_0.6.upper | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.7.point | 0.07042253521126761 | 0.07042253521126761 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.7.lower | 0.02112676056338028 | 0.02112676056338028 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.risk_0.7.upper | 0.11888111888111888 | 0.11888111888111888 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.8.point | 0.08024691358024691 | 0.08024691358024691 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.8.lower | 0.043209876543209874 | 0.043209876543209874 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.risk_0.8.upper | 0.13416691605566353 | 0.13416691605566353 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.9.point | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.risk_0.9.lower | 0.06043956043956044 | 0.06043956043956044 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.risk_0.9.upper | 0.15934065934065933 | 0.15934065934065933 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.5.point | -0.10891089108910891 | -0.10891089108910891 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.5.lower | -0.15346534653465346 | -0.15346534653465346 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.6.point | -0.10412270735270249 | -0.10412270735270249 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.6.lower | -0.1421872627506008 | -0.1421872627506008 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.6.upper | -0.05786398311962343 | -0.05786398311962343 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.7.point | -0.05829033607586111 | -0.05829033607586111 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.7.lower | -0.10054385720262167 | -0.10054385720262167 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.7.upper | -0.02593586688029585 | -0.02593586688029585 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.8.point | -0.04846595770688181 | -0.04846595770688181 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.8.lower | -0.07867265714301491 | -0.07867265714301491 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.8.upper | -0.01747758109144249 | -0.01747758109144249 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.9.point | -0.018822761397018828 | -0.018822761397018828 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M1.D_0.9.lower | -0.04437118635300749 | -0.04437118635300749 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M1.D_0.9.upper | 0.0008927122220418748 | 0.0008927122220418748 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.039554363128503425 | 0.03955436312850342 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.0205919389858565 | 0.020591938985856498 | 3.469446951953614e-18 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.06658511751467668 | 0.06658511751467668 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.aurc_trapezoid.point | 0.03923576691244617 | 0.03923576691244617 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.risk_0.5.upper | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.6.point | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.6.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.risk_0.6.upper | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.7.point | 0.07042253521126761 | 0.07042253521126761 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.7.lower | 0.02112676056338028 | 0.02112676056338028 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.risk_0.7.upper | 0.11888111888111888 | 0.11888111888111888 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.8.point | 0.08024691358024691 | 0.08024691358024691 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.8.lower | 0.043209876543209874 | 0.043209876543209874 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.risk_0.8.upper | 0.13416691605566353 | 0.13416691605566353 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.9.point | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.risk_0.9.lower | 0.06043956043956044 | 0.06043956043956044 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.risk_0.9.upper | 0.15934065934065933 | 0.15934065934065933 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.5.point | -0.10891089108910891 | -0.10891089108910891 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.5.lower | -0.15346534653465346 | -0.15346534653465346 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.6.point | -0.10412270735270249 | -0.10412270735270249 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.6.lower | -0.1421872627506008 | -0.1421872627506008 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.6.upper | -0.05786398311962343 | -0.05786398311962343 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.7.point | -0.05829033607586111 | -0.05829033607586111 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.7.lower | -0.10054385720262167 | -0.10054385720262167 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.7.upper | -0.02593586688029585 | -0.02593586688029585 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.8.point | -0.04846595770688181 | -0.04846595770688181 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.8.lower | -0.07867265714301491 | -0.07867265714301491 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.8.upper | -0.01747758109144249 | -0.01747758109144249 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.9.point | -0.018822761397018828 | -0.018822761397018828 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M2.D_0.9.lower | -0.04437118635300749 | -0.04437118635300749 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M2.D_0.9.upper | 0.0008927122220418748 | 0.0008927122220418748 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.03926469813125777 | 0.03926469813125777 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.019572597288542555 | 0.019572597288542555 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.06746517782728055 | 0.06746517782728055 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.aurc_trapezoid.point | 0.038946101915200516 | 0.038946101915200516 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.5.point | 0.0297029702970297 | 0.0297029702970297 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.risk_0.5.upper | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.6.point | 0.03278688524590164 | 0.03278688524590164 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.6.lower | 0.008064516129032258 | 0.008064516129032258 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.risk_0.6.upper | 0.07317073170731707 | 0.07317073170731707 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.7.point | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.7.lower | 0.014084507042253521 | 0.014084507042253521 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.risk_0.7.upper | 0.09791933418693972 | 0.09791933418693972 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.8.point | 0.07407407407407407 | 0.07407407407407407 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.8.lower | 0.037037037037037035 | 0.037037037037037035 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.risk_0.8.upper | 0.12883435582822086 | 0.12883435582822086 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.9.point | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.risk_0.9.lower | 0.06043956043956044 | 0.06043956043956044 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.risk_0.9.upper | 0.16393442622950818 | 0.16393442622950818 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.5.point | -0.09900990099009901 | -0.09900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.5.lower | -0.1485148514851485 | -0.1485148514851485 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.5.upper | -0.05940594059405941 | -0.05940594059405941 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.6.point | -0.09592598604122707 | -0.09592598604122707 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.6.lower | -0.13971599479020275 | -0.13971599479020275 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.6.upper | -0.056322025645187464 | -0.056322025645187464 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.7.point | -0.0794170966392414 | -0.0794170966392414 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.7.lower | -0.1153953423511365 | -0.1153953423511365 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.7.upper | -0.04056955803922759 | -0.04056955803922759 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.8.point | -0.054638797213054646 | -0.054638797213054646 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.8.lower | -0.0830598337611539 | -0.0830598337611539 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.8.upper | -0.021268793546021278 | -0.021268793546021278 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.9.point | -0.018822761397018828 | -0.018822761397018828 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M3.D_0.9.lower | -0.044663257534544656 | -0.044663257534544656 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M3.D_0.9.upper | 0.002381589510302401 | 0.002381589510302401 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.17265039964898152 | 0.17265039964898152 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.10014424042751002 | 0.10014424042751002 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.25395095013132424 | 0.2539509501313242 | 5.551115123125783e-17 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.aurc_trapezoid.point | 0.17233180343292429 | 0.17233180343292429 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.5.point | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.5.lower | 0.1188118811881188 | 0.1188118811881188 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.risk_0.5.upper | 0.27722772277227725 | 0.27722772277227725 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.6.point | 0.1721311475409836 | 0.1721311475409836 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.6.lower | 0.10655737704918032 | 0.10655737704918032 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.risk_0.6.upper | 0.2459016393442623 | 0.2459016393442623 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.7.point | 0.14788732394366197 | 0.14788732394366197 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.7.lower | 0.0957818830792977 | 0.0957818830792977 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.risk_0.7.upper | 0.2112676056338028 | 0.2112676056338028 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.8.point | 0.1419753086419753 | 0.1419753086419753 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.8.lower | 0.09202453987730061 | 0.09202453987730061 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.risk_0.8.upper | 0.19753086419753085 | 0.19753086419753085 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.9.point | 0.13186813186813187 | 0.13186813186813187 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.risk_0.9.lower | 0.08743169398907104 | 0.08743169398907104 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.risk_0.9.upper | 0.1858178706539361 | 0.1858178706539361 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.5.point | 0.0792079207920792 | 0.0792079207920792 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.5.lower | 0.014822364589400104 | 0.014822364589400104 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.5.upper | 0.11386138613861388 | 0.11386138613861388 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.6.point | 0.04341827625385489 | 0.04341827625385489 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.6.lower | 0.007547476059081307 | 0.007547476059081307 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.6.upper | 0.07774711897419251 | 0.07774711897419251 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.7.point | 0.019174452656533253 | 0.019174452656533253 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.7.lower | -0.004881257356504881 | -0.004881257356504881 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.7.upper | 0.04792821491656206 | 0.04792821491656206 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.8.point | 0.013262437354846585 | 0.013262437354846585 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.8.lower | -0.009053072996461214 | -0.009053072996461214 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.8.upper | 0.030558611416697218 | 0.030558611416697218 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.9.point | 0.0031552605810031553 | 0.0031552605810031553 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M4.D_0.9.lower | -0.009850958974477885 | -0.009850958974477885 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M4.D_0.9.upper | 0.016320313350016324 | 0.016320313350016324 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.039554363128503425 | 0.03955436312850342 | 6.938893903907228e-18 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.0205919389858565 | 0.020591938985856498 | 3.469446951953614e-18 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.06658511751467668 | 0.06658511751467668 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.aurc_trapezoid.point | 0.03923576691244617 | 0.03923576691244617 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.risk_0.5.upper | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.6.point | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.6.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.risk_0.6.upper | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.7.point | 0.07042253521126761 | 0.07042253521126761 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.7.lower | 0.02112676056338028 | 0.02112676056338028 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.risk_0.7.upper | 0.11888111888111888 | 0.11888111888111888 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.8.point | 0.08024691358024691 | 0.08024691358024691 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.8.lower | 0.043209876543209874 | 0.043209876543209874 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.risk_0.8.upper | 0.13416691605566353 | 0.13416691605566353 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.9.point | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.risk_0.9.lower | 0.06043956043956044 | 0.06043956043956044 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.risk_0.9.upper | 0.15934065934065933 | 0.15934065934065933 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.always_predict_risk | 0.12871287128712872 | 0.12871287128712872 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.n_errors | 26 | 26 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.5.point | -0.10891089108910891 | -0.10891089108910891 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.5.lower | -0.15346534653465346 | -0.15346534653465346 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.5.upper | -0.06435643564356436 | -0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.6.point | -0.10412270735270249 | -0.10412270735270249 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.6.lower | -0.1421872627506008 | -0.1421872627506008 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.6.upper | -0.05786398311962343 | -0.05786398311962343 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.7.point | -0.05829033607586111 | -0.05829033607586111 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.7.lower | -0.10054385720262167 | -0.10054385720262167 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.7.upper | -0.02593586688029585 | -0.02593586688029585 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.8.point | -0.04846595770688181 | -0.04846595770688181 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.8.lower | -0.07867265714301491 | -0.07867265714301491 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.8.upper | -0.01747758109144249 | -0.01747758109144249 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.9.point | -0.018822761397018828 | -0.018822761397018828 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M5.D_0.9.lower | -0.04437118635300749 | -0.04437118635300749 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M5.D_0.9.upper | 0.0008927122220418748 | 0.0008927122220418748 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.07828575073769241 | 0.07828575073769241 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.04248527472642301 | 0.04248527472642301 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.125052991917827 | 0.125052991917827 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.aurc_trapezoid.point | 0.07785687121607687 | 0.07785687121607689 | -1.3877787807814457e-17 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.5.point | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.5.lower | 0.009900990099009901 | 0.009900990099009901 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.risk_0.5.upper | 0.11893682225365325 | 0.11893682225365325 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.6.point | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.6.lower | 0.03278688524590164 | 0.03278688524590164 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.risk_0.6.upper | 0.13114754098360656 | 0.13114754098360656 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.7.point | 0.1056338028169014 | 0.1056338028169014 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.7.lower | 0.055934343434343434 | 0.055934343434343434 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.risk_0.7.upper | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.8.point | 0.12962962962962962 | 0.12962962962962962 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.8.lower | 0.07961258804817088 | 0.07961258804817088 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.9.point | 0.14835164835164835 | 0.14835164835164835 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.risk_0.9.lower | 0.0989010989010989 | 0.0989010989010989 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.risk_0.9.upper | 0.21428571428571427 | 0.21428571428571427 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.always_predict_risk | 0.17326732673267325 | 0.17326732673267325 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.n_errors | 35 | 35 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.5.point | -0.11386138613861385 | -0.11386138613861385 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.5.lower | -0.1683168316831683 | -0.1683168316831683 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.5.upper | -0.05940594059405942 | -0.05940594059405942 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.6.point | -0.09949683492939457 | -0.09949683492939457 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.6.lower | -0.14234702158740464 | -0.14234702158740464 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.6.upper | -0.0470662230157442 | -0.0470662230157442 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.7.point | -0.06763352391577185 | -0.06763352391577185 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.7.lower | -0.10989033627089685 | -0.10989033627089685 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.7.upper | -0.028762407490749115 | -0.028762407490749115 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.8.point | -0.04363769710304363 | -0.04363769710304363 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.8.lower | -0.07694811147781445 | -0.07694811147781445 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.8.upper | -0.012712382349346046 | -0.012712382349346046 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.9.point | -0.024915678381024903 | -0.024915678381024903 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.mechanisms.M6.D_0.9.lower | -0.04580567946904579 | -0.04580567946904579 | 0.0 | ok | .01  |
| conditions.drop_t2.mechanisms.M6.D_0.9.upper | 0.0020128386465020076 | 0.0020128386465020076 | 0.0 | ok | .01  |
| conditions.drop_t2.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.coverage | 0.995049504950495 | 0.995049504950495 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.abstention_rate | 0.6831683168316832 | 0.6831683168316832 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.full_count | 138 | 138 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.singleton_count | 64 | 64 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.singleton_true_label_fraction | 0.984375 | 0.984375 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.deviation.point | 0.04504950495049509 | 0.04504950495049509 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.05.deviation.lower | 0.020297029702970315 | 0.020297029702970315 | 0.0 | ok | .01  |
| conditions.drop_t2.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.drop_t2.conformal.0.05.deviation.half_width | 0.014851485148514865 | 0.014851485148514865 | 0.0 | ok | .01  |
| conditions.drop_t2.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.coverage | 0.9851485148514851 | 0.9851485148514851 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.abstention_rate | 0.36633663366336633 | 0.36633663366336633 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.full_count | 74 | 74 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.singleton_count | 128 | 128 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.singleton_true_label_fraction | 0.9765625 | 0.9765625 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.deviation.point | 0.08514851485148511 | 0.08514851485148511 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.1.deviation.lower | -0.06336633663366342 | -0.05841584158415847 | -0.004950495049504955 | ok | .01  |
| conditions.drop_t2.conformal.0.1.deviation.upper | 0.09999999999999998 | 0.09999999999999998 | 0.0 | ok | .01  |
| conditions.drop_t2.conformal.0.1.deviation.half_width | 0.0816831683168317 | 0.07920792079207922 | 0.0024752475247524774 | ok | .01  |
| conditions.drop_t2.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.coverage | 0.7524752475247525 | 0.7524752475247525 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.abstention_rate | 0.17326732673267325 | 0.17326732673267325 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.empty_count | 35 | 35 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.singleton_count | 167 | 167 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.singleton_true_label_fraction | 0.9101796407185628 | 0.9101796407185628 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.deviation.point | -0.04752475247524757 | -0.04752475247524757 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.conformal.0.2.deviation.lower | -0.33960396039603963 | -0.3346534653465347 | -0.004950495049504955 | ok | .01  |
| conditions.drop_t2.conformal.0.2.deviation.upper | 0.09108910891089106 | 0.09603960396039601 | -0.004950495049504955 | ok | .01  |
| conditions.drop_t2.conformal.0.2.deviation.half_width | 0.21534653465346534 | 0.21534653465346534 | 0.0 | ok | .01  |
| conditions.drop_t2.oracle_aurc | 0.016567003234976965 | 0.008981736521931584 | 0.007585266713045382 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.drop_t2.c5_adjacent.0.5-0.6.point | -0.004788183736406427 | -0.004788183736406427 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c5_adjacent.0.5-0.6.lower | -0.041060426117776196 | -0.041060426117776196 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.5-0.6.upper | 0.008525736019180025 | 0.008525736019180025 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.6-0.7.point | -0.04583237127684138 | -0.04583237127684138 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c5_adjacent.0.6-0.7.lower | -0.07644880792150849 | -0.07644880792150849 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.6-0.7.upper | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.7-0.8.point | -0.0098243783689793 | -0.0098243783689793 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c5_adjacent.0.7-0.8.lower | -0.045905059989567024 | -0.045905059989567024 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.7-0.8.upper | 0.0065744417165828645 | 0.0065744417165828645 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.8-0.9.point | -0.02964319630986298 | -0.02964319630986298 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c5_adjacent.0.8-0.9.lower | -0.05467636607857333 | -0.05467636607857333 | 0.0 | ok | .01  |
| conditions.drop_t2.c5_adjacent.0.8-0.9.upper | -0.00171733208618456 | -0.00171733208618456 | 0.0 | ok | .01  |
| conditions.drop_t2.c6_enrichment.0.5.observed | 0.1089108910891089 | 0.1089108910891089 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.5.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.5.rejected_but_correct_rate | 0.7623762376237624 | 0.7623762376237624 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.5.p_adjusted | 5/20002 | 4999500049995001/30000000000000000000 | 24999999999999994999/300030000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.6.observed | 0.15878712871287126 | 0.15878712871287126 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.6.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.6.rejected_but_correct_rate | 0.7125 | 0.7125 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.6.p_adjusted | 5/20002 | 4999500049995001/30000000000000000000 | 24999999999999994999/300030000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.7.observed | 0.13795379537953795 | 0.13795379537953795 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.7.p_value | 8/10001 | 0.00039996000399960006 | 199999999999999989997/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.7.rejected_but_correct_rate | 0.7333333333333334 | 0.7333333333333333 | 1.1102230246251565e-16 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.7.p_adjusted | 10/10001 | 19998000199980003/40000000000000000000 | 199999999999999989997/400040000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.8.observed | 0.1962871287128713 | 0.1962871287128713 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.8.p_value | 2/10001 | 9.999000099990002e-05 | 49999999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.8.rejected_but_correct_rate | 0.675 | 0.675 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.8.p_adjusted | 10/30003 | 4999500049995001/30000000000000000000 | 49999999999999994999/300030000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.9.observed | 0.17128712871287127 | 0.17128712871287127 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.9.p_value | 281/10001 | 0.027497250274972504 | 749999999999998437/1250125000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_t2.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.9.rejected_but_correct_rate | 0.7 | 0.7 | 0.0 | ok | 1e-9  |
| conditions.drop_t2.c6_enrichment.0.9.p_adjusted | 281/10001 | 3437156284371563/125000000000000000 | 749999999999998437/1250125000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.n_errors | 41 | 41 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.always_predict_risk | 0.20297029702970298 | 0.20297029702970298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.10108680129700627 | 0.10108680129700626 | 1.3877787807814457e-17 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.06179698654418596 | 0.06179698654418596 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.15156382922073097 | 0.15156382922073097 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.aurc_trapezoid.point | 0.1005843995716852 | 0.1005843995716852 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.5.point | 0.09900990099009901 | 0.09900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.5.lower | 0.049019607843137254 | 0.049019607843137254 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.risk_0.5.upper | 0.16831683168316833 | 0.16831683168316833 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.6.point | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.6.lower | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.risk_0.6.upper | 0.17886178861788618 | 0.17886178861788618 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.7.point | 0.14788732394366197 | 0.14788732394366197 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.7.lower | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.risk_0.7.upper | 0.20422535211267606 | 0.20422535211267606 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.8.point | 0.16049382716049382 | 0.16049382716049382 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.8.lower | 0.10427857997905132 | 0.10427857997905132 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.risk_0.8.upper | 0.21604938271604937 | 0.21604938271604937 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.9.point | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.risk_0.9.lower | 0.12087912087912088 | 0.12087912087912088 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.risk_0.9.upper | 0.23626373626373626 | 0.23626373626373626 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.always_predict_risk | 0.20297029702970298 | 0.20297029702970298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.n_errors | 41 | 41 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.5.point | -0.10396039603960397 | -0.10396039603960397 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.5.lower | -0.1584158415841584 | -0.1584158415841584 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.5.upper | -0.044554455445544566 | -0.044554455445544566 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.6.point | -0.08821619866904724 | -0.08821619866904724 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.6.lower | -0.13602948259640038 | -0.13602948259640038 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.6.upper | -0.043516023006319675 | -0.043516023006319675 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.7.point | -0.055082973086041015 | -0.055082973086041015 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.7.lower | -0.09690910992507701 | -0.09690910992507701 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.7.upper | -0.01888705528190962 | -0.01888705528190962 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.8.point | -0.042476469869209166 | -0.042476469869209166 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.8.lower | -0.07829269038014912 | -0.07829269038014912 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.8.upper | -0.01278624794994837 | -0.01278624794994837 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.9.point | -0.02165161571102167 | -0.02165161571102167 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M1.D_0.9.lower | -0.05048575227726341 | -0.05048575227726341 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M1.D_0.9.upper | -0.003349699724070786 | -0.003349699724070786 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.10108680129700627 | 0.10108680129700626 | 1.3877787807814457e-17 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.06179698654418596 | 0.06179698654418596 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.15156382922073097 | 0.15156382922073097 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.aurc_trapezoid.point | 0.1005843995716852 | 0.1005843995716852 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.5.point | 0.09900990099009901 | 0.09900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.5.lower | 0.049019607843137254 | 0.049019607843137254 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.risk_0.5.upper | 0.16831683168316833 | 0.16831683168316833 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.6.point | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.6.lower | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.risk_0.6.upper | 0.17886178861788618 | 0.17886178861788618 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.7.point | 0.14788732394366197 | 0.14788732394366197 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.7.lower | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.risk_0.7.upper | 0.20422535211267606 | 0.20422535211267606 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.8.point | 0.16049382716049382 | 0.16049382716049382 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.8.lower | 0.10427857997905132 | 0.10427857997905132 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.risk_0.8.upper | 0.21604938271604937 | 0.21604938271604937 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.9.point | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.risk_0.9.lower | 0.12087912087912088 | 0.12087912087912088 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.risk_0.9.upper | 0.23626373626373626 | 0.23626373626373626 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.always_predict_risk | 0.20297029702970298 | 0.20297029702970298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.n_errors | 41 | 41 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.5.point | -0.10396039603960397 | -0.10396039603960397 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.5.lower | -0.1584158415841584 | -0.1584158415841584 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.5.upper | -0.044554455445544566 | -0.044554455445544566 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.6.point | -0.08821619866904724 | -0.08821619866904724 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.6.lower | -0.13602948259640038 | -0.13602948259640038 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.6.upper | -0.043516023006319675 | -0.043516023006319675 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.7.point | -0.055082973086041015 | -0.055082973086041015 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.7.lower | -0.09690910992507701 | -0.09690910992507701 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.7.upper | -0.01888705528190962 | -0.01888705528190962 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.8.point | -0.042476469869209166 | -0.042476469869209166 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.8.lower | -0.07829269038014912 | -0.07829269038014912 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.8.upper | -0.01278624794994837 | -0.01278624794994837 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.9.point | -0.02165161571102167 | -0.02165161571102167 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M2.D_0.9.lower | -0.05048575227726341 | -0.05048575227726341 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M2.D_0.9.upper | -0.003349699724070786 | -0.003349699724070786 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.10479657248533696 | 0.10479657248533696 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.06346510001499094 | 0.06346510001499094 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.15767116957491453 | 0.15767116957491456 | -2.7755575615628914e-17 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.aurc_trapezoid.point | 0.1042941707600159 | 0.10429417076001592 | -1.3877787807814457e-17 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.5.point | 0.09900990099009901 | 0.09900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.5.lower | 0.049019607843137254 | 0.049019607843137254 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.risk_0.5.upper | 0.16831683168316833 | 0.16831683168316833 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.6.point | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.6.lower | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.risk_0.6.upper | 0.17886178861788618 | 0.17886178861788618 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.7.point | 0.14084507042253522 | 0.14084507042253522 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.7.lower | 0.08391608391608392 | 0.08391608391608392 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.risk_0.7.upper | 0.19718309859154928 | 0.19718309859154928 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.8.point | 0.15432098765432098 | 0.15432098765432098 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.8.lower | 0.10493827160493827 | 0.10493827160493827 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.risk_0.8.upper | 0.21821507760532133 | 0.21821507760532133 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.9.point | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.risk_0.9.lower | 0.12087912087912088 | 0.12087912087912088 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.risk_0.9.upper | 0.23626373626373626 | 0.23626373626373626 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.always_predict_risk | 0.20297029702970298 | 0.20297029702970298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.n_errors | 41 | 41 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.5.point | -0.10396039603960397 | -0.10396039603960397 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.5.lower | -0.15346534653465346 | -0.15346534653465346 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.5.upper | -0.044554455445544566 | -0.044554455445544566 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.6.point | -0.08821619866904724 | -0.08821619866904724 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.6.lower | -0.13547996642926988 | -0.13547996642926988 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.6.upper | -0.04211233565979551 | -0.04211233565979551 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.7.point | -0.062125226607167766 | -0.062125226607167766 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.7.lower | -0.10591322810504238 | -0.10591322810504238 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.7.upper | -0.026401478175986634 | -0.026401478175986634 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.8.point | -0.048649309375382005 | -0.048649309375382005 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.8.lower | -0.07584800146681335 | -0.07584800146681335 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.8.upper | -0.011814371621211212 | -0.011814371621211212 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.9.point | -0.02165161571102167 | -0.02165161571102167 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M3.D_0.9.lower | -0.046895060385159386 | -0.046895060385159386 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M3.D_0.9.upper | -0.0029376564030029195 | -0.0029376564030029195 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.1748448822225951 | 0.1748448822225951 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.11173430354449505 | 0.11173430354449507 | -1.3877787807814457e-17 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.2488584019266819 | 0.24885840192668193 | -2.7755575615628914e-17 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.aurc_trapezoid.point | 0.1743669878985092 | 0.1743669878985092 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.5.point | 0.1782178217821782 | 0.1782178217821782 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.5.lower | 0.09900990099009901 | 0.09900990099009901 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.risk_0.5.upper | 0.2549019607843137 | 0.2549019607843137 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.6.point | 0.19672131147540983 | 0.19672131147540983 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.6.lower | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.risk_0.6.upper | 0.26229508196721313 | 0.26229508196721313 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.7.point | 0.18309859154929578 | 0.18309859154929578 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.7.lower | 0.11971830985915492 | 0.11971830985915492 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.risk_0.7.upper | 0.2517482517482518 | 0.2517482517482518 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.8.point | 0.18518518518518517 | 0.18518518518518517 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.8.lower | 0.12883435582822086 | 0.12883435582822086 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.risk_0.8.upper | 0.25308641975308643 | 0.25308641975308643 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.9.point | 0.19230769230769232 | 0.19230769230769232 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.risk_0.9.lower | 0.13736263736263737 | 0.13736263736263737 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.risk_0.9.upper | 0.25274725274725274 | 0.25274725274725274 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.always_predict_risk | 0.19306930693069307 | 0.19306930693069307 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.n_errors | 39 | 39 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.5.point | -0.014851485148514865 | -0.014851485148514865 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.5.lower | -0.07428169287516988 | -0.07428169287516988 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.5.upper | 0.03960396039603961 | 0.03960396039603961 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.6.point | 0.003652004544716758 | 0.003652004544716758 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.6.lower | -0.04878482493939506 | -0.04878482493939506 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.6.upper | 0.04138938484012336 | 0.04138938484012336 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.7.point | -0.009970715381397294 | -0.009970715381397294 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.7.lower | -0.0522262441154266 | -0.0522262441154266 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.7.upper | 0.028657091061218803 | 0.028657091061218803 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.8.point | -0.0078841217455079 | -0.0078841217455079 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.8.lower | -0.039972191663610816 | -0.039972191663610816 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.8.upper | 0.02786945361202786 | 0.02786945361202786 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.9.point | -0.0007616146230007559 | -0.0007616146230007559 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M4.D_0.9.lower | -0.0200256413229145 | -0.0200256413229145 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M4.D_0.9.upper | 0.01735529322162986 | 0.01735529322162986 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.10108680129700627 | 0.10108680129700626 | 1.3877787807814457e-17 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.06179698654418596 | 0.06179698654418596 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.15156382922073097 | 0.15156382922073097 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.aurc_trapezoid.point | 0.1005843995716852 | 0.1005843995716852 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.5.point | 0.09900990099009901 | 0.09900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.5.lower | 0.049019607843137254 | 0.049019607843137254 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.risk_0.5.upper | 0.16831683168316833 | 0.16831683168316833 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.6.point | 0.11475409836065574 | 0.11475409836065574 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.6.lower | 0.05737704918032787 | 0.05737704918032787 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.risk_0.6.upper | 0.17886178861788618 | 0.17886178861788618 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.7.point | 0.14788732394366197 | 0.14788732394366197 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.7.lower | 0.08450704225352113 | 0.08450704225352113 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.risk_0.7.upper | 0.20422535211267606 | 0.20422535211267606 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.8.point | 0.16049382716049382 | 0.16049382716049382 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.8.lower | 0.10427857997905132 | 0.10427857997905132 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.risk_0.8.upper | 0.21604938271604937 | 0.21604938271604937 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.9.point | 0.1813186813186813 | 0.1813186813186813 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.risk_0.9.lower | 0.12087912087912088 | 0.12087912087912088 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.risk_0.9.upper | 0.23626373626373626 | 0.23626373626373626 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.always_predict_risk | 0.20297029702970298 | 0.20297029702970298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.n_errors | 41 | 41 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.5.point | -0.10396039603960397 | -0.10396039603960397 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.5.lower | -0.1584158415841584 | -0.1584158415841584 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.5.upper | -0.044554455445544566 | -0.044554455445544566 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.6.point | -0.08821619866904724 | -0.08821619866904724 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.6.lower | -0.13602948259640038 | -0.13602948259640038 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.6.upper | -0.043516023006319675 | -0.043516023006319675 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.7.point | -0.055082973086041015 | -0.055082973086041015 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.7.lower | -0.09690910992507701 | -0.09690910992507701 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.7.upper | -0.01888705528190962 | -0.01888705528190962 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.8.point | -0.042476469869209166 | -0.042476469869209166 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.8.lower | -0.07829269038014912 | -0.07829269038014912 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.8.upper | -0.01278624794994837 | -0.01278624794994837 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.9.point | -0.02165161571102167 | -0.02165161571102167 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M5.D_0.9.lower | -0.05048575227726341 | -0.05048575227726341 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M5.D_0.9.upper | -0.003349699724070786 | -0.003349699724070786 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.25511398239206523 | 0.25511398239206523 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.19327271421933762 | 0.19327271421933762 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.3279546664452384 | 0.32795466644523835 | 5.551115123125783e-17 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.aurc_trapezoid.point | 0.2540969252408055 | 0.2540969252408055 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.5.point | 0.27722772277227725 | 0.27722772277227725 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.5.lower | 0.18811881188118812 | 0.18811881188118812 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.risk_0.5.upper | 0.38613861386138615 | 0.38613861386138615 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.6.point | 0.3442622950819672 | 0.3442622950819672 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.6.lower | 0.2540983606557377 | 0.2540983606557377 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.risk_0.6.upper | 0.4355723839496455 | 0.4355723839496455 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.7.point | 0.36619718309859156 | 0.36619718309859156 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.7.lower | 0.293655303030303 | 0.293655303030303 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.risk_0.7.upper | 0.4507042253521127 | 0.4507042253521127 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.8.point | 0.38271604938271603 | 0.38271604938271603 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.8.lower | 0.3067484662576687 | 0.3067484662576687 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.risk_0.8.upper | 0.4573872138261256 | 0.4573872138261256 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.9.point | 0.38461538461538464 | 0.38461538461538464 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.risk_0.9.lower | 0.31868131868131866 | 0.31868131868131866 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.risk_0.9.upper | 0.45901639344262296 | 0.45901639344262296 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.always_predict_risk | 0.41089108910891087 | 0.41089108910891087 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.n_errors | 83 | 83 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.5.point | -0.13366336633663362 | -0.13366336633663362 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.5.lower | -0.198019801980198 | -0.198019801980198 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.5.upper | -0.0530892059794215 | -0.0530892059794215 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.6.point | -0.06662879402694366 | -0.06662879402694366 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.6.lower | -0.1260398068495374 | -0.1260398068495374 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.6.upper | -0.007385164745982775 | -0.007385164745982775 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.7.point | -0.044693906010319306 | -0.044693906010319306 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.7.lower | -0.08618044903081862 | -0.08618044903081862 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.7.upper | 0.004927200466525479 | 0.004927200466525479 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.8.point | -0.02817503972619484 | -0.02817503972619484 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.8.lower | -0.06649706637330398 | -0.06649706637330398 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.8.upper | 0.008235892607665683 | 0.008235892607665683 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.9.point | -0.02627570449352623 | -0.02627570449352623 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.mechanisms.M6.D_0.9.lower | -0.04439936812004181 | -0.04439936812004181 | 0.0 | ok | .01  |
| conditions.drop_flair.mechanisms.M6.D_0.9.upper | 0.0011976757521311966 | 0.0011976757521311966 | 0.0 | ok | .01  |
| conditions.drop_flair.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.coverage | 0.9554455445544554 | 0.9554455445544554 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.abstention_rate | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.full_count | 122 | 122 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.singleton_count | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.singleton_true_label_fraction | 0.8875 | 0.8875 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.deviation.point | 0.00544554455445545 | 0.00544554455445545 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.05.deviation.lower | -0.07871287128712867 | -0.07871287128712867 | 0.0 | ok | .01  |
| conditions.drop_flair.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.drop_flair.conformal.0.05.deviation.half_width | 0.06435643564356436 | 0.06435643564356436 | 0.0 | ok | .01  |
| conditions.drop_flair.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.coverage | 0.8861386138613861 | 0.8861386138613861 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.abstention_rate | 0.2524752475247525 | 0.2524752475247525 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.full_count | 51 | 51 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.singleton_count | 151 | 151 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.singleton_true_label_fraction | 0.847682119205298 | 0.847682119205298 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.deviation.point | -0.013861386138613874 | -0.013861386138613874 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.1.deviation.lower | -0.12772277227722773 | -0.11782178217821782 | -0.00990099009900991 | ok | .01  |
| conditions.drop_flair.conformal.0.1.deviation.upper | 0.0653465346534653 | 0.06039603960396034 | 0.004950495049504955 | ok | .01  |
| conditions.drop_flair.conformal.0.1.deviation.half_width | 0.09653465346534651 | 0.08910891089108908 | 0.007425742574257432 | ok | .01  |
| conditions.drop_flair.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.coverage | 0.7079207920792079 | 0.7079207920792079 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.abstention_rate | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.empty_count | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.singleton_count | 171 | 171 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.singleton_true_label_fraction | 0.8362573099415205 | 0.8362573099415205 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.deviation.point | -0.09207920792079216 | -0.09207920792079216 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.conformal.0.2.deviation.lower | -0.2950495049504951 | -0.2851485148514852 | -0.00990099009900991 | ok | .01  |
| conditions.drop_flair.conformal.0.2.deviation.upper | 0.036633663366336555 | 0.036633663366336555 | 0.0 | ok | .01  |
| conditions.drop_flair.conformal.0.2.deviation.half_width | 0.16584158415841582 | 0.16089108910891087 | 0.004950495049504955 | ok | .01  |
| conditions.drop_flair.oracle_aurc | 0.04119694147632585 | 0.022654949702475058 | 0.01854199177385079 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.drop_flair.c5_adjacent.0.5-0.6.point | -0.015744197370556726 | -0.015744197370556726 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c5_adjacent.0.5-0.6.lower | -0.05056780917995838 | -0.05056780917995838 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.5-0.6.upper | 0.019286403085824494 | 0.019286403085824494 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.6-0.7.point | -0.03313322558300623 | -0.03313322558300623 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c5_adjacent.0.6-0.7.lower | -0.06724216265333939 | -0.06724216265333939 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.6-0.7.upper | 0.0020780420226275687 | 0.0020780420226275687 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.7-0.8.point | -0.01260650321683185 | -0.01260650321683185 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c5_adjacent.0.7-0.8.lower | -0.04407770980540933 | -0.04407770980540933 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.7-0.8.upper | 0.011997913406364108 | 0.011997913406364108 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.8-0.9.point | -0.020824854158187495 | -0.020824854158187495 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c5_adjacent.0.8-0.9.lower | -0.045072561750123856 | -0.045072561750123856 | 0.0 | ok | .01  |
| conditions.drop_flair.c5_adjacent.0.8-0.9.upper | 0.0056688859546857005 | 0.0056688859546857005 | 0.0 | ok | .01  |
| conditions.drop_flair.c6_enrichment.0.5.observed | 0.10396039603960394 | 0.10396039603960394 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.5.p_value | 4/10001 | 0.00029997000299970003 | 99999999999999999997/1000100000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.5.rejected_but_correct_rate | 0.693069306930693 | 0.693069306930693 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.5.p_adjusted | 10/10001 | 19998000199980003/20000000000000000000 | -10003/200020000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.6.observed | 0.13452970297029704 | 0.13452970297029704 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.6.p_value | 2/10001 | 0.00039996000399960006 | -100000000000000010003/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.6.rejected_but_correct_rate | 0.6625 | 0.6625 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.6.p_adjusted | 10/10001 | 19998000199980003/20000000000000000000 | -10003/200020000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.7.observed | 0.13036303630363033 | 0.13036303630363033 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.7.p_value | 27/10001 | 0.0028997100289971 | -19999999999999971/100010000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.7.rejected_but_correct_rate | 0.6666666666666667 | 0.6666666666666666 | 1.1102230246251565e-16 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.7.p_adjusted | 45/10001 | 7749225077492251/2000000000000000000 | 12499999999999997749/20002000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.8.observed | 0.17202970297029702 | 0.17202970297029702 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.8.p_value | 41/10001 | 0.0030996900309969004 | 24999999999999997749/25002500000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.8.rejected_but_correct_rate | 0.625 | 0.625 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.8.p_adjusted | 205/40004 | 7749225077492251/2000000000000000000 | 24999999999999997749/20002000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.9.observed | 0.19702970297029704 | 0.19702970297029704 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.9.p_value | 276/10001 | 0.026697330266973303 | 8999999999999996697/10001000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.drop_flair.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.9.rejected_but_correct_rate | 0.6 | 0.6 | 0.0 | ok | 1e-9  |
| conditions.drop_flair.c6_enrichment.0.9.p_adjusted | 276/10001 | 26697330266973303/1000000000000000000 | 8999999999999996697/10001000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.n | 202 | 202 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.n_errors | 42 | 42 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.always_predict_risk | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_mean_over_cutoffs.point | 0.06390654132817762 | 0.06390654132817762 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_mean_over_cutoffs.lower | 0.037411736828682096 | 0.037411736828682096 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_mean_over_cutoffs.upper | 0.09945206777804896 | 0.09945206777804896 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_trapezoid.point | 0.06339188590223899 | 0.06339188590223899 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.5.upper | 0.09711117456691401 | 0.09711117456691401 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.6.upper | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.7.point | 0.09859154929577464 | 0.09859154929577464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.7.lower | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.7.upper | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.8.point | 0.12962962962962962 | 0.12962962962962962 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.8.lower | 0.07407407407407407 | 0.07407407407407407 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.9.point | 0.16483516483516483 | 0.16483516483516483 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.9.lower | 0.1092896174863388 | 0.1092896174863388 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.risk_0.9.upper | 0.2185792349726776 | 0.2185792349726776 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.always_predict_risk | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.n_errors | 42 | 42 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.5.point | -0.18811881188118812 | -0.18811881188118812 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.5.lower | -0.22772277227722773 | -0.22772277227722773 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.5.upper | -0.11957872257814023 | -0.11957872257814023 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.6.point | -0.14234702158740464 | -0.14234702158740464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.6.lower | -0.1870723657731627 | -0.1870723657731627 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.6.upper | -0.09282018215815996 | -0.09282018215815996 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.7.point | -0.10932924278343327 | -0.10932924278343327 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.7.lower | -0.15082101520011157 | -0.15082101520011157 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.7.upper | -0.06719219457156984 | -0.06719219457156984 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.8.point | -0.07829116244957829 | -0.07829116244957829 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.8.lower | -0.10677331622051094 | -0.10677331622051094 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.8.upper | -0.04356933152664864 | -0.04356933152664864 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.9.point | -0.04308562724404308 | -0.04308562724404308 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.9.lower | -0.06899276466108151 | -0.06899276466108151 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M1.D_0.9.upper | -0.021053204221521044 | -0.021053204221521044 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_mean_over_cutoffs.point | 0.06390654132817762 | 0.06390654132817762 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_mean_over_cutoffs.lower | 0.037411736828682096 | 0.037411736828682096 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_mean_over_cutoffs.upper | 0.09945206777804896 | 0.09945206777804896 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_trapezoid.point | 0.06339188590223899 | 0.06339188590223899 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.5.upper | 0.09711117456691401 | 0.09711117456691401 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.6.upper | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.7.point | 0.09859154929577464 | 0.09859154929577464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.7.lower | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.7.upper | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.8.point | 0.12962962962962962 | 0.12962962962962962 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.8.lower | 0.07407407407407407 | 0.07407407407407407 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.9.point | 0.16483516483516483 | 0.16483516483516483 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.9.lower | 0.1092896174863388 | 0.1092896174863388 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.risk_0.9.upper | 0.2185792349726776 | 0.2185792349726776 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.always_predict_risk | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.n_errors | 42 | 42 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.5.point | -0.18811881188118812 | -0.18811881188118812 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.5.lower | -0.22772277227722773 | -0.22772277227722773 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.5.upper | -0.11957872257814023 | -0.11957872257814023 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.6.point | -0.14234702158740464 | -0.14234702158740464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.6.lower | -0.1870723657731627 | -0.1870723657731627 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.6.upper | -0.09282018215815996 | -0.09282018215815996 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.7.point | -0.10932924278343327 | -0.10932924278343327 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.7.lower | -0.15082101520011157 | -0.15082101520011157 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.7.upper | -0.06719219457156984 | -0.06719219457156984 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.8.point | -0.07829116244957829 | -0.07829116244957829 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.8.lower | -0.10677331622051094 | -0.10677331622051094 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.8.upper | -0.04356933152664864 | -0.04356933152664864 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.9.point | -0.04308562724404308 | -0.04308562724404308 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.9.lower | -0.06899276466108151 | -0.06899276466108151 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M2.D_0.9.upper | -0.021053204221521044 | -0.021053204221521044 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_mean_over_cutoffs.point | 0.06499735995899784 | 0.06499735995899786 | -1.3877787807814457e-17 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_mean_over_cutoffs.lower | 0.03826865356156274 | 0.03826865356156274 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_mean_over_cutoffs.upper | 0.10152405237230662 | 0.10152405237230662 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_trapezoid.point | 0.06448270453305922 | 0.06448270453305922 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.5.point | 0.039603960396039604 | 0.039603960396039604 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.5.upper | 0.10384914819563983 | 0.10384914819563983 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.6.point | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.6.upper | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.7.point | 0.09154929577464789 | 0.09154929577464789 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.7.lower | 0.04225352112676056 | 0.04225352112676056 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.7.upper | 0.14788732394366197 | 0.14788732394366197 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.8.point | 0.12345679012345678 | 0.12345679012345678 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.8.lower | 0.07360840939697741 | 0.07360840939697741 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.9.point | 0.15934065934065933 | 0.15934065934065933 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.9.lower | 0.1092896174863388 | 0.1092896174863388 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.risk_0.9.upper | 0.21978021978021978 | 0.21978021978021978 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.always_predict_risk | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.n_errors | 42 | 42 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.5.point | -0.1683168316831683 | -0.1683168316831683 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.5.lower | -0.21782178217821782 | -0.21782178217821782 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.5.upper | -0.10997379149679676 | -0.10997379149679676 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.6.point | -0.13415030027592922 | -0.13415030027592922 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.6.lower | -0.18552537730782273 | -0.18552537730782273 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.6.upper | -0.0897581561434832 | -0.0897581561434832 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.7.point | -0.11637149630456002 | -0.11637149630456002 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.7.lower | -0.1588375820247247 | -0.1588375820247247 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.7.upper | -0.07536522883057535 | -0.07536522883057535 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.8.point | -0.08446400195575113 | -0.08446400195575113 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.8.lower | -0.11018973148166895 | -0.11018973148166895 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.8.upper | -0.04464556885136367 | -0.04464556885136367 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.9.point | -0.04858013273854858 | -0.04858013273854858 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.9.lower | -0.07110216516157111 | -0.07110216516157111 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M3.D_0.9.upper | -0.019416490829410816 | -0.019416490829410816 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_mean_over_cutoffs.point | 0.26965509186417735 | 0.26965509186417735 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_mean_over_cutoffs.lower | 0.18180293842488787 | 0.18180293842488787 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_mean_over_cutoffs.upper | 0.36519231578100464 | 0.3651923157810047 | -5.551115123125783e-17 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_trapezoid.point | 0.26927522714503216 | 0.2692752271450322 | -5.551115123125783e-17 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.5.point | 0.24752475247524752 | 0.24752475247524752 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.5.lower | 0.16666666666666666 | 0.16666666666666666 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.5.upper | 0.3465346534653465 | 0.3465346534653465 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.6.point | 0.21311475409836064 | 0.21311475409836064 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.6.lower | 0.13934426229508196 | 0.13934426229508196 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.6.upper | 0.29508196721311475 | 0.29508196721311475 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.7.point | 0.19014084507042253 | 0.19014084507042253 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.7.lower | 0.1267605633802817 | 0.1267605633802817 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.7.upper | 0.25874125874125875 | 0.25874125874125875 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.8.point | 0.1728395061728395 | 0.1728395061728395 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.8.lower | 0.11728395061728394 | 0.11728395061728394 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.8.upper | 0.2345679012345679 | 0.2345679012345679 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.9.point | 0.15934065934065933 | 0.15934065934065933 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.9.lower | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.risk_0.9.upper | 0.21428571428571427 | 0.21428571428571427 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.always_predict_risk | 0.15346534653465346 | 0.15346534653465346 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.n_errors | 31 | 31 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.5.point | 0.09405940594059406 | 0.09405940594059406 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.5.lower | 0.04455445544554455 | 0.04455445544554455 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.5.upper | 0.14511745292176276 | 0.14511745292176276 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.6.point | 0.05964940756370718 | 0.05964940756370718 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.6.lower | 0.02138414569230331 | 0.02138414569230331 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.6.upper | 0.09568251907157929 | 0.09568251907157929 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.7.point | 0.03667549853576907 | 0.03667549853576907 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.7.lower | 0.006410779722338426 | 0.006410779722338426 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.7.upper | 0.06178182959140984 | 0.06178182959140984 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.8.point | 0.019374159638186034 | 0.019374159638186034 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.8.lower | -0.0024600619571159554 | -0.0024600619571159554 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.8.upper | 0.039115022613372435 | 0.039115022613372435 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.9.point | 0.005875312806005867 | 0.005875312806005867 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.9.lower | -0.009525005645610889 | -0.009525005645610889 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M4.D_0.9.upper | 0.018496355130018488 | 0.018496355130018488 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_mean_over_cutoffs.point | 0.06390654132817762 | 0.06390654132817762 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_mean_over_cutoffs.lower | 0.037411736828682096 | 0.037411736828682096 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_mean_over_cutoffs.upper | 0.09945206777804896 | 0.09945206777804896 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_trapezoid.point | 0.06339188590223899 | 0.06339188590223899 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.5.point | 0.019801980198019802 | 0.019801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.5.lower | 0.0 | 0.0 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.5.upper | 0.09711117456691401 | 0.09711117456691401 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.6.point | 0.06557377049180328 | 0.06557377049180328 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.6.lower | 0.02459016393442623 | 0.02459016393442623 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.6.upper | 0.12295081967213115 | 0.12295081967213115 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.7.point | 0.09859154929577464 | 0.09859154929577464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.7.lower | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.7.upper | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.8.point | 0.12962962962962962 | 0.12962962962962962 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.8.lower | 0.07407407407407407 | 0.07407407407407407 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.9.point | 0.16483516483516483 | 0.16483516483516483 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.9.lower | 0.1092896174863388 | 0.1092896174863388 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.risk_0.9.upper | 0.2185792349726776 | 0.2185792349726776 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.always_predict_risk | 0.2079207920792079 | 0.2079207920792079 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.n_errors | 42 | 42 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.5.point | -0.18811881188118812 | -0.18811881188118812 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.5.lower | -0.22772277227722773 | -0.22772277227722773 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.5.upper | -0.11957872257814023 | -0.11957872257814023 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.6.point | -0.14234702158740464 | -0.14234702158740464 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.6.lower | -0.1870723657731627 | -0.1870723657731627 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.6.upper | -0.09282018215815996 | -0.09282018215815996 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.7.point | -0.10932924278343327 | -0.10932924278343327 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.7.lower | -0.15082101520011157 | -0.15082101520011157 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.7.upper | -0.06719219457156984 | -0.06719219457156984 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.8.point | -0.07829116244957829 | -0.07829116244957829 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.8.lower | -0.10677331622051094 | -0.10677331622051094 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.8.upper | -0.04356933152664864 | -0.04356933152664864 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.9.point | -0.04308562724404308 | -0.04308562724404308 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.9.lower | -0.06899276466108151 | -0.06899276466108151 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M5.D_0.9.upper | -0.021053204221521044 | -0.021053204221521044 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_mean_over_cutoffs.point | 0.08306373388792017 | 0.08306373388792017 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_mean_over_cutoffs.lower | 0.04491804764823012 | 0.04491804764823012 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_mean_over_cutoffs.upper | 0.13424745391987505 | 0.13424745391987508 | -2.7755575615628914e-17 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_trapezoid.point | 0.08257358586321671 | 0.08257358586321671 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.5.point | 0.0594059405940594 | 0.0594059405940594 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.5.lower | 0.019417475728155338 | 0.019417475728155338 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.5.upper | 0.1188118811881188 | 0.1188118811881188 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.coverage_0.5 | 0.5 | 0.5 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.6.point | 0.07377049180327869 | 0.07377049180327869 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.6.lower | 0.032520325203252036 | 0.032520325203252036 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.6.upper | 0.13114754098360656 | 0.13114754098360656 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.coverage_0.6 | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.7.point | 0.1056338028169014 | 0.1056338028169014 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.7.lower | 0.04929577464788732 | 0.04929577464788732 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.7.upper | 0.1619718309859155 | 0.1619718309859155 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.coverage_0.7 | 0.7029702970297029 | 0.7029702970297029 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.8.point | 0.13580246913580246 | 0.13580246913580246 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.8.lower | 0.08023460577141558 | 0.08023460577141558 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.8.upper | 0.19135802469135801 | 0.19135802469135801 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.coverage_0.8 | 0.801980198019802 | 0.801980198019802 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.9.point | 0.15384615384615385 | 0.15384615384615385 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.9.lower | 0.10989010989010989 | 0.10989010989010989 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.risk_0.9.upper | 0.22407449108268762 | 0.22407449108268762 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.coverage_0.9 | 0.900990099009901 | 0.900990099009901 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.always_predict_risk | 0.19801980198019803 | 0.19801980198019803 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.n_errors | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.5.point | -0.13861386138613863 | -0.13861386138613863 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.5.lower | -0.18841244418559502 | -0.18841244418559502 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.5.upper | -0.08415841584158418 | -0.08415841584158418 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.6.point | -0.12424931017691934 | -0.12424931017691934 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.6.lower | -0.17172689498458044 | -0.17172689498458044 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.6.upper | -0.0725267648716091 | -0.0725267648716091 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.7.point | -0.09238599916329662 | -0.09238599916329662 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.7.lower | -0.13826523497420165 | -0.13826523497420165 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.7.upper | -0.05354830986890671 | -0.05354830986890671 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.8.point | -0.06221733284439557 | -0.06221733284439557 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.8.lower | -0.09770394217335845 | -0.09770394217335845 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.8.upper | -0.03193855769353356 | -0.03193855769353356 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.9.point | -0.044173648134044174 | -0.044173648134044174 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.9.lower | -0.05957050375367206 | -0.05957050375367206 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.mechanisms.M6.D_0.9.upper | -0.01226758901834587 | -0.01226758901834587 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.05.quantile | 0.777272037215785 | 0.7772720380564715 | -8.406865203980374e-10 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.coverage | 0.995049504950495 | 0.995049504950495 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.abstention_rate | 0.7425742574257426 | 0.7425742574257426 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.full_count | 150 | 150 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.singleton_count | 52 | 52 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.singleton_true_label_fraction | 0.9807692307692307 | 0.9807692307692307 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.deviation.point | 0.04504950495049509 | 0.04504950495049509 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.05.deviation.lower | 0.010396039603960405 | 0.010396039603960405 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.05.deviation.upper | 0.050000000000000044 | 0.050000000000000044 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.05.deviation.half_width | 0.01980198019801982 | 0.01980198019801982 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.1.quantile | 0.6621428457682237 | 0.6621428463530682 | -5.84844506157367e-10 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.coverage | 0.9702970297029703 | 0.9702970297029703 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.abstention_rate | 0.4405940594059406 | 0.4405940594059406 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.empty_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.full_count | 89 | 89 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.singleton_count | 113 | 113 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.singleton_true_label_fraction | 0.9469026548672567 | 0.9469026548672567 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.deviation.point | 0.07029702970297025 | 0.07029702970297025 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.1.deviation.lower | -0.13267326732673268 | -0.13267326732673268 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.1.deviation.upper | 0.09999999999999998 | 0.09999999999999998 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.1.deviation.half_width | 0.11633663366336633 | 0.11633663366336633 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.2.quantile | 0.3923337643879117 | 0.39233376398264225 | 4.0526942912677555e-10 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.coverage | 0.6683168316831684 | 0.6683168316831684 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.abstention_rate | 0.24752475247524752 | 0.24752475247524752 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.empty_count | 50 | 50 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.full_count | 0 | 0 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.singleton_count | 152 | 152 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.singleton_true_label_fraction | 0.8881578947368421 | 0.8881578947368421 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.deviation.point | -0.1316831683168317 | -0.1316831683168317 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.conformal.0.2.deviation.lower | -0.40891089108910894 | -0.3891089108910892 | -0.019801980198019764 | DISCREPANCY | .01 C4_MC |
| conditions.t1ce_flair_only.conformal.0.2.deviation.upper | 0.04158415841584151 | 0.04158415841584151 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.conformal.0.2.deviation.half_width | 0.22524752475247523 | 0.21534653465346534 | 0.009900990099009882 | ok | .01  |
| conditions.t1ce_flair_only.oracle_aurc | 0.04323105577884521 | 0.023805669220342964 | 0.019425386558502244 | DISCREPANCY | 1e-9 UNRESOLVED_STOP |
| conditions.t1ce_flair_only.c5_adjacent.0.5-0.6.point | -0.045771790293783476 | -0.045771790293783476 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c5_adjacent.0.5-0.6.lower | -0.07317073170731707 | -0.07317073170731707 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.5-0.6.upper | 0.00048251520591527646 | 0.00048251520591527646 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.6-0.7.point | -0.03301777880397136 | -0.03301777880397136 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c5_adjacent.0.6-0.7.lower | -0.06511529226693162 | -0.06511529226693162 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.6-0.7.upper | 0.0010390210113137843 | 0.0010390210113137843 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.7-0.8.point | -0.03103808033385498 | -0.03103808033385498 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c5_adjacent.0.7-0.8.lower | -0.06372391227824642 | -0.06372391227824642 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.7-0.8.upper | -0.004578926875633582 | -0.004578926875633582 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.8-0.9.point | -0.03520553520553521 | -0.03520553520553521 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c5_adjacent.0.8-0.9.lower | -0.056862821787894716 | -0.056862821787894716 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c5_adjacent.0.8-0.9.upper | -0.0035951702618369358 | -0.0035951702618369358 | 0.0 | ok | .01  |
| conditions.t1ce_flair_only.c6_enrichment.0.5.observed | 0.18811881188118815 | 0.18811881188118815 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.5.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.5.n_rejected | 101 | 101 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.5.rejected_but_correct_rate | 0.6039603960396039 | 0.6039603960396039 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.5.p_adjusted | 5/40004 | 4999500049995001/50000000000000000000 | 12499999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.6.observed | 0.21707920792079208 | 0.21707920792079208 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.6.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.6.n_rejected | 80 | 80 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.6.rejected_but_correct_rate | 0.575 | 0.575 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.6.p_adjusted | 5/40004 | 4999500049995001/50000000000000000000 | 12499999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.7.observed | 0.2587458745874588 | 0.2587458745874588 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.7.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.7.n_rejected | 60 | 60 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.7.rejected_but_correct_rate | 0.5333333333333333 | 0.5333333333333333 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.7.p_adjusted | 5/40004 | 4999500049995001/50000000000000000000 | 12499999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.8.observed | 0.31707920792079214 | 0.31707920792079214 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.8.p_value | 1/10001 | 9.999000099990002e-05 | -5001/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.8.n_rejected | 40 | 40 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.8.rejected_but_correct_rate | 0.475 | 0.475 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.8.p_adjusted | 5/40004 | 4999500049995001/50000000000000000000 | 12499999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.9.observed | 0.3920792079207921 | 0.3920792079207921 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.9.p_value | 2/10001 | 9.999000099990002e-05 | 49999999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| conditions.t1ce_flair_only.c6_enrichment.0.9.n_rejected | 20 | 20 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.9.rejected_but_correct_rate | 0.4 | 0.4 | 0.0 | ok | 1e-9  |
| conditions.t1ce_flair_only.c6_enrichment.0.9.p_adjusted | 2/10001 | 4999500049995001/50000000000000000000 | 49999999999999994999/500050000000000000000000 | DISCREPANCY | exact C6_MC_OR_ENCODING |
| ablations.R7.n | 202 | 202 | 0.0 | ok | 1e-9  |
| ablations.R7.auroc | 0.9044057377049181 | 0.9044057377049181 | 0.0 | ok | 1e-9  |
| ablations.R7.auprc | 0.8762964390845026 | 0.8762964390845025 | 1.1102230246251565e-16 | ok | 1e-9  |
| ablations.R7.aurc_mean_over_cutoffs | 0.0901919544720286 | 0.09019195447202859 | 1.3877787807814457e-17 | ok | 1e-9  |
| ablations.R7.ece | 0.11801785059125706 | 0.11801785059125708 | -1.3877787807814457e-17 | ok | 1e-9  |
| ablations.R7.brier | 0.13727356649845235 | 0.13727356649845235 | 0.0 | ok | 1e-9  |
| ablations.R7.coverage | 1.0 | 1.0 | 0.0 | ok | 1e-9  |
| ablations.R7.delong_vs_R2.difference | -0.02418032786885249 | -0.02418032786885246 | -3.122502256758253e-17 | ok | 1e-9  |
| ablations.R7.delong_vs_R2.p_value | 0.048339346858190045 | 0.04833934685819038 | -3.3306690738754696e-16 | ok | 1e-9  |
| ablations.R7.aurc_vs_R2.point | 0.03966446990510389 | 0.03966446990510388 | 6.938893903907228e-18 | ok | 1e-9  |
| ablations.R7.aurc_vs_R2.lower | 0.01597727470238529 | 0.015977274702385295 | -6.938893903907228e-18 | ok | .01  |
| ablations.R7.aurc_vs_R2.upper | 0.06782056625843857 | 0.06782056625843856 | 1.3877787807814457e-17 | ok | .01  |
| ablations.R7.aurc_vs_R2.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| ablations.R8.n | 202 | 202 | 0.0 | ok | 1e-9  |
| ablations.R8.auroc | 0.9269467213114754 | 0.9269467213114754 | 0.0 | ok | 1e-9  |
| ablations.R8.auprc | 0.9051594347495573 | 0.9051594347495573 | 0.0 | ok | 1e-9  |
| ablations.R8.aurc_mean_over_cutoffs | 0.0756403181990247 | 0.07564031819902468 | 1.3877787807814457e-17 | ok | 1e-9  |
| ablations.R8.ece | 0.14169574235524332 | 0.1416957423552433 | 2.7755575615628914e-17 | ok | 1e-9  |
| ablations.R8.brier | 0.1432496402767709 | 0.1432496402767709 | 0.0 | ok | 1e-9  |
| ablations.R8.coverage | 1.0 | 1.0 | 0.0 | ok | 1e-9  |
| ablations.R8.delong_vs_R2.difference | -0.0016393442622951726 | -0.001639344262295082 | -9.063930161978817e-17 | ok | 1e-9  |
| ablations.R8.delong_vs_R2.p_value | 0.8941169860900324 | 0.8941169860900382 | -5.773159728050814e-15 | ok | 1e-9  |
| ablations.R8.aurc_vs_R2.point | 0.025112833632099985 | 0.025112833632099978 | 6.938893903907228e-18 | ok | 1e-9  |
| ablations.R8.aurc_vs_R2.lower | 0.0008665094217082761 | 0.0008665094217082761 | 0.0 | ok | .01  |
| ablations.R8.aurc_vs_R2.upper | 0.05593823145200499 | 0.055938231452004994 | -6.938893903907228e-18 | ok | .01  |
| ablations.R8.aurc_vs_R2.p_value | 28/667 | 28/667 | 0 | ok | exact  |
| ablations.R2.n | 202 | 202 | 0.0 | ok | 1e-9  |
| ablations.R2.auroc | 0.9285860655737705 | 0.9285860655737705 | 0.0 | ok | 1e-9  |
| ablations.R2.auprc | 0.897789537045756 | 0.8977895370457563 | -2.220446049250313e-16 | ok | 1e-9  |
| ablations.R2.aurc_mean_over_cutoffs | 0.05052748456692471 | 0.050527484566924706 | 6.938893903907228e-18 | ok | 1e-9  |
| ablations.R2.ece | 0.09663086735740267 | 0.09663086735740269 | -1.3877787807814457e-17 | ok | 1e-9  |
| ablations.R2.brier | 0.11781259301521835 | 0.11781259301521835 | 0.0 | ok | 1e-9  |
| ablations.R2.coverage | 1.0 | 1.0 | 0.0 | ok | 1e-9  |
| external_family.A1.point | -0.0002265176279195799 | -0.00022651762791958685 | 6.938893903907228e-18 | ok | 1e-9  |
| external_family.A1.lower | -0.005225538852066346 | -0.005225538852066346 | 0.0 | ok | .01  |
| external_family.A1.upper | 0.005830042345601972 | 0.005830042345601979 | -6.938893903907228e-18 | ok | .01  |
| external_family.A1.p_value | 594/667 | 594/667 | 0 | ok | exact  |
| external_family.A2.point | -0.06928997272266599 | -0.06928997272266599 | 0.0 | ok | 1e-9  |
| external_family.A2.lower | -0.11371607305258152 | -0.11371607305258155 | 2.7755575615628914e-17 | ok | .01  |
| external_family.A2.upper | -0.029165530978743425 | -0.029165530978743446 | 2.0816681711721685e-17 | ok | .01  |
| external_family.A2.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| external_family.A3.point | -0.0690634550947464 | -0.0690634550947464 | 0.0 | ok | 1e-9  |
| external_family.A3.lower | -0.11322116067809988 | -0.11322116067809987 | -1.3877787807814457e-17 | ok | .01  |
| external_family.A3.upper | -0.028812135013865217 | -0.028812135013865217 | 0.0 | ok | .01  |
| external_family.A3.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| external_family.B1.point | 0.007025666701449329 | 0.007025666701449329 | 0.0 | ok | 1e-9  |
| external_family.B1.lower | -0.0012394595613362818 | -0.0012394595613362818 | 0.0 | ok | .01  |
| external_family.B1.upper | 0.016423474764111965 | 0.016423474764111975 | -1.0408340855860843e-17 | ok | .01  |
| external_family.B1.p_value | 214/2001 | 214/2001 | 0 | ok | exact  |
| external_family.B2.point | 0.25985489896757885 | 0.25985489896757885 | 0.0 | ok | 1e-9  |
| external_family.B2.lower | 0.18983302435680924 | 0.18983302435680924 | 0.0 | ok | .01  |
| external_family.B2.upper | 0.3370456286316798 | 0.33704562863167975 | 5.551115123125783e-17 | ok | .01  |
| external_family.B2.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| external_family.B3.point | -0.010973121438421288 | -0.010973121438421288 | 0.0 | ok | 1e-9  |
| external_family.B3.lower | -0.028759281260692295 | -0.028759281260692295 | 0.0 | ok | .01  |
| external_family.B3.upper | 0.007004122728824307 | 0.00700412272882432 | -1.3010426069826053e-17 | ok | .01  |
| external_family.B3.p_value | 436/2001 | 436/2001 | 0 | ok | exact  |
| external_family.B4.point | 0.05055931673008156 | 0.05055931673008155 | 6.938893903907228e-18 | ok | 1e-9  |
| external_family.B4.lower | 0.01685717110128205 | 0.016857171101282053 | -3.469446951953614e-18 | ok | .01  |
| external_family.B4.upper | 0.08843422671856334 | 0.08843422671856331 | 2.7755575615628914e-17 | ok | .01  |
| external_family.B4.p_value | 2/667 | 2/667 | 0 | ok | exact  |
| external_family.B5.point | 0.013379056761252908 | 0.013379056761252915 | -6.938893903907228e-18 | ok | 1e-9  |
| external_family.B5.lower | -0.011426478278723005 | -0.011426478278723012 | 6.938893903907228e-18 | ok | .01  |
| external_family.B5.upper | 0.040343217404633674 | 0.040343217404633674 | 0.0 | ok | .01  |
| external_family.B5.p_value | 568/2001 | 568/2001 | 0 | ok | exact  |
| external_family.C1.point | -0.02500691345362914 | -0.025006913453629147 | 6.938893903907228e-18 | ok | 1e-9  |
| external_family.C1.lower | -0.0781785270998407 | -0.07786734507784494 | -0.0003111820219957595 | ok | .01  |
| external_family.C1.upper | 0.021050505865391356 | 0.02122924640373 | -0.00017874053833864464 | ok | .01  |
| external_family.C1.p_value | 8/29 | 554/2001 | -2/2001 | DISCREPANCY | exact UNPAIRED_STREAMS |
| external_family.D1.point | -0.009010367957233825 | -0.009010367382805556 | -5.744282688402436e-10 | ok | 1e-9  |
| external_family.D1.lower | -0.035428143837204204 | -0.03542814362609875 | -2.1110545256330937e-10 | ok | .01  |
| external_family.D1.upper | 0.009819235806519357 | 0.009819236344721897 | -5.382025398265045e-10 | ok | .01  |
| external_family.D1.p_value | 454/2001 | 454/2001 | 0 | ok | exact  |
| external_family.D2.point | -0.0033832239510218493 | -0.0033832238247315932 | -1.262902560306145e-10 | ok | 1e-9  |
| external_family.D2.lower | -0.005088663778355816 | -0.005088663596087476 | -1.822683401778158e-10 | ok | .01  |
| external_family.D2.upper | -0.0015221725310580008 | -0.0015221724647875748 | -6.627042599578747e-11 | ok | .01  |
| external_family.D2.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| external_family.E1.point | -0.02418032786885249 | -0.02418032786885246 | -3.122502256758253e-17 | ok | 1e-9  |
| external_family.E1.lower | -0.049699463062544 | -0.049699463062544 | 0.0 | ok | .01  |
| external_family.E1.upper | -0.00040800736101199227 | -0.00040800736101199227 | 0.0 | ok | .01  |
| external_family.E1.p_value | 0.048339346858190045 | 0.04833934685819038 | -3.3306690738754696e-16 | ok | 1e-9  |
| external_family.E2.point | 0.03966446990510389 | 0.03966446990510388 | 6.938893903907228e-18 | ok | 1e-9  |
| external_family.E2.lower | 0.01597727470238529 | 0.015977274702385295 | -6.938893903907228e-18 | ok | .01  |
| external_family.E2.upper | 0.06782056625843857 | 0.06782056625843856 | 1.3877787807814457e-17 | ok | .01  |
| external_family.E2.p_value | 2/2001 | 2/2001 | 0 | ok | exact  |
| external_family.E3.point | -0.0016393442622951726 | -0.001639344262295082 | -9.063930161978817e-17 | ok | 1e-9  |
| external_family.E3.lower | -0.027464364468483375 | -0.027464364468483375 | 0.0 | ok | .01  |
| external_family.E3.upper | 0.023107121741088994 | 0.023107121741088994 | 0.0 | ok | .01  |
| external_family.E3.p_value | 0.8941169860900324 | 0.8941169860900382 | -5.773159728050814e-15 | ok | 1e-9  |
| external_family.E4.point | 0.025112833632099985 | 0.025112833632099978 | 6.938893903907228e-18 | ok | 1e-9  |
| external_family.E4.lower | 0.0008665094217082761 | 0.0008665094217082761 | 0.0 | ok | .01  |
| external_family.E4.upper | 0.05593823145200499 | 0.055938231452004994 | -6.938893903907228e-18 | ok | .01  |
| external_family.E4.p_value | 28/667 | 28/667 | 0 | ok | exact  |
| pooled_BH.utsw:A1 | 28/115 | 28/115 | 0 | ok | exact  |
| pooled_BH.utsw:A2 | 1652/1725 | 1652/1725 | 0 | ok | exact  |
| pooled_BH.utsw:A3 | 133/138 | 133/138 | 0 | ok | exact  |
| pooled_BH.utsw:B1 | 1970/2001 | 1970/2001 | 0 | ok | exact  |
| pooled_BH.utsw:B2 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.utsw:B3 | 779/828 | 779/828 | 0 | ok | exact  |
| pooled_BH.utsw:B4 | 43/161 | 43/161 | 0 | ok | exact  |
| pooled_BH.utsw:B5 | 236/897 | 236/897 | 0 | ok | exact  |
| pooled_BH.utsw:D1 | 1336/1587 | 1336/1587 | 0 | ok | exact  |
| pooled_BH.utsw:D2 | 40/69 | 40/69 | 0 | ok | exact  |
| pooled_BH.utsw:E1 | 178322129841592361/220000000000000000 | 178322129841592361/220000000000000000 | 0 | ok | exact  |
| pooled_BH.utsw:E2 | 86/115 | 86/115 | 0 | ok | exact  |
| pooled_BH.utsw:E3 | 178322129841592361/220000000000000000 | 178322129841592361/220000000000000000 | 0 | ok | exact  |
| pooled_BH.utsw:E4 | 107/414 | 107/414 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:A1 | 64823481491527349/67500000000000000 | 129646962983055539/135000000000000000 | -841/135000000000000000 | DISCREPANCY | exact POOLED_PROPAGATION |
| pooled_BH.ucsf_pdgm:A2 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:A3 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:B1 | 107/414 | 107/414 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:B2 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:B3 | 227/552 | 227/552 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:B4 | 2/161 | 2/161 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:B5 | 284/621 | 284/621 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:C1 | 284/621 | 284/621 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:D1 | 227/552 | 227/552 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:D2 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:E1 | 280368211777502261/1800000000000000000 | 70092052944376051/450000000000000000 | -1943/1800000000000000000 | DISCREPANCY | exact POOLED_PROPAGATION |
| pooled_BH.ucsf_pdgm:E2 | 1/207 | 1/207 | 0 | ok | exact  |
| pooled_BH.ucsf_pdgm:E3 | 64823481491527349/67500000000000000 | 129646962983055539/135000000000000000 | -841/135000000000000000 | DISCREPANCY | exact POOLED_PROPAGATION |
| pooled_BH.ucsf_pdgm:E4 | 7/46 | 7/46 | 0 | ok | exact  |

## Claim statuses and coverage labels

| Claim / label | Yours | Reference | Status / cause |
|---|---|---|---|
| full.C3 | supported | supported | ok  |
| full.C4 | refuted | refuted | ok  |
| full.C5 | supported | supported | ok  |
| full.C6 | supported | supported | ok  |
| drop_t1.C3 | inconclusive at this n | inconclusive | ok  |
| drop_t1.C4 | refuted | refuted | ok  |
| drop_t1.C5 | supported | supported | ok  |
| drop_t1.C6 | inconclusive at this n | inconclusive | ok  |
| drop_t1ce.C3 | inconclusive at this n | inconclusive | ok  |
| drop_t1ce.C4 | refuted | refuted | ok  |
| drop_t1ce.C5 | supported | supported | ok  |
| drop_t1ce.C6 | inconclusive at this n | inconclusive | ok  |
| drop_t2.C3 | inconclusive at this n | inconclusive | ok  |
| drop_t2.C4 | refuted | refuted | ok  |
| drop_t2.C5 | supported | supported | ok  |
| drop_t2.C6 | supported | supported | ok  |
| drop_flair.C3 | supported | supported | ok  |
| drop_flair.C4 | refuted | refuted | ok  |
| drop_flair.C5 | supported | supported | ok  |
| drop_flair.C6 | supported | supported | ok  |
| t1ce_flair_only.C3 | supported | supported | ok  |
| t1ce_flair_only.C4 | refuted | refuted | ok  |
| t1ce_flair_only.C5 | supported | supported | ok  |
| t1ce_flair_only.C6 | supported | supported | ok  |
| overall.C3 | inconclusive at this n | supported | DISCREPANCY OWN_C3_AGGREGATION |
| overall.C4 | refuted | refuted | ok  |
| overall.C5 | supported | supported | ok  |
| overall.C6 | inconclusive at this n | inconclusive | ok  |
| secondary_worst.C3 | inconclusive at this n | inconclusive | ok  |
| full.alpha_0.05.coverage_label_0.07 | preserved | preserved | ok  |
| full.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| full.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| full.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| full.alpha_0.2.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| full.alpha_0.2.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1.alpha_0.05.coverage_label_0.07 | preserved | preserved | ok  |
| drop_t1.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t1.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1.alpha_0.2.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t1.alpha_0.2.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1ce.alpha_0.05.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t1ce.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1ce.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t1ce.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t1ce.alpha_0.2.coverage_label_0.07 | degraded | degraded | ok  |
| drop_t1ce.alpha_0.2.coverage_label_0.05 | degraded | degraded | ok  |
| drop_t2.alpha_0.05.coverage_label_0.07 | preserved | preserved | ok  |
| drop_t2.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t2.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t2.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_t2.alpha_0.2.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_t2.alpha_0.2.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.05.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.2.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| drop_flair.alpha_0.2.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| t1ce_flair_only.alpha_0.05.coverage_label_0.07 | preserved | preserved | ok  |
| t1ce_flair_only.alpha_0.05.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| t1ce_flair_only.alpha_0.1.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| t1ce_flair_only.alpha_0.1.coverage_label_0.05 | indeterminate | indeterminate | ok  |
| t1ce_flair_only.alpha_0.2.coverage_label_0.07 | indeterminate | indeterminate | ok  |
| t1ce_flair_only.alpha_0.2.coverage_label_0.05 | indeterminate | indeterminate | ok  |

## Pooled registered family

ONE family of 29 at q=.05: 14 UTSW raw p-values borrowed only now and 15 independently computed external p-values. The pooled_BH rows above compare this pass with the same pass on author raw external values. Author published final adjusted values were not supplied in an allowed comparison file, so agreement with that publication is not asserted. External-only BH in the JSON is supplementary and is not substituted for the pooled family.

| Member | Raw p used | Pooled adjusted p | Reject < .05 |
|---|---:|---:|---|
| utsw:A1 | 56/667 | 28/115 | False |
| utsw:A2 | 1652/2001 | 1652/1725 | False |
| utsw:A3 | 1862/2001 | 133/138 | False |
| utsw:B1 | 1970/2001 | 1970/2001 | False |
| utsw:B2 | 2/2001 | 1/207 | True |
| utsw:B3 | 1558/2001 | 779/828 | False |
| utsw:B4 | 86/667 | 43/161 | False |
| utsw:B5 | 236/2001 | 236/897 | False |
| utsw:D1 | 1336/2001 | 1336/1587 | False |
| utsw:D2 | 760/2001 | 40/69 | False |
| utsw:E1 | 0.597303138438992 | 178322129841592361/220000000000000000 | False |
| utsw:E2 | 344/667 | 86/115 | False |
| utsw:E3 | 0.6149038960054909 | 178322129841592361/220000000000000000 | False |
| utsw:E4 | 212/2001 | 107/414 | False |
| ucsf_pdgm:A1 | 594/667 | 64823481491527349/67500000000000000 | False |
| ucsf_pdgm:A2 | 2/2001 | 1/207 | True |
| ucsf_pdgm:A3 | 2/2001 | 1/207 | True |
| ucsf_pdgm:B1 | 214/2001 | 107/414 | False |
| ucsf_pdgm:B2 | 2/2001 | 1/207 | True |
| ucsf_pdgm:B3 | 436/2001 | 227/552 | False |
| ucsf_pdgm:B4 | 2/667 | 2/161 | True |
| ucsf_pdgm:B5 | 568/2001 | 284/621 | False |
| ucsf_pdgm:C1 | 8/29 | 284/621 | False |
| ucsf_pdgm:D1 | 454/2001 | 227/552 | False |
| ucsf_pdgm:D2 | 2/2001 | 1/207 | True |
| ucsf_pdgm:E1 | 0.048339346858190045 | 280368211777502261/1800000000000000000 | False |
| ucsf_pdgm:E2 | 2/2001 | 1/207 | True |
| ucsf_pdgm:E3 | 0.8941169860900324 | 64823481491527349/67500000000000000 | False |
| ucsf_pdgm:E4 | 28/667 | 7/46 | False |

## Saved numbers with no allowed reference field

These are DISCREPANCY (reference coverage), not established numeric disagreement. The permitted Phase 09 external JSON does not include per-condition AUROC/AUPRC/ECE/Brier; Phase 10 contains full only. It also omits trapezoid intervals, C5 p-values and ablation DeLong variance. Additional optional output is retained; no reference value is invented. Calibration n is measured from parquet, not inferred from internal test n.

| Number | Yours | Reference | Difference | Status |
|---|---:|---|---|---|
| calibration_n | 124 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M1.aurc_trapezoid.lower | 0.028197440795435104 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M1.aurc_trapezoid.upper | 0.07926943766160809 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M2.aurc_trapezoid.lower | 0.028197440795435104 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M2.aurc_trapezoid.upper | 0.07926943766160809 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M3.aurc_trapezoid.lower | 0.028938075704425657 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M3.aurc_trapezoid.upper | 0.07930666933382952 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M4.aurc_trapezoid.lower | 0.07253971096147928 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M4.aurc_trapezoid.upper | 0.17139411207816702 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M5.aurc_trapezoid.lower | 0.028197440795435104 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M5.aurc_trapezoid.upper | 0.07926943766160809 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M6.aurc_trapezoid.lower | 0.05676863386780159 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.mechanisms.M6.aurc_trapezoid.upper | 0.1353333777259497 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.5-0.6.p_value | 88/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.5-0.6.p_adjusted | 1520/6003 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.6-0.7.p_value | 312/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.6-0.7.p_adjusted | 312/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.7-0.8.p_value | 20/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.7-0.8.p_adjusted | 80/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.8-0.9.p_value | 380/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.full.c5_adjacent.0.8-0.9.p_adjusted | 1520/6003 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.auroc | 0.9136270491803279 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.auprc | 0.869001434716188 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.calibration.M1.ece | 0.0902428216315889 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.calibration.M1.brier | 0.12489746712624698 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.calibration.M2.ece | 0.09178439564184102 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.calibration.M2.brier | 0.1282017735439047 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M1.aurc_trapezoid.lower | 0.03348680387165584 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M1.aurc_trapezoid.upper | 0.08852598036132824 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M2.aurc_trapezoid.lower | 0.03348680387165584 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M2.aurc_trapezoid.upper | 0.08852598036132824 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M3.aurc_trapezoid.lower | 0.03420163871061763 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M3.aurc_trapezoid.upper | 0.0945486058269202 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M4.aurc_trapezoid.lower | 0.06859789878085741 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M4.aurc_trapezoid.upper | 0.1642147505602366 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M5.aurc_trapezoid.lower | 0.03348680387165584 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M5.aurc_trapezoid.upper | 0.08852598036132824 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M6.aurc_trapezoid.lower | 0.038276035984612704 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.mechanisms.M6.aurc_trapezoid.upper | 0.09935873913983222 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.5-0.6.p_value | 718/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.5-0.6.p_adjusted | 718/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.6-0.7.p_value | 454/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.6-0.7.p_adjusted | 1816/6003 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.7-0.8.p_value | 80/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.7-0.8.p_adjusted | 160/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.8-0.9.p_value | 8/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1.c5_adjacent.0.8-0.9.p_adjusted | 32/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.auroc | 0.7354508196721311 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.auprc | 0.6753994038298823 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.calibration.M1.ece | 0.22914758368883983 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.calibration.M1.brier | 0.2670643317487545 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.calibration.M2.ece | 0.2172138643199611 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.calibration.M2.brier | 0.25987480571674965 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M1.aurc_trapezoid.lower | 0.23458838123703998 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M1.aurc_trapezoid.upper | 0.3933325599314172 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M2.aurc_trapezoid.lower | 0.23458838123703998 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M2.aurc_trapezoid.upper | 0.3933325599314172 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M3.aurc_trapezoid.lower | 0.21870223474328263 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M3.aurc_trapezoid.upper | 0.3666003774428029 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M4.aurc_trapezoid.lower | 0.2951332587977708 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M4.aurc_trapezoid.upper | 0.4868659527275296 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M5.aurc_trapezoid.lower | 0.23458838123703998 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M5.aurc_trapezoid.upper | 0.3933325599314172 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M6.aurc_trapezoid.lower | 0.4892995543247109 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.mechanisms.M6.aurc_trapezoid.upper | 0.6777820494897365 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.5-0.6.p_value | 4/23 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.5-0.6.p_adjusted | 16/69 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.6-0.7.p_value | 4/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.6-0.7.p_adjusted | 12/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.7-0.8.p_value | 6/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.7-0.8.p_adjusted | 12/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.8-0.9.p_value | 1922/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t1ce.c5_adjacent.0.8-0.9.p_adjusted | 1922/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.auroc | 0.9369877049180327 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.auprc | 0.915026997560515 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.calibration.M1.ece | 0.1589174541335848 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.calibration.M1.brier | 0.11676188069688082 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.calibration.M2.ece | 0.15170979101208207 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.calibration.M2.brier | 0.12243502073987791 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M1.aurc_trapezoid.lower | 0.020252933194641002 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M1.aurc_trapezoid.upper | 0.06545334735388578 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M2.aurc_trapezoid.lower | 0.020252933194641002 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M2.aurc_trapezoid.upper | 0.06545334735388578 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M3.aurc_trapezoid.lower | 0.019185174759764237 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M3.aurc_trapezoid.upper | 0.06636197775308489 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M4.aurc_trapezoid.lower | 0.10000759572962054 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M4.aurc_trapezoid.upper | 0.24985372076190512 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M5.aurc_trapezoid.lower | 0.020252933194641002 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M5.aurc_trapezoid.upper | 0.06545334735388578 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M6.aurc_trapezoid.lower | 0.04198373093390768 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.mechanisms.M6.aurc_trapezoid.upper | 0.12302522434776436 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.5-0.6.p_value | 1756/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.5-0.6.p_adjusted | 1756/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.6-0.7.p_value | 106/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.6-0.7.p_adjusted | 212/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.7-0.8.p_value | 168/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.7-0.8.p_adjusted | 224/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.8-0.9.p_value | 18/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_t2.c5_adjacent.0.8-0.9.p_adjusted | 212/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.auroc | 0.8561475409836066 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.auprc | 0.8342808325915545 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.calibration.M1.ece | 0.07653971055077648 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.calibration.M1.brier | 0.1479914720782612 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.calibration.M2.ece | 0.06773916403923684 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.calibration.M2.brier | 0.14985328113459886 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M1.aurc_trapezoid.lower | 0.061190682430810106 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M1.aurc_trapezoid.upper | 0.1497913148282299 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M2.aurc_trapezoid.lower | 0.061190682430810106 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M2.aurc_trapezoid.upper | 0.1497913148282299 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M3.aurc_trapezoid.lower | 0.06283782043147085 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M3.aurc_trapezoid.upper | 0.15572349809655886 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M4.aurc_trapezoid.lower | 0.11136490702083275 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M4.aurc_trapezoid.upper | 0.24676296914668372 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M5.aurc_trapezoid.lower | 0.061190682430810106 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M5.aurc_trapezoid.upper | 0.1497913148282299 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M6.aurc_trapezoid.lower | 0.19224447085561966 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.mechanisms.M6.aurc_trapezoid.upper | 0.32531368049768106 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.5-0.6.p_value | 1166/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.5-0.6.p_adjusted | 1166/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.6-0.7.p_value | 140/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.6-0.7.p_adjusted | 172/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.7-0.8.p_value | 698/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.7-0.8.p_adjusted | 2792/6003 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.8-0.9.p_value | 86/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.drop_flair.c5_adjacent.0.8-0.9.p_adjusted | 172/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.n_positive | 80 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.auroc | 0.909733606557377 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.auprc | 0.8693042604042823 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.calibration.M1.ece | 0.13312180584301195 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.calibration.M1.brier | 0.1401596566232839 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.calibration.M2.ece | 0.13964446515897705 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.calibration.M2.brier | 0.14466675918935562 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_trapezoid.lower | 0.03676710326167421 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M1.aurc_trapezoid.upper | 0.09808533115776301 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_trapezoid.lower | 0.03676710326167421 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M2.aurc_trapezoid.upper | 0.09808533115776301 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_trapezoid.lower | 0.03763254581506908 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M3.aurc_trapezoid.upper | 0.10003776875003247 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_trapezoid.lower | 0.18100823732747223 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M4.aurc_trapezoid.upper | 0.359807033804338 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_trapezoid.lower | 0.03676710326167421 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M5.aurc_trapezoid.upper | 0.09808533115776301 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_trapezoid.lower | 0.04438817307651605 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.mechanisms.M6.aurc_trapezoid.upper | 0.13245204517098072 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.5-0.6.p_value | 110/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.5-0.6.p_adjusted | 112/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.6-0.7.p_value | 112/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.6-0.7.p_adjusted | 112/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.7-0.8.p_value | 16/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.7-0.8.p_adjusted | 32/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.8-0.9.p_value | 34/2001 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| conditions.t1ce_flair_only.c5_adjacent.0.8-0.9.p_adjusted | 32/667 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| ablations.R7.delong_vs_R2.variance | 0.00014999126505076506 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |
| ablations.R8.delong_vs_R2.variance | 0.0001517072808039599 | absent in allowed files | n/a | DISCREPANCY (reference coverage) |

## Validation and next action

Independent hand-derived self-checks ran at compute start. ruff check and ruff format were run on the final script. No commit was requested or made; Gate A/B were not claimed. This is a recomputation audit, not a scientific run or Gate C/D completion. The requested stopping rule applies.

Research Lead: adjudicate Block C's independent resampling and the own C3 aggregation bug before accepting T13.9; authorize a fresh, separately named rerun if corrections are wanted. Preserve these blinded artifacts.


## Append-only investigation addendum: all remaining causes resolved

The six rows labelled UNRESOLVED_STOP above are now traced to **OWN_ORACLE_TIES**.
The original rows and blinded JSON are preserved; this section appends the
investigation without overwriting their values. No discrepancies remain without
a diagnosed cause. No scientific compute function has been changed after unblinding.

The saved implementation calls `selective(-loss, loss)` for the oracle. That makes
all errors one tie block; every cutoff in that block takes its final risk, giving
`(n_errors / n)^2`. The oracle contract instead requires the minimum attainable
cutoff mean: all correct cases first, then each error admitted at its own cutoff,
`sum(j / (n - e + j) for j in 1..e) / n`. An exact Fraction hand-sum reproduces all
six author values exactly:

| Condition | Correct oracle hand-sum | Reference | Status |
|---|---:|---:|---|
| full | 0.0128083489181176 | 0.0128083489181176 | ok |
| drop_t1 | 0.014540481087361468 | 0.014540481087361468 | ok |
| drop_t1ce | 0.12259832379770286 | 0.12259832379770286 | ok |
| drop_t2 | 0.008981736521931584 | 0.008981736521931584 | ok |
| drop_flair | 0.022654949702475058 | 0.022654949702475058 | ok |
| t1ce_flair_only | 0.023805669220342964 | 0.023805669220342964 | ok |

These diagnostic hand-sums do not replace the saved oracle estimates or change
the original 2,060-number comparison denominator. All six original oracle values
remain DISCREPANCY, caused by my implementation bug. The final
script's comparison classifier now names this cause explicitly, while compute is
unchanged.

C6 was also checked against the exact hypergeometric null distribution using only
aggregate `(n, n_errors, n_rejected, rejected_errors)` and integer `math.comb`.
Of the 30 raw-p discrepancies, 14 have identical integer exceedance numerators and
are solely float-versus-rational encoding; 16 have different Monte Carlo counts
as well. Across both implementations, the largest absolute standardized count
deviation from the exact null tail was 2.2644288530742447 binomial standard
deviations. This supports Monte Carlo variation as the cause rather than an
observed-enrichment formula disagreement. The remaining 30 C6 discrepancies are
BH adjusted values propagating these count/encoding differences. Exact equality
still fails and no p-value was substituted. The author's full permutation-index
layout remains unverified.

Final cause inventory for the original 75 numeric discrepancies:

- 60 C6 p / BH values: 14 raw encoding-only, 16 raw Monte Carlo plus encoding,
  and 30 adjusted values propagating those differences.
- 6 oracle AURCs: own tie-block bug, resolved diagnostically by exact hand-sums.
- 4 C4 bootstrap lower endpoints: seed and index-layout Monte Carlo differences.
- 3 pooled BH adjusted values: tiny external DeLong floating-point differences;
  in this dataset the Block C1 raw-p difference does not change pooled BH values.
- 1 Block C1 raw p: independent-stream construction differs; restarting seed 0
  per cohort reproduces author aggregates, requiring Research Lead adjudication
  against the independent-cohort resampling contract.
- 1 temperature: 4.370088957372786e-9 solver difference, within the written 1e-6
  temperature-fit tolerance but outside this task's strict 1e-9 point tolerance.

All 24 per-condition claim categories match. Overall primary C3 still mismatches
because my aggregate summary incorrectly includes secondary conditions; the
primary full condition itself is supported on both sides. The other three
overall claim categories match. The 159 absent reference fields remain separately
listed; they are not counted as validated.

Final validation: ruff check passed; ruff format and ruff format --check passed.
The ASTs of all 23 non-compare functions, including compute and main, match the
pre-comparison script. The blinded JSON hash and pre-comparison script hash match
the recorded hashes. All 40 parquet SHA-256 sidecars verified. No commit was made.

Research Lead: adjudicate the resampling discrepancy and the two own bugs before
accepting T13.9; preserve these artifacts for any separately named correction run.
