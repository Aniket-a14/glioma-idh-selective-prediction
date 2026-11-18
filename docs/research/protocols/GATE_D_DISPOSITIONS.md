# Gate D: disposition of the independent review findings (Phases 06 to 10)

Written 2026-11-18 by Claude. Source: `GATE_D_REVIEW_SUMMARY_CODEX.md` and the five phase reports. The review is the degraded solo fallback (D-001: a second agent, not a second human). **This file records what was done about each finding. It does not pass Gate D: the Research Lead does that.** Verdicts as reviewed: 06 pass with concerns, 07 and 09 fail, 08 and 10 hold.

| ID | Finding (short) | Disposition | Status |
|---|---|---|---|
| F01 | Phase 07 criterion 3: no test asserts every fitted parameter ignores the test split | Fixed. `tests/unit/test_calibration_isolation.py`: both analysis entry points run twice with the same calibration split and a different test split; temperatures, conformal quantiles and CRC thresholds must be identical; control runs change the calibration split and must change them. Mutation-checked: fitting on calibration plus test rows fails both entry-point tests. | Closed |
| F02 | D-012 still OPEN and blocking | Resolved on the log's own recommendation (alternative (a)); nothing applies to UTSW or UCSF-PDGM (0 naturally incomplete); same policy for the EGD addendum. Research Lead asked to confirm. | Closed, confirm |
| F03 | `paper/NEGATIVE_RESULTS.md` is empty; C2, C4, C6 refuted on 2026-11-14 and the ECE finding (D-058) are not entered | **Not done by me.** `paper/` is human-owned and the Research Lead parked the paper. Drafts exist at the end of `PHASE09_INTERNAL_RESULTS.md`. The same-day rule was missed; the entries must carry the true discovery dates and a note that they were entered late. | **Open, human** |
| F04 | No immutable trace that every historical table and figure followed its JSON | Cannot be established retroactively; recorded as a limitation, not fixed. The Phase 13 builders generate every figure and table from the sidecar-verified JSON, so the ordering holds from here on. No timestamps are invented. | Recorded |
| F05 | Full 29-member BH pass absent | Approved staging (D-052): runs once in Phase 13 after Phase 12. The 14-member supplementary pass is labelled supplementary. | Accepted, staged |
| F06 | Phase 07 criteria 5 and 6 unmet as written | Resolved as exceptions by D-058, accepted by the Research Lead 2026-11-18. | Closed |
| F07 | Phase 09 criterion 11 says "support or refute, no hedging"; C5 is "inconclusive" | The third outcome was fixed before results by D-035 and D-050; the phase file wording is superseded for C5 by that rule. The rule is not changed after seeing results. | Reconciled, confirm |
| F08 | R1 and R2 records have `end_time_utc = null` | Historical provenance gap; no completion time is invented. Criterion 10 passes (the field is outside the 20 required items). | Recorded |
| F09 | `phase09_analysis.json`, `phase09_m6_analysis.json`, `phase10_analysis.json` are not committed to git | By policy they are patient-level frozen artifacts on the storage root with sidecars; git holds their SHA-256 values in the results documents. "Committed" is read as hash pointer in git plus immutable artifact on storage. Research Lead to confirm that reading. | Reconciled, confirm |
| F10 | Stale prose (108 and 18 cell counts, D-058 status line, "decision owed") | Fixed 2026-11-18: 36 internal cells stated, D-058 marked resolved. | Closed |
| F11 | R7/R8 literature check unverified | Three sources checked against primary text (`PHASE10_LITERATURE_SANITY_CHECK.md`). Result: AUROC range consistent; no source is a controlled H1 or H2 comparison; GMMAS's "two-stage" is semi-supervised training stages. Full-text tables still unread; not needed for Gate D. | Closed for Gate D |
| F12 | The review's test run excluded six files that touch the Gate E flag, so it is not a full Gate A/B pass | Full gate run by me on main after the Phase 12 and 13 merges: 1167 passed, 8 skipped (EGD test and storage-dependent tests), mypy 96 files clean, ruff clean, invariants pass; then 1171 with the isolation tests. | Closed |

## What Gate D still needs from the Research Lead

1. F03: the human step on `paper/NEGATIVE_RESULTS.md`.
2. Confirm F02, F07 and F09 readings.
3. Sign Gate D per phase (the review does not substitute for the signature); the reviewer is an agent, which is disclosed in Limitations (D-001).
