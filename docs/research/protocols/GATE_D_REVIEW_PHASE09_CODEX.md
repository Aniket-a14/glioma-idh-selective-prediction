# Gate D independent review — Phase 09

Date: 2026-11-18. Reviewed code: `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`.

Reviewer: Codex, independent of the phase author. **D-001 degraded solo fallback: a second agent, not a second human.** No claim is made that a human Person C reviewed or signed anything.

**Gate D verdict: FAIL — negative-results log empty; historical JSON-first ordering unverified.** Review task status: **DONE_WITH_CONCERNS**. Acceptance counts: 9 met, 2 not met, 1 cannot tell.

Criteria source: [PHASE_09_SELECTIVE_PREDICTION_INTERNAL.md](../phases/PHASE_09_SELECTIVE_PREDICTION_INTERNAL.md). Author briefs/readiness tables were treated as assertions to check. The embedded read-only checker below was actually executed, exit 0, using the requested virtualenv and `PYTHONPATH=src`. Each criterion repeats its exact command; shared commands were run once, not once per repeated listing. Outputs are trimmed.

Storage was resolved through `glioma_selective.utils.paths` with `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`. Only the named UTSW run artifacts and UTSW manifest summary were used (plus R8’s explicitly referenced stage-1 record). No external image/label file was opened; the authorization flag was unset and was never assigned. No installation, training, inference, refit of the IDH model, or write to the SSD occurred. A historical “met” GPU outcome means its frozen report was checked; a new live GPU measurement is not claimed.

## Criterion 1: met

Risk–coverage curves computed for all 6 conditions × 6 mechanisms internally.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
```

Comparison and judgment: Independent reconstruction agrees for all 36 internal curves. The main 30-cell artifact plus the six-cell M6 addendum form the complete internal grid; each uses the correct predictor’s loss, including the ensemble mean for M4.

## Criterion 2: met

AURC with patient-level bootstrap CI (≥1000 iterations) for every cell.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
cell {"aurc": 0.07553439802055385, "aurc_CI": {"lower": 0.04077129449484881, "upper": 0.12297767039479833}, "condition": "full", "magnitude": 1.0820103201377322, "mechanism": "M1", "n": 124, "violations": 253}
cell {"aurc": 0.07553439802055385, "aurc_CI": {"lower": 0.04077129449484881, "upper": 0.12297767039479833}, "condition": "full", "magnitude": 1.0820103201377322, "mechanism": "M2", "n": 124, "violations": 253}
cell {"aurc": 0.08036748109202108, "aurc_CI": {"lower": 0.0441873929934057, "upper": 0.1304888956018648}, "condition": "full", "magnitude": 0.7069314190888684, "mechanism": "M3", "n": 124, "violations": 217}
cell {"aurc": 0.07956350010573535, "aurc_CI": {"lower": 0.04124803125714573, "upper": 0.129299471078999}, "condition": "full", "magnitude": 3.1095500525501882, "mechanism": "M4", "n": 124, "violations": 553}
cell {"aurc": 0.07553439802055385, "aurc_CI": {"lower": 0.04077129449484881, "upper": 0.12297767039479833}, "condition": "full", "magnitude": 1.0820103201377322, "mechanism": "M5", "n": 124, "violations": 253}
cell {"aurc": 0.13425844311173038, "aurc_CI": {"lower": 0.07821206706790228, "upper": 0.21051392934807756}, "condition": "full", "magnitude": 7.226104782251479, "mechanism": "M6", "n": 124, "violations": 706}
cell {"aurc": 0.07587952283524353, "aurc_CI": {"lower": 0.039323728311828295, "upper": 0.12825515864050246}, "condition": "drop_t1", "magnitude": 1.8976978539815197, "mechanism": "M1", "n": 124, "violations": 422}
cell {"aurc": 0.07587952283524353, "aurc_CI": {"lower": 0.039323728311828295, "upper": 0.12825515864050246}, "condition": "drop_t1", "magnitude": 1.8976978539815197, "mechanism": "M2", "n": 124, "violations": 422}
cell {"aurc": 0.07982310381221963, "aurc_CI": {"lower": 0.04082319295850792, "upper": 0.13248474415859282}, "condition": "drop_t1", "magnitude": 1.1596421256835658, "mechanism": "M3", "n": 124, "violations": 324}
cell {"aurc": 0.07067209241697169, "aurc_CI
... [remaining output trimmed]
```

Comparison and judgment: Every cell has a rederived 2,000-draw patient bootstrap AURC interval, compared numerically at absolute 1e-9 with its frozen limits. Tie blocks are kept whole. The checker implements the metric directly with NumPy instead of calling production AURC.

## Criterion 3: met

Selective risk at every pre-registered matched-coverage level.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
```

Comparison and judgment: All 180 mechanism/condition/target points and attained coverages match for phi .9/.8/.7/.6/.5, as frozen in PREREGISTRATION.md and SAP §3. Risk intervals and paired D(phi) intervals were independently rederived from the same patient draws.

## Criterion 4: met

Empirical-vs-nominal coverage for every α in the pre-registered grid.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
conformal_quantiles_cal_test [["full", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["full", "refit", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "refit", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "refit", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["drop_t1", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9516129032258065, -0.008064516129032251], ["drop_t1", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["drop_t1", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1", "refit", 0.05, 0.7519863224670393, 0.9596774193548387, 0.9354838709677419, -0.024193548387096864], ["drop_t1", "refit", 0.1, 0.674464195463088, 0.9112903225806451, 0.8870967741935484, -0.024193548387096753], ["drop_t1", "refit", 0.2, 0.4049432223723396, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1ce", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.7580645161290323, -0.2016129032258065], ["drop_t1ce", "carried_over", 0.1, 0.662142 ... [trimmed]
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
```

Comparison and judgment: All 18 carried-over and 18 refit alpha cells match. The independent checker also repeats each 2,000-pair calibration/test bootstrap and agrees with the frozen deviation interval. These are conformal set coverage values, not the selective fraction accepted.

## Criterion 5: met

Monotonicity violations counted and magnitude-quantified with a bootstrap CI.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
```

Comparison and judgment: All 36 pairwise violation counts, total positive risk-difference magnitudes, and 2,000-draw bootstrap magnitude intervals agree. For full M5: 253 violating pairs, magnitude 1.08201032014; no eyeballing of curves substitutes for this check.

## Criterion 6: met

**Rejected-but-correct rate reported** for every mechanism and condition.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
```

Comparison and judgment: All 180 rejected-but-correct rates and rejected counts agree with independently selected tie-block prefixes. The code calculates correctness among rejected patients, not rejection rate or correctness in the accepted set.

## Criterion 7: met

Abstention/error enrichment computed with a permutation test.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
```

Comparison and judgment: All 180 observed enrichment differences, seeded 10,000-permutation p-values, and grid-wise BH adjustments are recomputed and agree. Compared with SAP §5, D-050 +1 Monte Carlo convention, and the stored per-cell enrichment block.

## Criterion 8: met

Calibration-vs-test coverage discrepancy reported.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
conformal_quantiles_cal_test [["full", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["full", "refit", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9596774193548387, 0.0], ["full", "refit", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["full", "refit", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7258064516129032, -0.08064516129032251], ["drop_t1", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.9516129032258065, -0.008064516129032251], ["drop_t1", "carried_over", 0.1, 0.6621428466616712, 0.9112903225806451, 0.8709677419354839, -0.040322580645161255], ["drop_t1", "carried_over", 0.2, 0.3923337637687951, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1", "refit", 0.05, 0.7519863224670393, 0.9596774193548387, 0.9354838709677419, -0.024193548387096864], ["drop_t1", "refit", 0.1, 0.674464195463088, 0.9112903225806451, 0.8870967741935484, -0.024193548387096753], ["drop_t1", "refit", 0.2, 0.4049432223723396, 0.8064516129032258, 0.7580645161290323, -0.048387096774193505], ["drop_t1ce", "carried_over", 0.05, 0.7772720385000738, 0.9596774193548387, 0.7580645161290323, -0.2016129032258065], ["drop_t1ce", "carried_over", 0.1, 0.662142 ... [trimmed]
```

Comparison and judgment: All 36 calibration/test coverage discrepancies are present and independently verified. Full input differences are 0, -0.04032258065, -0.08064516129 at alpha .05/.10/.20. Carried-over comparisons use the original full-input calibration set; interpreting this as the masked calibration set would be a different quantity.

## Criterion 9: met

Independent implementations agree.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
grid_checks {"curves_and_aurc_and_monotonicity": 36, "enrichment_observed_difference": 180, "max_aurc_difference": 5.551115123125783e-17, "selective_risk_and_rejected_correct": 180}
bootstrap_and_permutation_recomputed {"BH_grid_adjustments": 180, "cells": 36, "monotonicity_intervals": 36, "patient_bootstrap_iterations": 2000, "permutation_tests": 180, "permutations_each": 10000, "risk_intervals": 180, "two_stage_conformal_intervals": 36}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
```

Output (trimmed):

```text
83 passed in 0.73s
```

Comparison and judgment: The new reviewer rederivation agrees across the real grid (max AURC absolute difference 5.56e-17). Existing independently written AURC-vs-risk-coverage and exact-fraction fixture checks also pass in tests/unit/test_selective_crosscheck.py. This is D-001 agent fallback evidence, not a second human verification.

## Criterion 10: cannot tell

All results written as machine-readable JSON **before** any table or figure is produced.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
analysis_hashes {"M6": "9fc919d4906d527b1dd52eaffafc44f413e5f8d03b1fcae4f707262d88f9d8dc", "phase09": "99f48c7dd3069fc657f15f1009c0d6628fbe5369b9f79e96259de420f99dc3e9"}
first_results_commit "4ca025a 2026-11-14 08:30:52 +0530 docs(results): Phase 08 and Phase 09 internal results for R2 to R6; state update\n558473d 2026-11-17 09:59:06 +0530 docs: correct M6 statement (D-005/D-006), log D-055 C4 decision and open D-056\n36048b2 2026-11-17 14:25:16 +0530 docs: M6 (R1) results, D-056 sweep done\n"
```

Comparison and judgment: F04: both SHA-256-verified JSON files exist, and code writes machine-readable JSON before downstream consumers can read it. This supports the current pipeline ordering. The synchronized SSD files have no immutable creation/event record proving that every historical table/figure was first made only after JSON was written. Git dates for result documents and content hashes do not prove that universal timing claim. An original analysis/renderer event log or equivalent dated provenance would settle it.

## Criterion 11: not met

**C1, C2, C5, C6 adjudicated internally** against their verbatim pre-registered refutation criteria — support or refute stated explicitly, with no hedging.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
independently_adjudicated_claims {"C1": "supported", "C2": "refuted", "C4": "refuted", "C5": "inconclusive", "C6": "refuted"}
claims {"C1": "supported", "C2": "refuted", "C3": "not evaluated", "C4": "refuted", "C5": "inconclusive", "C6": "refuted"}
D-035 "D-035 \u2014 How the SPEC's refutation criteria for C1, C2, C3, C5 and C6 are applied to finite samples\n**Status:** RESOLVED 2026-09-30 (Research Lead: alternative (c), three-way rule) \u00b7 **Resolve by:** Phase 05 (before `PREREGISTRATION.md` is hashed, T05.10) \u00b7 **Blocking:** was YES for T05.7 and T05.10; cleared once the rule is written into `PREREGISTRATION.md` and `STATISTICAL_ANALYSIS_PLAN.md`\n\n**Conflict.** SPEC \u00a71.4 states the results that would prove each claim wrong in words that cannot be applied literally to\nestimates from a 124-patient test set. C1: \"selective risk at *any* fixed coverage >= always-predict ... [remaining decision entry trimmed]
```

Comparison and judgment: F07: literal criterion 11 demands “support or refute ... no hedging”, but C5 is explicitly inconclusive. Under the *approved, frozen* D-035/D-050 three-way rules, all adjudications are correct: C1 supported, C2 refuted, C5 inconclusive, C6 refuted; C4 also refuted. I do not replace the approved rule with a new binary test. Research Lead should explicitly reconcile the phase wording with its already-approved three-way rule. This is a wording/acceptance mismatch, not an incorrect numerical decision.

## Criterion 12: not met

Any refutation recorded in `paper/NEGATIVE_RESULTS.md` **the day it is found.**

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
negative_log ["paper/NEGATIVE_RESULTS.md:1: # NEGATIVE RESULTS LOG", "paper/NEGATIVE_RESULTS.md:2: ", "paper/NEGATIVE_RESULTS.md:3: **Written the moment a claim is refuted, not at write-up time.** This is the", "paper/NEGATIVE_RESULTS.md:4: practical defence against retroactively softening a result after seeing it", "paper/NEGATIVE_RESULTS.md:5: (`docs/research/PUBLICATION_PLAN.md` \u00a75). Ships in the manuscript exactly as", "paper/NEGATIVE_RESULTS.md:6: recorded here.", "paper/NEGATIVE_RESULTS.md:7: ", "paper/NEGATIVE_RESULTS.md:8: **Standing rule** (`docs/research/README.md`, `MASTER_RESEARCH_EXECUTION_PLAN.md`", "paper/NEGATIVE_RESULTS.md:9: \u00a74): if selective prediction fails under shift \u2014 non-monotonic risk\u2013coverage", "paper/NEGATIVE_RESULTS.md:10: curves, coverage collapse, calibration degradation \u2014 that is the finding, and", "paper/NEGATIVE_RESULTS.md:11: it is publishable. **No experiment is re-run, re-tuned, or re-scoped because", "paper/NEGATIVE_RESULTS.md:12: its outcome refutes a claim.**", "paper/NEGATIVE_RESULTS.md:13: ", "paper/NEGATIVE_RESULTS.md:14: Every pre-registered falsification condition a result can trigger is listed", "paper/NEGATIVE_RESULTS.md:15: in `docs/research/SPEC_TRACEABILITY_MATRIX.md` Part 2, verbatim, against", "paper/NEGATIVE_RESULTS.md:16: C1\u2013C6. When a run's result meets one, it is entered below **before** any", "paper/NEGATIVE_RESULTS.md:17: further analysis on that claim continues.", "paper/NEGATIVE_RESULTS.m ... [trimmed]
negative_log_git "c0c6f00 2026-09-11 14:11:17 +0530 paper: continuously-maintained skeleton (T00.9)\n"
first_results_commit "4ca025a 2026-11-14 08:30:52 +0530 docs(results): Phase 08 and Phase 09 internal results for R2 to R6; state update\n558473d 2026-11-17 09:59:06 +0530 docs: correct M6 statement (D-005/D-006), log D-055 C4 decision and open D-056\n36048b2 2026-11-17 14:25:16 +0530 docs: M6 (R1) results, D-056 sweep done\n"
independently_adjudicated_claims {"C1": "supported", "C2": "refuted", "C4": "refuted", "C5": "inconclusive", "C6": "refuted"}
```

Comparison and judgment: F03: paper/NEGATIVE_RESULTS.md is still the empty skeleton and says “No entries yet — no claim has been evaluated”. Its last commit is 2026-09-11; Phase 09 refutations were committed in the results doc by 2026-11-14. C2/C4/C6 are refuted in the frozen file. Draft entries elsewhere do not satisfy the named-file or same-day requirement. The same-day deadline has already been missed; a later dated entry must disclose the actual delay. paper/ is human-owned and was not edited.

## Scientific validation

The independent checker verifies the real 36-cell grid, all 180 risk/rejected-correct/enrichment operating points, 36 AURC and monotonicity intervals, and 36 two-stage conformal intervals. The random-confidence large-cohort negative-control test passed in the unit suite. C1/C2/C4/C5/C6 were independently adjudicated against the frozen rules. Non-monotonic finite-sample curves are preserved.

F03 is a missed mandatory same-day log, not a negative scientific result being treated as failure. F04 is a provenance limit; JSON-first code today does not prove all historical ordering. F07 is the literal binary wording versus approved three-way decision mismatch.

Next action: Research Lead enters the delayed negative findings with truthful discovery/entry dates and resolves the acceptance/provenance gaps.

## Reproducible read-only checker

The command above executes this embedded code. It contains reviewer calculations and source inspection only; it never calls artifact-writing analysis entry points.

<!-- BEGIN REVIEW CHECKER -->
```python
import sys, os, json, hashlib, math, re, subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import minimize_scalar
from scipy.special import expit
from glioma_selective.utils import paths
assert 'GLIOMA_EXTERNAL_EVAL_AUTHORIZED' not in os.environ
RUNS = ['01M45268QDQ2CFBSPNH117MF41','01M46999FB083AX4WW0067YM13','01M4FPECM9DKAR7F6B7VFRQNC5','01M60CYFD2AYA8DCPBTDSJS4DM','01M66E2KR6ZV2YPBTNPF5FD53T','01M776GTZC70FTB1ABD2DDMYHH','01M7C0KRNY5M2SNH59PH97XZ8K','01M7JZYEBFCJF8WY0W1WJ3RZX7']
ROOT = paths.experiments_dir()
CONDS = ['full','drop_t1','drop_t1ce','drop_t2','drop_flair','t1ce_flair_only']
GRID = [.9,.8,.7,.6,.5]
def emit(tag, value): print(tag, json.dumps(value, sort_keys=True, default=str))
def load(i,name): return json.loads((ROOT/RUNS[i-1]/name).read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def verified(p):
 assert digest(p)==p.with_name(p.name+'.sha256').read_text().split()[0], str(p)
 return True
def frame(i,name='predictions.parquet',split=None):
 p=ROOT/RUNS[i-1]/name; verified(p); f=pd.read_parquet(p)
 assert set(f.cohort)<= {'utsw_calibration','utsw_internal_test'}, str(p)
 if split: f=f[f.cohort=='utsw_'+split]
 assert not f.duplicated(['patient_id','cohort','modality_condition']).any()
 return f.sort_values('patient_id').reset_index(drop=True)
def temp(f):
 z=f.logit.to_numpy(float); y=f.label.to_numpy(int)
 r=minimize_scalar(lambda t:np.mean(np.logaddexp(0,z/np.exp(t))-y*z/np.exp(t)),bounds=(math.log(.05),math.log(20)),method='bounded',options={'xatol':1e-12})
 return float(np.exp(r.x))
def ece(p,y,b=10):
 q=np.minimum((p*b).astype(int),b-1)
 return sum(abs(float(np.sum(p[q==i]-y[q==i])))/len(y) for i in range(b))
def auc(p,y):
 a=p[y==1,None]; b=p[y==0][None,:]
 return float(np.mean((a>b)+.5*(a==b)))
def ap(p,y):
 o=np.argsort(-p,kind='stable'); p=p[o];y=y[o]; k=np.flatnonzero(np.r_[p[1:]!=p[:-1],True])+1
 tp=np.cumsum(y)[k-1];return float(np.sum(np.diff(np.r_[0,tp])*tp/k)/y.sum())
def curve(s,e):
 o=np.argsort(-np.asarray(s),kind='stable'); s=np.asarray(s)[o];e=np.asarray(e)[o]
 k=np.flatnonzero(np.r_[s[1:]!=s[:-1],True])+1; risks=np.cumsum(e)[k-1]/k
 return k,risks,e,o
def area(s,e):
 k,r,_,_=curve(s,e);return float(np.sum(np.diff(np.r_[0,k])*r)/len(e))
def interval(v): return np.quantile(v,[.025,.975])
def close(a,b,tol=1e-9):
 assert np.allclose(a,b,atol=tol,rtol=0), (a,b)
def quantile(p,y,a):
 from fractions import Fraction
 n=len(y); k=math.ceil((n+1)*(1-Fraction(str(a))))
 s=np.where(y==1,1-p,p)
 return float(np.sort(s)[k-1]) if k<=n else math.inf

def phase09():
 j=load(2,'phase09_analysis.json');m6=load(2,'phase09_m6_analysis.json');verified(ROOT/RUNS[1]/'phase09_analysis.json');verified(ROOT/RUNS[1]/'phase09_m6_analysis.json')
 emit('analysis_hashes',{'phase09':digest(ROOT/RUNS[1]/'phase09_analysis.json'),'M6':digest(ROOT/RUNS[1]/'phase09_m6_analysis.json')})
 emit('resampling',j['results_summary']);checked=0;rejected=0;enrichment=0;conformal=[];maxdiff=0.
 for c in CONDS:
  f=frame(2,'conditions/'+c+'.parquet',split='internal_test');cal=frame(2,'conditions/'+c+'.parquet',split='calibration');T=temp(frame(2,'conditions/full.parquet',split='calibration'));prob=expit(f.logit.to_numpy(float)/T);raw=f.p_hat.to_numpy(float);y=f.label.to_numpy(int);errors=((raw>=.5)!=y).astype(int)
  members=[]
  for i in range(2,7):
   fm=frame(i,'conditions/'+c+'.parquet',split='internal_test');assert fm.patient_id.tolist()==f.patient_id.tolist();assert fm.label.tolist()==f.label.tolist();members.append(fm.p_hat.to_numpy(float))
  samples=np.asarray(f.mc_dropout_samples.tolist());q=samples.mean(axis=1);ent=np.where(q>0,q*np.log(np.maximum(q,1e-300)),0)+np.where(q<1,(1-q)*np.log(np.maximum(1-q,1e-300)),0)
  scores={'M1':np.maximum(raw,1-raw),'M2':np.maximum(prob,1-prob),'M3':ent,'M4':-np.var(members,axis=0),'M5':np.maximum(prob,1-prob)}
  for m in ['M1','M2','M3','M4','M5','M6']:
   s=scores.get(m);e=errors if m!='M4' else ((np.mean(members,axis=0)>=.5)!=y).astype(int)
   block=j['conditions'][c][m] if m!='M6' else m6['conditions'][c]
   if m=='M6':
    fm=frame(1,'conditions/'+c+'.parquet',split='internal_test');p=fm.p_hat.to_numpy(float);s=np.maximum(p,1-p);e=((p>=.5)!=fm.label.to_numpy(int)).astype(int)
   k,r,ordered,order=curve(s,e);points=np.c_[k/len(e),r];close(points,block['rc_points']);a=area(s,e);close(a,block['aurc_mean_over_cutoffs']);maxdiff=max(maxdiff,abs(a-block['aurc_mean_over_cutoffs']))
   dif=r[:,None]-r[None,:];triangle=np.triu(np.ones(dif.shape,dtype=bool),1);count=int(np.sum(triangle & (dif>1e-15)));mag=float(np.sum(np.maximum(dif[triangle],0)));close(mag,block['monotonicity']['magnitude']);assert count==block['monotonicity']['violations']
   assert all(x in block['aurc_bootstrap_95_interval'] for x in ['lower','upper']);assert all(x in block['monotonicity']['bootstrap_95_interval'] for x in ['lower','upper'])
   draws=np.random.default_rng(0).integers(0,len(e),size=(2000,len(e)));bs=[];riskdraws={g:[] for g in GRID}
   for idx in draws:
    kk,rr,_,_=curve(np.asarray(s)[idx],e[idx]);bs.append(area(np.asarray(s)[idx],e[idx]))
    for g in GRID:riskdraws[g].append(rr[np.searchsorted(kk/len(e),g)])
   close(interval(bs),[block['aurc_bootstrap_95_interval'][x] for x in ['lower','upper']])
   ci=CONDS.index(c);mi=int(m[1:])-1;mono_seed=ci*6+mi
   if m=='M6':mono_seed=ci*6+5
   mono=[]
   for idx in np.random.default_rng(mono_seed).integers(0,len(e),size=(2000,len(e))):
    _,rr,_,_=curve(np.asarray(s)[idx],e[idx]);dd=rr[:,None]-rr[None,:];mono.append(float(np.sum(np.maximum(dd[np.triu_indices(len(rr),1)],0))))
   close(interval(mono),[block['monotonicity']['bootstrap_95_interval'][x] for x in ['lower','upper']])
   pvalues=[]
   for g in GRID:
    close(interval(riskdraws[g]),[block['selective_risk_at_coverage'][str(g)]['risk_95_interval'][x] for x in ['lower','upper']])
    dd=np.array(riskdraws[g])-e[draws].mean(axis=1);close(interval(dd),[block['selective_risk_at_coverage'][str(g)]['D_phi'][x] for x in ['lower','upper']])
    ix=int(np.searchsorted(k/len(e),g));op=block['selective_risk_at_coverage'][str(g)];close(r[ix],op['risk']);close(k[ix]/len(e),op['attained_coverage']);nrej=len(e)-int(k[ix]);rb=float(np.mean(1-ordered[k[ix]:])) if nrej else None;close(rb,op['rejected_but_correct_rate']);rejected+=1
    en=block['enrichment'][str(g)];obs=float(np.mean(ordered[k[ix]:])-np.mean(e));close(obs,en['observed_difference']);assert 0<=en['p_value']<=1;enrichment+=1
    rng=np.random.default_rng(GRID.index(g));cut=s[order[k[ix]-1]];reject=np.asarray(s)<cut;actual=int(e[reject].sum());permcount=sum(int(e[rng.permutation(len(e))[:nrej]].sum())>=actual for _ in range(10000));pv=(1+permcount)/10001;close(pv,en['p_value']);pvalues.append(pv)
   orderp=np.argsort(pvalues);adj=np.empty(5);adj[orderp]=np.minimum(1,np.minimum.accumulate((np.array(pvalues)[orderp]*5/np.arange(1,6))[::-1])[::-1])
   from fractions import Fraction
   for g,v in zip(GRID,adj):close(v,float(Fraction(block['enrichment'][str(g)]['adjusted_p_value'])))
   emit('cell',{'condition':c,'mechanism':m,'n':len(e),'aurc':a,'violations':count,'magnitude':mag,'aurc_CI':block['aurc_bootstrap_95_interval']});checked+=1
  # Reconstruct quantiles and the calibration/test discrepancy from UTSW parquet only.
  for variant in ['carried_over','refit']:
   source=frame(2,'conditions/'+('full' if variant=='carried_over' else c)+'.parquet',split='calibration');tv=T if variant=='carried_over' else temp(cal);cp=expit(source.logit.to_numpy(float)/tv);cy=source.label.to_numpy(int);tp=expit(f.logit.to_numpy(float)/tv)
   for alpha in [.05,.1,.2]:
    qhat=quantile(cp,cy,alpha);b=j['conformal'][c][variant][str(alpha)];testcov=float(np.mean(np.where(y==1,1-tp,tp)<=qhat));calcov=float(np.mean(np.where(cy==1,1-cp,cp)<=qhat));close(qhat,b['quantile'],2e-6);close(testcov,b['empirical_coverage']);close(calcov,b['calibration_empirical_coverage']);close(testcov-calcov,b['test_minus_calibration_coverage']);conformal.append([c,variant,alpha,qhat,calcov,testcov,testcov-calcov])
    rng=np.random.default_rng((10000 if variant=='carried_over' else 20000)+CONDS.index(c)*100+[.05,.1,.2].index(alpha));values=[]
    for _ in range(2000):
     ci=rng.integers(0,len(cy),len(cy));qdraw=quantile(cp[ci],cy[ci],alpha);ti=rng.integers(0,len(y),len(y));values.append(float(np.mean(np.where(y[ti]==1,1-tp[ti],tp[ti])<=qdraw))-(1-alpha))
    close(interval(values),[b['coverage_deviation_bootstrap'][x] for x in ['lower','upper']])
 emit('bootstrap_and_permutation_recomputed',{'cells':36,'patient_bootstrap_iterations':2000,'risk_intervals':180,'monotonicity_intervals':36,'permutation_tests':180,'permutations_each':10000,'BH_grid_adjustments':180,'two_stage_conformal_intervals':36})
 emit('grid_checks',{'curves_and_aurc_and_monotonicity':checked,'selective_risk_and_rejected_correct':rejected,'enrichment_observed_difference':enrichment,'max_aurc_difference':maxdiff})
 emit('conformal_quantiles_cal_test',conformal)
 def worst(states): return max(states,key=lambda x:{'supported':0,'inconclusive':1,'refuted':2}[x])
 def risk_status(c):
  ops=j['conditions'][c]['M5']['selective_risk_at_coverage'].values()
  return 'refuted' if any(v['D_phi']['point']>=0 for v in ops) else ('supported' if all(v['D_phi']['upper']<0 for v in ops) else 'inconclusive')
 def c5_status(c):
  ops=j['conditions'][c]['M5']['adjacent_grid_risk_differences']
  return 'refuted' if any(v['lower']>0 for v in ops) else ('supported' if all(v['point']<=0 for v in ops) else 'inconclusive')
 def c6_status(c):
  from fractions import Fraction
  ops=j['conditions'][c]['M5']['enrichment'].values()
  return 'refuted' if any(v['observed_difference']<=0 for v in ops) else ('supported' if all(float(Fraction(v['adjusted_p_value']))<.05 for v in ops) else 'inconclusive')
 expected={'C1':risk_status('full'),'C2':worst([risk_status(c) for c in CONDS[1:]]),'C4':'refuted' if any(b['coverage_deviation_bootstrap']['half_width']>.07 for c in CONDS for b in j['conformal'][c]['carried_over'].values()) else 'supported','C5':worst([c5_status(c) for c in CONDS]),'C6':worst([c6_status(c) for c in CONDS])}
 actual={k:v.get('worst_status',v.get('status')) for k,v in j['claims'].items()}
 for k,v in expected.items(): assert v==actual[k],(k,v,actual[k])
 emit('independently_adjudicated_claims',expected)
 emit('claims',actual)
 emit('M5_drop_t1ce',{'risks':j['conditions']['drop_t1ce']['M5']['selective_risk_at_coverage'],'enrichment':j['conditions']['drop_t1ce']['M5']['enrichment']})
def show(tag, filename, start, end):
    lines=Path(filename).read_text().splitlines()
    emit(tag, [f"{filename}:{i+1}: {line}" for i,line in enumerate(lines) if start<=i+1<=end])
def decision(key):
    text=Path('docs/research/DECISION_LOG.md').read_text()
    sections=text.split('\n## ')
    emit(key,next(x for x in sections if x.startswith(key+' ')))

phase09()
decision('D-035');decision('D-050')
show('negative_log','paper/NEGATIVE_RESULTS.md',1,30)
show('analysis_json_write','src/glioma_selective/evaluation/phase09_analysis.py',882,900)
emit('negative_log_git',subprocess.run(['git','log','-1','--format=%h %ad %s','--date=iso','--','paper/NEGATIVE_RESULTS.md'],capture_output=True,text=True).stdout)
emit('first_results_commit',subprocess.run(['git','log','--reverse','--format=%h %ad %s','--date=iso','--','docs/research/protocols/PHASE09_INTERNAL_RESULTS.md'],capture_output=True,text=True).stdout)

```
