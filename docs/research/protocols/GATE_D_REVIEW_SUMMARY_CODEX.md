# Gate D independent review — Phases 06–10

Review task status: **DONE_WITH_CONCERNS**. Overall Gate D verdict: **not passed**.

Reviewed 2026-11-18 at `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`. Codex is independent of the phase author. **This is D-001’s degraded solo fallback: a second agent, not a second human.** It does not certify that a human Person C performed a review or that the Research Lead signed a freeze. No phase state or decision entry was edited.

Every one of the 52 numbered acceptance criteria has an individual met / not met / cannot tell verdict, exact executed command, trimmed output, and comparison in the phase reports. Each report embeds its read-only checker, so the recorded command remains executable without this session’s temporary scripts.

| Phase | Met | Not met, literally | Cannot tell | Gate D verdict | Report |
|---|---:|---:|---:|---|---|
| 06 | 11 | 0 | 0 | Pass with concerns: lifecycle metadata and historical GPU limitations | [Phase 06](GATE_D_REVIEW_PHASE06_CODEX.md) |
| 07 | 7 | 3 | 0 | Fail: required calibration-isolation test absent; two D-058 exceptions accepted by Lead | [Phase 07](GATE_D_REVIEW_PHASE07_CODEX.md) |
| 08 | 7 | 0 | 1 | Hold: D-012 remains OPEN and blocking | [Phase 08](GATE_D_REVIEW_PHASE08_CODEX.md) |
| 09 | 9 | 2 | 1 | Fail: same-day negative-results log missing; historical ordering unverified | [Phase 09](GATE_D_REVIEW_PHASE09_CODEX.md) |
| 10 | 8 | 3 | 0 | Hold: finality/literature incomplete; literal commitment and BH requirements need recorded dispositions | [Phase 10](GATE_D_REVIEW_PHASE10_CODEX.md) |

“Not met, literally” includes approved staged exceptions and contradictory wording; the findings distinguish them from implementation defects. This review does not revoke D-035, D-051, D-052, D-057 or D-058 and does not invent permission to access external data to satisfy a deferred criterion.

## Ranked findings

Rank is the order for Research Lead disposition. High means an unresolved acceptance/governance failure; medium means a validation/provenance gap; low includes approved exceptions and metadata/documentation defects. An observed negative result is never ranked as a software defect.

| Rank | ID | Severity | Phase / criterion | Finding and exact evidence | Required disposition |
|---:|---|---|---|---|---|
| 1 | F03 | High | 09 / 12 | `paper/NEGATIVE_RESULTS.md:21–26` is still an empty table and says no claim has been evaluated. Its last Git change is `c0c6f00` on 2026-09-11. The frozen Phase 09 file refutes C2/C4/C6, and results were committed by `4ca025a` on 2026-11-14. Draft entries in another document do not meet this criterion. | Human owner records findings with truthful discovery and delayed-entry dates; acknowledge that the same-day deadline was missed. Do not rewrite the scientific results. |
| 2 | F01 | High | 07 / 3 | Code fits on calibration arrays, and independent frozen-file fits agree. However, the required test asserting isolation of **every** fitted T, conformal quantile and CRC threshold is absent. `tests/unit/test_internal_analysis.py:39–50` makes both splits identically ordered; its positive test at line 73 would not detect fitting T on the wrong split. `test_condition_analysis.py:118` tests carried/refit differences, not invariance to test-label/logit changes. | Assign a targeted calibration-isolation regression test. This is missing acceptance coverage, not evidence of actual leakage. |
| 3 | F02 | High | 08 / 8; prior-phase prerequisite | `DECISION_LOG.md:186–199` still marks D-012 OPEN, Blocking: yes, resolve by Phase 03. The frozen UTSW inventory records 625 complete / 0 incomplete. D-057 defers EGD but does not explicitly resolve D-012’s inclusion/reporting policy or current-study non-applicability. External data were not inspected to settle it. | Research Lead resolves current-study applicability and the future EGD policy explicitly. UTSW has no natural-missingness subgroup to analyze. |
| 4 | F11 | Medium | 10 / scientific validation 3, criterion 11 | `PHASE10_LITERATURE_SANITY_CHECK.md:5` expressly says search snippets only, full texts unopened, all quoted literature numbers unverified under D-010. The claimed implementation sanity check therefore remains unverified. Earlier unresolved criteria also prevent certification that everything internal is final. | Verify the primary full texts and cohort/metric definitions, then record final internal disposition. Agent recomputation cannot supply a human signature. |
| 5 | F04 | Medium | 09 / 10 | SHA-verified JSON and JSON-first code exist, but synchronized artifacts carry no immutable event trace proving that **every historical** table/figure followed JSON creation. Present source structure and a document’s Git date do not prove universal historical timing. | Supply original generation/event provenance or record the inability to establish the timing requirement. Do not fabricate timestamps. |
| 6 | F09 | Medium | 10 / 10 | Actual `phase09_analysis.json`, `phase09_m6_analysis.json` and `phase10_analysis.json` are machine-readable on the SSD with sidecars; `git ls-files` for those exact basenames returns empty. Hash references/results documents are committed. This obeys the artifact policy while failing the literal “statistics ... committed” wording. | Lead clarifies the approved representation (versioned hash/pointer plus immutable external artifact). Do not commit patient artifacts as a workaround. |
| 7 | F12 | Medium, review limit | Gate A verification | Unit run excluded six files that exercise the external-authorization flag, to obey the user’s requirement that it remain unset. Of the remaining tests, 966 passed and one skipped because sandboxed PyTorch worker shared memory is unavailable. Reference suite: 83 passed. This is not a full Gate A/B pass. | Run the complete repository gate in an appropriately governed environment if a full-gate certification is required; preserve this review’s narrower evidence label. |
| 8 | F05 | Low, approved staging | 10 / 6 | Full 29-member BH correction is absent: 14 UTSW raw p-values computed, 15 external rows pending. Family matches the Lead-confirmed SAP membership; the supplementary 14-member correction independently reproduces. D-052 explicitly stages the full pass to Phase 13 after Phase 12. | Preserve the approved deferred duty. Do not call the supplementary correction the pre-registered correction and do not access external labels now. |
| 9 | F06 | Low, approved negative findings | 07 / 5–6 | Original ±2pp coverage fails 3/6 R1/R2 cells. ECE increases R1 .186323→.191225 and R2 .118866→.122161, while Brier improves. Independent calculations and the 1,000-replication check reproduce the evidence. `DECISION_LOG.md:1385` accepts both D-058 exceptions. | Record “not met as written, exception accepted”; preserve/report the negative findings without refitting. F03 also applies to the ECE negative-log duty. |
| 10 | F07 | Low, approved-rule/wording mismatch | 09 / 11 | Criterion says explicit support/refute with no hedging, while the correctly rederived C5 status is inconclusive. Frozen D-035/D-050 rules expressly allow that third outcome. C1 supported, C2/C4/C6 refuted all reproduce. | Explicitly reconcile the phase wording with the already-approved pre-result rule. Do not change the rule after seeing results. |
| 11 | F08 | Low | 06 / 10 lifecycle caveat | R1/R2 records have all 22 mandatory flattened keys, non-null protocol values, completed status and `git_dirty=false`, but `end_time_utc=null`. That field is outside the protocol’s 20 grouped requirements; criterion 10 passes. | Preserve the lifecycle gap as historical provenance. No invented completion time. |
| 12 | F10 | Low | Author readiness / status prose | `GATE_D_READINESS_PHASES_07_10.md:30` claims 108 main cells and 18 M6 cells; the frozen **internal** grid is 30 main computed + 6 companion M6 = 36. D-058’s original Status line and Phase 07’s trailing “decision ... owes” are stale despite its dated resolution; D-057 and family confirmation also supersede earlier open prose. | Treat the dated decisions and derived grid as evidence; reconcile stale prose separately. No result recomputation is needed to fix wording. |

F01–F04/F11 are not repaired by the author readiness table. F05/F06 have explicit Lead-approved dispositions; they remain literal unmet criteria, not newly discovered permission requests. F07/F09 concern a mismatch between requirements and an adopted protocol/policy. No source/config/result/doc outside these six review files was edited to make an item pass.

## Independent numerical evidence

- Parameter count: **18,815,144**, rebuilt on CPU.
- R1/R2 authorization reports: all seven historical steps passed; actual checkpoint hashes and prediction sidecars match. R1’s recorded/freeze SHA mismatch is explicit under D-044; R2’s SHAs agree.
- Baseline paired metrics, independently derived from frozen UTSW rows:

| Run | AUROC [Phase 06 bootstrap 95%] | AUPRC | ECE raw | Brier raw | AURC, full | Coverage, always predict |
|---|---|---:|---:|---:|---:|---:|
| R1 | .871910 [.797023,.932591] | .742976 | .186323 | .171226 | .134258 | 1.0 |
| R2 | .878331 [.803616,.935118] | .778231 | .118866 | .139927 | .075534 | 1.0 |

- The Phase 06/10 bootstrap interval discrepancy is explained, not left open: preserving original parquet row order reproduces Phase 06 exactly; sorting patients reproduces Phase 10’s R2 [.807611,.938666]. Both use 2,000 draws, seed 0. A seeded bootstrap is sensitive to index ordering even though the statistic is permutation-invariant.
- New reviewer code independently reconstructs **36 curves/AURCs**, all **180** fixed-coverage risk/rejected-correct/enrichment operating points, **36 AURC** and **36 monotonicity** bootstrap intervals, all **180** risk and paired D(phi) intervals, **180** seeded 10,000-permutation tests and their grid BH adjustments, and **36** two-stage conformal bootstrap intervals/quantiles/discrepancies. Maximum AURC point discrepancy is approximately **5.56e-17**.
- The separate author-supplied Person C pack was executed: **188 of 188** covered Phase 10 numbers agree. Running that pack alone would not constitute a new independent implementation; it is supplemented by the reviewer derivations and existing separate references. It was not run by a second human in this review.
- Probe: an independent SciPy optimization of the fixed frozen-feature objective gives 75.623632527706 against stored 75.623632527700; AUROC/AUPRC rankings agree. Test n=66, codeleted=14; IDH-mutant-only n=28. No inferential claim is made.
- HD95 counts/means were independently reaggregated from frozen per-patient outcomes. Dice reporting was checked from verified files. No fresh segmentation inference or encoder-feature extraction was run.
- R8 stage 1 `01M7ETEEYVT8KXCVJSQS5R7KJC` is explicitly linked by its stage-2 record; its actual checkpoint hash agrees. D-051 counts its two stages as one run-budget item: eight named R1–R8 configurations, nine actual training stages. No architecture search was performed.

These checks found no discrepancy in the numerical quantities they cover. They do not establish GPU reproducibility, historical JSON/table creation order, external performance, full-text literature facts or a human sign-off. Live CUDA availability on this Mac is false. Where a new hardware measurement would be needed, the phase reports identify the required GPU run; existing authorization outcomes are labelled historical.

## Commands and gate scope

All phase checkers use the requested interpreter, `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`, `PYTHONPATH=src`, and assert that `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` is absent. Artifacts/manifests were resolved through `utils/paths.py`. Frozen inputs were only opened for reading. No pip install, download, external label access, GPU run or IDH refit occurred.

The exact numerical/source commands, including the embedded reviewer code, are in each criterion’s phase report. Additional shared commands actually run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/check_invariants.py
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/check_conformal_exchangeable.py --run-id 01M46999FB083AX4WW0067YM13 --reps 1000 --seed 0
```

Trimmed outputs: `966 passed, 1 skipped, 1 warning`; `83 passed`; `Repository invariant check passed.`; `188 of 188 numbers agree`; exchangeability synthetic means .953/.905/.801, pooled R2 means .953/.905/.801 with SD .027/.038/.050. The exact replication output is also in Phase 07 criterion 5.

Gate D is the purpose of this review. Gate A applies to any report commit; the restricted test run is not the complete Gate A suite. Gate B (merge) and Gate C (new scientific run) were not applicable actions here. No merge/push or new scientific run was attempted.

## Delivery state

Git staging was attempted with exactly the six report paths:

```sh
git add docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md docs/research/protocols/GATE_D_REVIEW_SUMMARY_CODEX.md
```

Output: `fatal: Unable to create '/Users/aniketsaha/4th_Year/Glioma/.git/worktrees/codex-gate-d/index.lock': Operation not permitted`.

The worktree index is outside the permitted writable root. No commit was created, no hook was bypassed, and the six reports remain untracked. No permission escalation or alternate index was attempted. `git diff --name-only` is empty; `git status --short` lists only these six new reports.

Report-only pre-commit was run from the existing cached hook environments without installing packages. Its first run fixed trailing whitespace in two allowed reports and flagged a truncated quote fragment and an unused checker variable; these report-only issues were corrected. Final report-only hook command:

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/pre-commit run --files docs/research/protocols/GATE_D_REVIEW_PHASE06_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE08_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE09_CODEX.md docs/research/protocols/GATE_D_REVIEW_PHASE10_CODEX.md docs/research/protocols/GATE_D_REVIEW_SUMMARY_CODEX.md
```

Exit 0. Trailing whitespace, end-of-file, large-file, codespell and secret checks passed; YAML/TOML/ruff hooks had no applicable files. This is a report-only hook pass, not the full all-files pre-commit or full Gate A/B lane.

Next action: Research Lead reviews the ranked findings, closes or explicitly accepts the unresolved criteria, and records phase/Gate D dispositions before considering Gate E.
