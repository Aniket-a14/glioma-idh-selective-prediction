# Person C independent Codex recomputation

Date: 2026-11-18. Role: Person C, degraded solo fallback (D-001).

**DONE_WITH_CONCERNS:** 180/188 numbers agree under the guide tolerances. All 132 per-run numbers agree; 48/56 family numbers agree. The eight disagreements are A1 and A3 point, lower limit, upper limit and raw p. The scientific computation was not changed after reference access.

This is an independent numerical check of frozen internal UTSW predictions, not an independent check that the predictions themselves are correct. No external cohort data was read. BH, conformal sets, segmentation and exploratory endpoints are outside the requested check.

## Frozen-before-reference record

The first compute command wrote 188 numbers to `/private/tmp/person_c_codex_before_reference.json` before the reference JSON was opened. `PERSON_C_RESULTS_CODEX.json` is a byte-identical copy of that file.

- Results SHA-256: `d3b755781116649337eb601e87d5852224903d76ba7e5b07363884302044bfea`.
- First-compute implementation SHA-256: `0ba16e3e4da6f74ed6104fa38e033574455c9f1f6cd158fb95468093077bf96d`.
- Reference SHA-256 (verified against its sidecar): `3d2a220c49b558a543833057514ea65f733a80f5e49aa04411fd776ffd271f54`.
- Bootstrap matrix SHA-256 (native int64 bytes): `313e7ddd77856e99e30838e160edcee6318bd4274f184f7793deaa1844cee35c`.
- Matrix: `numpy.random.default_rng(0).integers(0, 124, size=(2000, 124))`.
- Calibration and test each contain 124 unique patients, 35 positive. Every paired input was checked for identical patient IDs, order and labels after sorting.
- Valid AUROC/AUPRC draws: 2000; skipped single-class draws: 0. All other statistics retain all 2000 draws.

After the freeze, a JSON schema adapter was added for comparison, and more hand-derived checks were added. No metric function, source selection or loss definition was changed. A final recomputation produced exactly the same 188 scalars and input hashes.

## Readings fixed before reference access

1. **R2 source.** Use `conditions/full.parquet` for R2 metrics and calibration fits, following Phase 10 S4 reuse of the Phase 09 condition cells. Use `predictions.parquet` for R7 and R8. R2 also has a separate predictions file; it was hash-verified but not used for its metrics. Its maximum absolute logit difference from the condition file is `4.38690185546875e-05`. This source distinction should be stated in the guide.
2. **Row order.** Sort each cohort lexicographically by `patient_id` and align every run/condition to it. The permitted text specifies the random matrix but not the patient order; parquet order is not lexicographic. Exact bootstrap reproduction needs both.
3. **AUPRC.** Use noninterpolated average precision: sum of recall increments multiplied by precision at each score-block end. The allowed text does not explicitly distinguish this from trapezoidal PR area. All AUPRC outputs agree with the reference.
4. **MC/ensemble prediction errors.** Read the mechanism-specific error vectors as errors of `mean(mc_samples) > 0.5` for M3 and `mean(member_probs) > 0.5` for M4. The texts define their ranking scores but do not explicitly say whether the M3 prediction itself is the stochastic mean or the underlying raw classifier. This is where the observed discrepancy occurs.
5. **Temperature/calibration arithmetic.** Promote stored float32 values to float64. Minimize calibration BCE over inverse temperature in `[1/20, 1/0.05]`, using the convex derivative and 100 bisection steps; keep temperature fixed across test bootstraps. M1 uses stored `p_hat`; M2 uses `sigmoid(logit/T)`. Missing-modality M5 scores use the full-input R2 T; this does not affect the ranking here.
6. **Intervals.** Linear percentile interpolation. Hanley–McNeil uses `Q1=A/(2-A)`, `Q2=2*A*A/(1+A)`, positive count m and negative count n, `[A(1-A)+(m-1)(Q1-A²)+(n-1)(Q2-A²)]/(mn)`, `z=1.959964`, and limits clipped to `[0,1]`. The allowed text gives the z but not the full formula or clipping rule.
7. **Ranking and ties.** Equal scores enter together; each cutoff within a tie block receives the block-end risk. AURC block sums use exact `Fraction` arithmetic and round once. Target coverage uses integer cross-products against the decimal fraction. Positive-class ECE uses ten equal-width left-closed bins, with 1 in the last.

## All eight disagreements: diagnosis

The independent full-input M3 AURC is `0.08030244467162564`. The reference A1/A3 imply M3 AURC `0.08036748109202106`. The difference is exactly `1/15376 = 1/(124*124)` to floating rounding.

One patient (zero-based row 71 in sorted internal-test order) has label 0, raw probability `0.5122405886650085`, and MC mean `0.49821494420369467`. The raw classifier is wrong and the MC-mean classifier is correct. This is the last accepted patient under the MC entropy ranking. Thus changing this one loss changes only cutoff 124, by `1/124`, and changes mean-over-cutoffs AURC by `1/(124*124)`.

A post-reference diagnostic kept all ranking scores and bootstrap rows fixed, but substituted the raw classifier loss vector for M3. It reproduced **all eight** A1/A3 reference scalars exactly, including their fraction-valued p-values. This supports the inference that the reference uses raw-classifier losses with M3 entropy ranking. This is an inference from numerical behavior; no reference implementation was opened. Float32 versus float64 MC means, exact decimal means and exact binary means all gave the same M3 AURC here; no M3 score ties occurred. The M4 mean classifier differs from raw on five patients, yet A2 agrees using M4 mean losses, so the loss convention needs to be stated separately for M3 and M4.

Consequences for each disagreement:

- `A1.point`, `.lower`, `.upper`, `.p_value`: M5 minus M3 uses different M3 errors. Independent raw p is `64/667`; reference is `56/667`.
- `A3.point`, `.lower`, `.upper`, `.p_value`: M3 minus M4 propagates the same M3 error choice with opposite point sign. Independent raw p is `1870/2001`; reference is `1862/2001`.

The diagnostic substitution is **not** applied to the delivered primary code or frozen results. It is reported as a post-reference sensitivity, not an independent 188/188 success. The report does not decide which prediction-loss definition the science intended.

## Full comparison (188 scalars)

Difference is mine minus reference. Points and limits use absolute tolerance `1e-9`; temperatures, M1/M2 ECE/Brier and D1/D2 use `1e-6`. Bootstrap p-values are compared as exact fractions, including D1/D2; DeLong p-values use `1e-9`. All 12 raw bootstrap p-values are fraction-valued: 10 agree, two disagree. Both DeLong p-values agree. AUROC bootstrap and Hanley–McNeil limits are listed separately. Coverage rows are attained point coverage; risk rows include bootstrap limits. No bootstrap interval for attained coverage was requested.

| Number | Mine | Reference | Difference | Tolerance | Result |
|---|---:|---:|---:|---:|:---|
| R2.temperature | 1.1247554289138795 | 1.1247554245437905 | 4.3700889573727864e-09 | 9.9999999999999995e-07 | agree |
| R2.auroc.point | 0.87833065810593902 | 0.87833065810593902 | 0 | 1.0000000000000001e-09 | agree |
| R2.auroc.lower | 0.80761051335234635 | 0.80761051335234635 | 0 | 1.0000000000000001e-09 | agree |
| R2.auroc.upper | 0.9386660617059891 | 0.9386660617059891 | 0 | 1.0000000000000001e-09 | agree |
| R2.auprc.point | 0.77823118706615624 | 0.77823118706615624 | 0 | 1.0000000000000001e-09 | agree |
| R2.auprc.lower | 0.64679724041914088 | 0.64679724041914088 | 0 | 1.0000000000000001e-09 | agree |
| R2.auprc.upper | 0.88413718845651457 | 0.88413718845651468 | -1.1102230246251565e-16 | 1.0000000000000001e-09 | agree |
| R2.auroc.hm_lower | 0.8006073732930139 | 0.80060737390608527 | -6.1307137144694934e-10 | 1.0000000000000001e-09 | agree |
| R2.auroc.hm_upper | 0.95605394291886414 | 0.95605394230579277 | 6.1307137144694934e-10 | 1.0000000000000001e-09 | agree |
| R2.aurc.point | 0.075534398020553853 | 0.075534398020553853 | 0 | 1.0000000000000001e-09 | agree |
| R2.aurc.lower | 0.040771294494848807 | 0.040771294494848807 | 0 | 1.0000000000000001e-09 | agree |
| R2.aurc.upper | 0.12297767039479833 | 0.12297767039479833 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.5.point | 0.048387096774193547 | 0.048387096774193547 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.5.lower | 0 | 0 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.5.upper | 0.12698412698412698 | 0.12698412698412698 | 0 | 1.0000000000000001e-09 | agree |
| R2.coverage_0.5 | 0.5 | 0.5 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.6.point | 0.093333333333333338 | 0.093333333333333338 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.6.lower | 0.026315789473684209 | 0.026315789473684209 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.6.upper | 0.17333333333333334 | 0.17333333333333334 | 0 | 1.0000000000000001e-09 | agree |
| R2.coverage_0.6 | 0.60483870967741937 | 0.60483870967741937 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.7.point | 0.11494252873563218 | 0.11494252873563218 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.7.lower | 0.056179775280898875 | 0.056179775280898875 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.7.upper | 0.20454545454545456 | 0.20454545454545456 | 0 | 1.0000000000000001e-09 | agree |
| R2.coverage_0.7 | 0.70161290322580649 | 0.70161290322580649 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.8.point | 0.16 | 0.16 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.8.lower | 0.080000000000000002 | 0.080000000000000002 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.8.upper | 0.23999999999999999 | 0.23999999999999999 | 0 | 1.0000000000000001e-09 | agree |
| R2.coverage_0.8 | 0.80645161290322576 | 0.80645161290322576 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.9.point | 0.16964285714285715 | 0.16964285714285715 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.9.lower | 0.10714285714285714 | 0.10714285714285714 | 0 | 1.0000000000000001e-09 | agree |
| R2.risk_0.9.upper | 0.25892857142857145 | 0.25892857142857145 | 0 | 1.0000000000000001e-09 | agree |
| R2.coverage_0.9 | 0.90322580645161288 | 0.90322580645161288 | 0 | 1.0000000000000001e-09 | agree |
| R2.M1.ece.point | 0.11886621112725816 | 0.11886621112725818 | -1.3877787807814457e-17 | 9.9999999999999995e-07 | agree |
| R2.M1.ece.lower | 0.086677289629340667 | 0.086677289629340667 | 0 | 9.9999999999999995e-07 | agree |
| R2.M1.ece.upper | 0.19030508085693587 | 0.1903050808569359 | -2.7755575615628914e-17 | 9.9999999999999995e-07 | agree |
| R2.M1.brier.point | 0.13992721038099037 | 0.13992721038099037 | 0 | 9.9999999999999995e-07 | agree |
| R2.M1.brier.lower | 0.10361669464181963 | 0.10361669464181963 | 0 | 9.9999999999999995e-07 | agree |
| R2.M1.brier.upper | 0.18092603853198203 | 0.18092603853198203 | 0 | 9.9999999999999995e-07 | agree |
| R2.M2.ece.point | 0.12216068673966862 | 0.12216068670319964 | 3.6468980613157953e-11 | 9.9999999999999995e-07 | agree |
| R2.M2.ece.lower | 0.090447350964200854 | 0.090447350859126627 | 1.0507422709693515e-10 | 9.9999999999999995e-07 | agree |
| R2.M2.ece.upper | 0.19420632704014765 | 0.19420632688976031 | 1.5038734146877175e-10 | 9.9999999999999995e-07 | agree |
| R2.M2.brier.point | 0.13871782796242776 | 0.13871782798972945 | -2.7301688687586534e-11 | 9.9999999999999995e-07 | agree |
| R2.M2.brier.lower | 0.10430432774897119 | 0.10430432771820898 | 3.0762212221979723e-11 | 9.9999999999999995e-07 | agree |
| R2.M2.brier.upper | 0.17745656572627272 | 0.17745656583230113 | -1.0602840827544924e-10 | 9.9999999999999995e-07 | agree |
| R7.temperature | 0.82746365327381377 | 0.82746365544374612 | -2.1699323449198005e-09 | 9.9999999999999995e-07 | agree |
| R7.auroc.point | 0.88796147672552161 | 0.88796147672552161 | 0 | 1.0000000000000001e-09 | agree |
| R7.auroc.lower | 0.82018096205730684 | 0.82018096205730684 | 0 | 1.0000000000000001e-09 | agree |
| R7.auroc.upper | 0.94095110761841172 | 0.94095110761841172 | 0 | 1.0000000000000001e-09 | agree |
| R7.auprc.point | 0.7414188599888365 | 0.7414188599888365 | 0 | 1.0000000000000001e-09 | agree |
| R7.auprc.lower | 0.58485845575770601 | 0.5848584557577059 | 1.1102230246251565e-16 | 1.0000000000000001e-09 | agree |
| R7.auprc.upper | 0.87306096425559176 | 0.87306096425559176 | 0 | 1.0000000000000001e-09 | agree |
| R7.auroc.hm_lower | 0.81298917979339347 | 0.81298918038476542 | -5.913719514083482e-10 | 1.0000000000000001e-09 | agree |
| R7.auroc.hm_upper | 0.96293377365764976 | 0.96293377306627781 | 5.913719514083482e-10 | 1.0000000000000001e-09 | agree |
| R7.aurc.point | 0.092867686302036956 | 0.092867686302036956 | 0 | 1.0000000000000001e-09 | agree |
| R7.aurc.lower | 0.039138139205007597 | 0.039138139205007597 | 0 | 1.0000000000000001e-09 | agree |
| R7.aurc.upper | 0.16573985066540567 | 0.16573985066540567 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.5.point | 0.080645161290322578 | 0.080645161290322578 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.5.lower | 0.015625 | 0.015625 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.5.upper | 0.14285714285714285 | 0.14285714285714285 | 0 | 1.0000000000000001e-09 | agree |
| R7.coverage_0.5 | 0.5 | 0.5 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.6.point | 0.066666666666666666 | 0.066666666666666666 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.6.lower | 0.025974025974025976 | 0.025974025974025976 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.6.upper | 0.14666666666666667 | 0.14666666666666667 | 0 | 1.0000000000000001e-09 | agree |
| R7.coverage_0.6 | 0.60483870967741937 | 0.60483870967741937 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.7.point | 0.091954022988505746 | 0.091954022988505746 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.7.lower | 0.034482758620689655 | 0.034482758620689655 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.7.upper | 0.17782771535580497 | 0.17782771535580497 | 0 | 1.0000000000000001e-09 | agree |
| R7.coverage_0.7 | 0.70161290322580649 | 0.70161290322580649 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.8.point | 0.14000000000000001 | 0.14000000000000001 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.8.lower | 0.070000000000000007 | 0.070000000000000007 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.8.upper | 0.215739662201514 | 0.215739662201514 | 0 | 1.0000000000000001e-09 | agree |
| R7.coverage_0.8 | 0.80645161290322576 | 0.80645161290322576 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.9.point | 0.16071428571428573 | 0.16071428571428573 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.9.lower | 0.089285714285714288 | 0.089285714285714288 | 0 | 1.0000000000000001e-09 | agree |
| R7.risk_0.9.upper | 0.22812063344201183 | 0.22812063344201183 | 0 | 1.0000000000000001e-09 | agree |
| R7.coverage_0.9 | 0.90322580645161288 | 0.90322580645161288 | 0 | 1.0000000000000001e-09 | agree |
| R7.M1.ece.point | 0.10786348094622936 | 0.10786348094622936 | 0 | 9.9999999999999995e-07 | agree |
| R7.M1.ece.lower | 0.08469879012029137 | 0.08469879012029137 | 0 | 9.9999999999999995e-07 | agree |
| R7.M1.ece.upper | 0.18035499292891466 | 0.18035499292891466 | 0 | 9.9999999999999995e-07 | agree |
| R7.M1.brier.point | 0.12940928085438691 | 0.12940928085438691 | 0 | 9.9999999999999995e-07 | agree |
| R7.M1.brier.lower | 0.096218507668758696 | 0.096218507668758696 | 0 | 9.9999999999999995e-07 | agree |
| R7.M1.brier.upper | 0.16884931595001995 | 0.16884931595001995 | 0 | 9.9999999999999995e-07 | agree |
| R7.M2.ece.point | 0.10863000398602134 | 0.10863000407217123 | -8.6149892775111425e-11 | 9.9999999999999995e-07 | agree |
| R7.M2.ece.lower | 0.083379460620041368 | 0.083379460819153012 | -1.9911164383934477e-10 | 9.9999999999999995e-07 | agree |
| R7.M2.ece.upper | 0.18140438760682051 | 0.1814043877134944 | -1.066738919419663e-10 | 9.9999999999999995e-07 | agree |
| R7.M2.brier.point | 0.12938796845897366 | 0.1293879684458252 | 1.3148454547362576e-11 | 9.9999999999999995e-07 | agree |
| R7.M2.brier.lower | 0.0936914864119925 | 0.09369148643800114 | -2.600863968638123e-11 | 9.9999999999999995e-07 | agree |
| R7.M2.brier.upper | 0.17227271964789961 | 0.17227271959453547 | 5.3364146435086468e-11 | 9.9999999999999995e-07 | agree |
| R8.temperature | 1.6540320445342624 | 1.6540320435209852 | 1.0132772398918632e-09 | 9.9999999999999995e-07 | agree |
| R8.auroc.point | 0.88876404494382022 | 0.88876404494382022 | 0 | 1.0000000000000001e-09 | agree |
| R8.auroc.lower | 0.81636762284701114 | 0.81636762284701114 | 0 | 1.0000000000000001e-09 | agree |
| R8.auroc.upper | 0.94809502787724198 | 0.94809502787724198 | 0 | 1.0000000000000001e-09 | agree |
| R8.auprc.point | 0.82276328203725602 | 0.82276328203725602 | 0 | 1.0000000000000001e-09 | agree |
| R8.auprc.lower | 0.70816906937303803 | 0.70816906937303814 | -1.1102230246251565e-16 | 1.0000000000000001e-09 | agree |
| R8.auprc.upper | 0.91152070818104203 | 0.91152070818104192 | 1.1102230246251565e-16 | 1.0000000000000001e-09 | agree |
| R8.auroc.hm_lower | 0.81402886045056444 | 0.81402886104006611 | -5.8950166970106466e-10 | 1.0000000000000001e-09 | agree |
| R8.auroc.hm_upper | 0.963499229437076 | 0.96349922884757433 | 5.8950166970106466e-10 | 1.0000000000000001e-09 | agree |
| R8.aurc.point | 0.097437747660466895 | 0.097437747660466895 | 0 | 1.0000000000000001e-09 | agree |
| R8.aurc.lower | 0.057325593104507654 | 0.057325593104507654 | 0 | 1.0000000000000001e-09 | agree |
| R8.aurc.upper | 0.15264310460029404 | 0.15264310460029404 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.5.point | 0.064516129032258063 | 0.064516129032258063 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.5.lower | 0.015873015873015872 | 0.015873015873015872 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.5.upper | 0.15625 | 0.15625 | 0 | 1.0000000000000001e-09 | agree |
| R8.coverage_0.5 | 0.5 | 0.5 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.6.point | 0.10666666666666667 | 0.10666666666666667 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.6.lower | 0.040000000000000001 | 0.040000000000000001 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.6.upper | 0.20779220779220781 | 0.20779220779220781 | 0 | 1.0000000000000001e-09 | agree |
| R8.coverage_0.6 | 0.60483870967741937 | 0.60483870967741937 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.7.point | 0.14942528735632185 | 0.14942528735632185 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.7.lower | 0.080459770114942528 | 0.080459770114942528 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.7.upper | 0.26436781609195403 | 0.26436781609195403 | 0 | 1.0000000000000001e-09 | agree |
| R8.coverage_0.7 | 0.70161290322580649 | 0.70161290322580649 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.8.point | 0.20999999999999999 | 0.20999999999999999 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.8.lower | 0.13 | 0.13 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.8.upper | 0.28999999999999998 | 0.28999999999999998 | 0 | 1.0000000000000001e-09 | agree |
| R8.coverage_0.8 | 0.80645161290322576 | 0.80645161290322576 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.9.point | 0.23214285714285715 | 0.23214285714285715 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.9.lower | 0.15929203539823009 | 0.15929203539823009 | 0 | 1.0000000000000001e-09 | agree |
| R8.risk_0.9.upper | 0.31858407079646017 | 0.31858407079646017 | 0 | 1.0000000000000001e-09 | agree |
| R8.coverage_0.9 | 0.90322580645161288 | 0.90322580645161288 | 0 | 1.0000000000000001e-09 | agree |
| R8.M1.ece.point | 0.1774308656291049 | 0.1774308656291049 | 0 | 9.9999999999999995e-07 | agree |
| R8.M1.ece.lower | 0.12210507146697487 | 0.12210507146697487 | 0 | 9.9999999999999995e-07 | agree |
| R8.M1.ece.upper | 0.24177742107678063 | 0.2417774210767806 | 2.7755575615628914e-17 | 9.9999999999999995e-07 | agree |
| R8.M1.brier.point | 0.16179373328510624 | 0.16179373328510624 | 0 | 9.9999999999999995e-07 | agree |
| R8.M1.brier.lower | 0.12318315453245586 | 0.12318315453245586 | 0 | 9.9999999999999995e-07 | agree |
| R8.M1.brier.upper | 0.20520232455559687 | 0.20520232455559687 | 0 | 9.9999999999999995e-07 | agree |
| R8.M2.ece.point | 0.17262175869336746 | 0.17262175868358512 | 9.7823416034259481e-12 | 9.9999999999999995e-07 | agree |
| R8.M2.ece.lower | 0.12772896458037533 | 0.12772896455756111 | 2.2814222733202882e-11 | 9.9999999999999995e-07 | agree |
| R8.M2.ece.upper | 0.24113921855539708 | 0.2411392185420678 | 1.3329282122498398e-11 | 9.9999999999999995e-07 | agree |
| R8.M2.brier.point | 0.15326356544007755 | 0.15326356544412181 | -4.044264922953289e-12 | 9.9999999999999995e-07 | agree |
| R8.M2.brier.lower | 0.12174340341596092 | 0.12174340341458777 | 1.3731515924320092e-12 | 9.9999999999999995e-07 | agree |
| R8.M2.brier.upper | 0.18770384680144919 | 0.18770384681700084 | -1.555164330646619e-11 | 9.9999999999999995e-07 | agree |
| A1.point | -0.0047680466510717917 | -0.0048330830714672091 | 6.5036420395417349e-05 | 1.0000000000000001e-09 | **DISAGREE** |
| A1.lower | -0.011912979785399746 | -0.011952751888752217 | 3.9772103352471097e-05 | 1.0000000000000001e-09 | **DISAGREE** |
| A1.upper | 0.00073050532041367487 | 0.00060807610289290138 | 0.00012242921752077349 | 1.0000000000000001e-09 | **DISAGREE** |
| A1.p_value | 64/667 | 56/667 | 8/667 | exact fraction | **DISAGREE** |
| A2.point | -0.0040291020851814796 | -0.0040291020851814796 | 0 | 1.0000000000000001e-09 | agree |
| A2.lower | -0.036659966783334476 | -0.036659966783334476 | 0 | 1.0000000000000001e-09 | agree |
| A2.upper | 0.029202169924684756 | 0.029202169924684756 | 0 | 1.0000000000000001e-09 | agree |
| A2.p_value | 1652/2001 | 1652/2001 | 0 | exact fraction | agree |
| A3.point | 0.0007389445658903121 | 0.00080398098628572945 | -6.5036420395417349e-05 | 1.0000000000000001e-09 | **DISAGREE** |
| A3.lower | -0.032442469175014123 | -0.032123739675673245 | -0.00031872949934087791 | 1.0000000000000001e-09 | **DISAGREE** |
| A3.upper | 0.036631335946148841 | 0.036818514564467747 | -0.00018717861831890614 | 1.0000000000000001e-09 | **DISAGREE** |
| A3.p_value | 1870/2001 | 1862/2001 | 8/2001 | exact fraction | **DISAGREE** |
| B1.point | 0.00034512481468966516 | 0.00034512481468966516 | 0 | 1.0000000000000001e-09 | agree |
| B1.lower | -0.019381034747971149 | -0.019381034747971149 | 0 | 1.0000000000000001e-09 | agree |
| B1.upper | 0.018190867077668173 | 0.018190867077668173 | 0 | 1.0000000000000001e-09 | agree |
| B1.p_value | 1970/2001 | 1970/2001 | 0 | exact fraction | agree |
| B2.point | 0.41717145250010407 | 0.41717145250010407 | 0 | 1.0000000000000001e-09 | agree |
| B2.lower | 0.2953757968410412 | 0.2953757968410412 | 0 | 1.0000000000000001e-09 | agree |
| B2.upper | 0.54339298444599426 | 0.54339298444599426 | 0 | 1.0000000000000001e-09 | agree |
| B2.p_value | 2/2001 | 2/2001 | 0 | exact fraction | agree |
| B3.point | -0.0025690026770017055 | -0.0025690026770017055 | 0 | 1.0000000000000001e-09 | agree |
| B3.lower | -0.025515833340294631 | -0.025515833340294631 | 0 | 1.0000000000000001e-09 | agree |
| B3.upper | 0.020396975242147848 | 0.020396975242147848 | 0 | 1.0000000000000001e-09 | agree |
| B3.p_value | 1558/2001 | 1558/2001 | 0 | exact fraction | agree |
| B4.point | 0.032683518308801715 | 0.032683518308801715 | 0 | 1.0000000000000001e-09 | agree |
| B4.lower | -0.0088844616576440119 | -0.0088844616576440119 | 0 | 1.0000000000000001e-09 | agree |
| B4.upper | 0.080492225365906722 | 0.080492225365906722 | 0 | 1.0000000000000001e-09 | agree |
| B4.p_value | 86/667 | 86/667 | 0 | exact fraction | agree |
| B5.point | 0.037920180774976456 | 0.037920180774976456 | 0 | 1.0000000000000001e-09 | agree |
| B5.lower | -0.0091097600142358032 | -0.0091097600142358032 | 0 | 1.0000000000000001e-09 | agree |
| B5.upper | 0.088628134923875113 | 0.088628134923875113 | 0 | 1.0000000000000001e-09 | agree |
| B5.p_value | 236/2001 | 236/2001 | 0 | exact fraction | agree |
| D1.point | -0.0032944756124104607 | -0.0032944755759414662 | -3.6468994490945761e-11 | 9.9999999999999995e-07 | agree |
| D1.lower | -0.027562568350256878 | -0.027562568215309266 | -1.3494761211263473e-10 | 9.9999999999999995e-07 | agree |
| D1.upper | 0.022334088665330827 | 0.022334088896014816 | -2.3068398927184042e-10 | 9.9999999999999995e-07 | agree |
| D1.p_value | 1336/2001 | 1336/2001 | 0 | exact fraction | agree |
| D2.point | 0.0012093824185626101 | 0.0012093823912609214 | 2.7301688687586534e-11 | 9.9999999999999995e-07 | agree |
| D2.lower | -0.0014282395529496973 | -0.0014282394943662621 | -5.8583435194950462e-11 | 9.9999999999999995e-07 | agree |
| D2.upper | 0.0040652562763590621 | 0.0040652561550681924 | 1.2129086970902314e-10 | 9.9999999999999995e-07 | agree |
| D2.p_value | 760/2001 | 760/2001 | 0 | exact fraction | agree |
| E1.point | 0.0096308186195825929 | 0.009630818619582664 | -7.1123662515049091e-17 | 1.0000000000000001e-09 | agree |
| E1.lower | -0.02609924971993936 | -0.02609924971993936 | 0 | 1.0000000000000001e-09 | agree |
| E1.upper | 0.046776233906673965 | 0.046776233906673965 | 0 | 1.0000000000000001e-09 | agree |
| E1.p_value | 0.59730313843899463 | 0.59730313843899197 | 2.6645352591003757e-15 | 1.0000000000000001e-09 | agree |
| E2.point | 0.017333288281483103 | 0.017333288281483103 | 0 | 1.0000000000000001e-09 | agree |
| E2.lower | -0.023702983906215443 | -0.023702983906215443 | 0 | 1.0000000000000001e-09 | agree |
| E2.upper | 0.070331914087633979 | 0.070331914087633979 | 0 | 1.0000000000000001e-09 | agree |
| E2.p_value | 344/667 | 344/667 | 0 | exact fraction | agree |
| E3.point | 0.010433386837881198 | 0.01043338683788122 | -2.2551405187698492e-17 | 1.0000000000000001e-09 | agree |
| E3.lower | -0.028581418581418591 | -0.028581418581418591 | 0 | 1.0000000000000001e-09 | agree |
| E3.upper | 0.050725191019726293 | 0.050725191019726293 | 0 | 1.0000000000000001e-09 | agree |
| E3.p_value | 0.61490389600549178 | 0.61490389600549089 | 8.8817841970012523e-16 | 1.0000000000000001e-09 | agree |
| E4.point | 0.021903349639913042 | 0.021903349639913042 | 0 | 1.0000000000000001e-09 | agree |
| E4.lower | -0.0038269661153558284 | -0.0038269661153558284 | 0 | 1.0000000000000001e-09 | agree |
| E4.upper | 0.052308626052731844 | 0.052308626052731844 | 0 | 1.0000000000000001e-09 | agree |
| E4.p_value | 212/2001 | 212/2001 | 0 | exact fraction | agree |

## Verification and environment

- Python `3.14.0`, NumPy `2.5.3`, pandas `3.0.6`.
- Interpreter: `/Users/aniketsaha/4th_Year/Glioma/.venv/bin/python`. No package installation.
- All 13 real parquet SHA-256 sidecars passed before dataframe use. The reference SHA-256 sidecar passed only after the independent results existed.
- Independent hand-derived checks passed: tied AUROC/AP, tied AURC/coverage, ECE bin boundaries, Brier, exact bootstrap p, DeLong identity/zero-variance/known placement-covariance/swap cases, temperature boundary and analytic interior optima, linear percentiles, and all-tied AP.
- SHA-256 tampering and missing-sidecar refusal checks passed on synthetic temporary payloads. Final replay reproduced all 188 saved numbers exactly.
- `ruff check` and `ruff format --check` passed on the standalone script.
- The comparison command exits 1 because eight values disagree, after saving its full comparison. Compute and self-test commands exit 0.
- Full Gate A (repository pre-commit, invariant script, unit suite) was not run: the requested read restriction excludes reference/source modules that those checks may inspect or import. No Gate B merge or scientific-run Gate C is claimed. Only the requested frozen-artifact recomputation and standalone checks were run.

## Reproduce

Use fresh output paths; the script refuses to overwrite its results and comparison files.

```sh
PY=/Users/aniketsaha/4th_Year/Glioma/.venv/bin/python
"$PY" scripts/person_c_independent_codex.py --self-test
"$PY" scripts/person_c_independent_codex.py \
  --results-root /private/tmp/claude-501/pcpkg/experiments \
  --output /private/tmp/person_c_codex_fresh.json
"$PY" scripts/person_c_independent_codex.py \
  --compare-results /private/tmp/person_c_codex_fresh.json \
  --reference /private/tmp/claude-501/pcpkg/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json \
  --comparison-output /private/tmp/person_c_codex_fresh_comparison.json
"$PY" -m ruff check scripts/person_c_independent_codex.py
"$PY" -m ruff format --check scripts/person_c_independent_codex.py
```

These compute/compare command forms were executed in this session with `person_c_codex_before_reference.json`, `person_c_codex_replay.json`, `PERSON_C_RESULTS_CODEX.json` and the comparison output paths below. The `fresh` filenames illustrate new destinations; they were not created in this session.

## Files opened

I did **not** open `scripts/person_c_recompute.py`, `src/glioma_selective/evaluation/phase10_analysis.py`, `src/glioma_selective/evaluation/phase09_analysis.py`, `src/glioma_selective/evaluation/selective_metrics.py`, `src/glioma_selective/evaluation/calibration_metrics.py`, or any file under `src/glioma_selective/statistics/`, `src/glioma_selective/selective/` or `src/glioma_selective/calibration/`. No `glioma_selective` module was imported. No other research documents, fixtures or implementation files were read.

Research text read, in this order:

1. `docs/research/protocols/PERSON_C_RECOMPUTATION_GUIDE.md`
2. `docs/research/protocols/PHASE09_METRIC_CONTRACTS.md`
3. `docs/research/protocols/PHASE10_STATS_CONTRACTS.md`
4. `docs/research/protocols/STATISTICAL_ANALYSIS_PLAN.md`

Data files opened, all beneath `/private/tmp/claude-501/pcpkg/experiments/`; each listed parquet and its `.sha256` sidecar were opened. SHA-256 values:

| Parquet path relative to experiments | SHA-256 |
|---|---|
| `01M46999FB083AX4WW0067YM13/conditions/drop_flair.parquet` | `9f045f07c4a43db298b79f22de8a4da941f9591e078a878fb05d5e40775d4395` |
| `01M46999FB083AX4WW0067YM13/conditions/drop_t1.parquet` | `fbdd0913521e7dd90a13599a0a109b8fb6371176ca4c24a18ee5075148a51f25` |
| `01M46999FB083AX4WW0067YM13/conditions/drop_t1ce.parquet` | `13823bf5b1e8e710c1c9f0db6c9138d5ab2a6bbe935015a497e39a9e484b1ead` |
| `01M46999FB083AX4WW0067YM13/conditions/drop_t2.parquet` | `16fd5f46c6875ea63d3daa700fd917f8e6194dec021eb3848afee8c62655fcb4` |
| `01M46999FB083AX4WW0067YM13/conditions/full.parquet` | `bf854c97a0c2a9f2b026d5fcdd633dc4252cb1c7677dd2ed3cec17ebe92744d0` |
| `01M46999FB083AX4WW0067YM13/conditions/t1ce_flair_only.parquet` | `da39bc355a9857828f0cf91837a2eceea0da27dd8b001afd486312aeb2018ad7` |
| `01M46999FB083AX4WW0067YM13/predictions.parquet` | `83f3d99c98557cf1f8d7084008f062dce760d0f3e65c26d7260bed3937e0611d` |
| `01M4FPECM9DKAR7F6B7VFRQNC5/conditions/full.parquet` | `3a24aff5d63378349603d133185d40944713d946835bb58087e1d8ebcd93ebe1` |
| `01M60CYFD2AYA8DCPBTDSJS4DM/conditions/full.parquet` | `76d3ab37a9add4049a639f246d68dc838f9abbb6598c1c3a62f1a5deb63aea01` |
| `01M66E2KR6ZV2YPBTNPF5FD53T/conditions/full.parquet` | `46354d02294ec551c2344da4467d1111acfb14ba5ce58da164d87a68b22a7cc5` |
| `01M776GTZC70FTB1ABD2DDMYHH/conditions/full.parquet` | `431d356e4423425e186bdd9beebde9857b3fa0a7d37fbc876b71bcfce9ba1d01` |
| `01M7C0KRNY5M2SNH59PH97XZ8K/predictions.parquet` | `eb2d9c1166f640e76bf360cf0fc896b281208d8a4e8356e7face6b47cbc39581` |
| `01M7JZYEBFCJF8WY0W1WJ3RZX7/predictions.parquet` | `e040da05a49e03768a1dbbbe17c60eba990fcd9eab03f195e18e20c3cb85853a` |

After the results freeze, the reference `01M46999FB083AX4WW0067YM13/phase10_analysis.json` and its `.sha256` sidecar were opened.

During the initial file scan, macOS AppleDouble metadata `01M46999FB083AX4WW0067YM13/._predictions.parquet` and `._predictions.parquet.sha256` were also opened. They are resource-fork metadata, not parquet predictions or checksum text. The first scan failed on their binary sidecar; a second attempt confirmed the metadata format. The actual implementation excludes `._*` files and verified all 13 real parquets without relaxing checksum checks.

Session-created files read: `scripts/person_c_independent_codex.py`, `docs/research/protocols/PERSON_C_RESULTS_CODEX.json`, and these diagnostic outputs under `/private/tmp/`: `person_c_codex_before_reference.json`, `person_c_codex_replay.json`, `person_c_codex_final_comparison.json`. Other created diagnostic outputs were `person_c_codex_first_comparison.json`, `person_c_codex_comparison.json`, `person_c_codex_m3_diagnostic.json` and `person_c_codex_m3_raw_loss_diagnostic.json`. Synthetic checksum-test payloads and sidecars were created, read and removed inside a temporary directory. This inventory excludes ordinary Python/package/tool internals and Git metadata.

## Delivery

Files: `scripts/person_c_independent_codex.py`, `docs/research/protocols/PERSON_C_RESULTS_CODEX.json`, `docs/research/protocols/PERSON_C_REPORT_CODEX.md`.

**No commit:** the initial `git add` succeeded, but subsequent staging and `git commit` were rejected by the sandbox: `Unable to create /Users/aniketsaha/4th_Year/Glioma/.git/worktrees/codex-person-c/index.lock: Operation not permitted`. The requested fallback to untracked files was attempted with `git restore --staged --` restricted to these three new files; it was rejected with the same error. Consequently the files remain staged, with this final report update additionally unstaged. No push or merge occurred, and no hook was bypassed. Restage the final report before committing outside the sandbox.

**Next action:** Research Lead should state the intended M3 prediction-loss definition in the permitted contract and decide whether the reference or the MC-mean reading needs correction; retain this 180/188 result as the independent finding.
