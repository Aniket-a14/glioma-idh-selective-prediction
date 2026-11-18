# NEGATIVE RESULTS LOG

**Written the moment a claim is refuted, not at write-up time.** This is the
practical defence against retroactively softening a result after seeing it
(`docs/research/PUBLICATION_PLAN.md` §5). Ships in the manuscript exactly as
recorded here.

**Standing rule** (`docs/research/README.md`, `MASTER_RESEARCH_EXECUTION_PLAN.md`
§4): if selective prediction fails under shift — non-monotonic risk–coverage
curves, coverage collapse, calibration degradation — that is the finding, and
it is publishable. **No experiment is re-run, re-tuned, or re-scoped because
its outcome refutes a claim.**

Every pre-registered falsification condition a result can trigger is listed
in `docs/research/SPEC_TRACEABILITY_MATRIX.md` Part 2, verbatim, against
C1–C6. When a run's result meets one, it is entered below **before** any
further analysis on that claim continues.

## Log

| Date found | Claim refuted | Refutation criterion met (verbatim, SPEC §1.4) | Cohort / condition | Evidence artifact | Phase | Reported at |
|---|---|---|---|---|---|---|
| 2026-11-14 | C2 | "Selective-risk advantage over always-predict disappears or reverses when 1–2 sequences are dropped." | UTSW internal test, simulated `drop_t1ce`: D(phi) = 0.012, 0.048, 0.065, 0.054, 0.016 at phi 0.9 to 0.5 (positive means worse than always-predict) | `phase09_analysis.json`, run `01M46999FB083AX4WW0067YM13`, SHA-256 `99f48c7dd3069fc657f15f1009c0d6628fbe5369b9f79e96259de420f99dc3e9`, `claims.C2.drop_t1ce` | 09 | Not yet in the manuscript |
| 2026-11-14 | C4 | "The deviation cannot be reliably characterized — e.g., empirical coverage estimates are too noisy/unstable (given sample size) to distinguish 'coverage preserved' from 'coverage degraded' at the pre-registered tolerance." | UTSW internal test, all six conditions (five simulated-missing), alpha 0.05, 0.1, 0.2: deviation-interval half-widths 0.065 to 0.222 against the frozen 0.07 band; 1 of 18 cells meets it; labels: 0 preserved, 2 degraded (`drop_t1ce`, alpha 0.1 and 0.2), 16 indeterminate | same file, `claims.C4` | 09 | Not yet in the manuscript |
| 2026-11-14 | C6 | "Abstained cases are no more likely to be erroneous than randomly selected cases of equal size." | UTSW internal test, simulated `drop_t1ce`: observed enrichment -0.116, -0.199, -0.154, -0.083, -0.016 at phi 0.9 to 0.5 (all at or below 0) | same file, `claims.C6.drop_t1ce` | 09 | Not yet in the manuscript |
| 2026-10-09 (numbers first produced); 2026-11-17 (recognized as an unmet acceptance criterion, D-058) | Phase 07 acceptance criterion 6, not a C-claim: "Temperature scaling reduces internal-test ECE relative to raw softmax." | The criterion text as written in `PHASE_07_CALIBRATION_UNCERTAINTY.md` | UTSW internal test, 10-bin ECE raw to scaled: R2 0.118866 to 0.122161, R1 0.186323 to 0.191225 (not lowered); Brier improves slightly; paired difference D1 on R2 = -0.0033, 95% interval (-0.028, 0.022), raw p 0.67; fitted temperature 1.125 | `internal_analysis.json` (R1, R2) and `phase10_analysis.json` (SHA-256 `3d2a220c49b558a543833057514ea65f733a80f5e49aa04411fd776ffd271f54`); `DECISION_LOG.md` D-058, resolved as an accepted exception, no refit | 07 | Not yet in the manuscript |

**Late entries.** The standing rule above requires an entry the day a claim is refuted. These four rows were entered on 2026-11-18, after the Phase 09 results were frozen on 2026-11-14 and after the ECE result was recognized on 2026-11-17; the same-day rule was missed. The dates in the first column are the dates the results were found, not the date of entry. No result or criterion was changed in the meantime. The independent Gate D review flagged the empty log (finding F03, `docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md`).

**Also on record, not refutations.** C1 is supported on the internal data. C5 is inconclusive under the frozen rule (D-035, D-050), which allows a third outcome. Phase 07 criterion 5 (conformal coverage within +/-2 pp on every alpha) was not met as written on one 124-patient split (3 of 6 R1/R2 cells outside); a 1000-replication check shows the conformal code is correct and a single split scatters by 2.5 to 5 pp (D-058, accepted exception). The external-cohort claims (C3 and the external halves of C4, C5, C6) are not evaluated here; entries for them are made the day each is adjudicated.
