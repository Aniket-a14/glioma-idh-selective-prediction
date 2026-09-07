# Phase 13 — Final Statistics, Figures, Tables, and Results Freeze

**Duration:** ~10 days · **Gate:** F · **Compute:** CPU

## Scientific purpose
Assemble the complete evidence base, apply multiplicity correction across the full family, and freeze every result so that the manuscript is written from immutable artifacts rather than from memory or a notebook.

## Engineering purpose
Generate every figure and table from frozen result files by code, and prove it by regenerating them from scratch.

## Specification requirements satisfied
SPEC §5.2 (metric hierarchy preserved), §5.5 (full statistical protocol), §5.3 (honest power reporting), §5.4 (edge-case reporting incl. rejected-but-correct rate), §9 step 9.

## RQs / claims addressed
All. This phase produces the final answer to every RQ and the final adjudication of every claim.

## Entry criteria
Phase 12 complete; external artifacts frozen; internal results final since Phase 10.

## Inputs
All frozen prediction artifacts (internal + external); all statistical results; the pre-registration; the statistical analysis plan.

## Tasks

| ID | Objective | Owner | Solo fallback | Executor | Compute | Parallel | Blocks |
|---|---|---|---|---|---|---|---|
| T13.1 | Combine internal + external into the full result set (108 cells) | A | — | Codex | CPU | no | T13.2 |
| T13.2 | Apply BH across the **complete** pre-registered family | A | — | Claude | CPU | no | T13.3 |
| T13.3 | Final adjudication of C1–C6, internal and external | A | — | Claude | CPU | no | T13.6 |
| T13.4 | Figures 1–5 generated from frozen results | A | — | Codex | CPU | yes | T13.7 |
| T13.5 | Tables 1–6 and Supplementary S1–S4 generated from frozen results | C | A+Codex (+5d) | Codex | CPU | yes | T13.7 |
| T13.6 | Answer RQ1–RQ4 explicitly, in writing, with artifact references | A | — | Claude | none | no | Phase 14 |
| T13.7 | **Regeneration test**: delete and rebuild all figures/tables | A | — | Codex | CPU | no | Gate F |
| T13.8 | Figure and table registry | C | A (+2d) | Codex | none | yes | Phase 14 |
| T13.9 | Independent verification of every reported number | C | A+Codex (+5d) **DEGRADED** | Human | CPU | no | Gate F |
| T13.10 | Freeze results; hash; tag the repository | A | — | Human | none | no | Phase 14 |

**T13.3 — adjudication is mechanical.** Each claim is compared against its verbatim refutation criterion. **Refuted claims are reported as refuted**, in the abstract if they are primary. No hedging language ("trends toward", "suggests a possible"), no re-framing to make a refutation sound like partial support.

**T13.7 — the regeneration test.**
```bash
rm -rf paper/figures paper/tables
python -m glioma_selective.cli.build_paper_artifacts
git diff --stat paper/   # must be empty or numerically identical
```
**A figure that cannot be regenerated does not go in the paper.**

**T13.9 — independent verification.** C takes the frozen artifacts and independently recomputes every number that appears in a table or figure. Under solo fallback, Codex recomputes from the specification text with a separate implementation. This is DEGRADED solo and disclosed if so.

## Human allocation
**A:** adjudication, RQ answers, freeze. **C:** owns table verification, figure validation, and independent number-checking — C's largest contribution. **B:** none.

## Claude tasks
T13.2, T13.3, T13.6 — statistical judgement and claim adjudication.

## Codex tasks
T13.1, T13.4, T13.5, T13.7, T13.8 — generation and verification tooling.

## Parallelization map
```
T13.1 ─> T13.2 ─> T13.3 ─> T13.6 ─┐
T13.4, T13.5, T13.8 (parallel) ───┼─> T13.7 ─> T13.9 ─> T13.10
```

## Worktrees / branches
```
agent/codex/p13-figures-tables      agent/claude/p13-adjudication
```

## Files / modules expected
`src/glioma_selective/visualization/{risk_coverage,reliability,coverage,abstention}.py`, `src/glioma_selective/cli/build_paper_artifacts.py`, `paper/figures/`, `paper/tables/`, `paper/REGISTRY.md`, `results/final/*.json`.

## Data required
Frozen artifacts only. No image data, no GPU.

## Compute required
CPU, minutes.

## Outputs / artifacts
Complete result set (108 cells) · BH-corrected results across the full family · **final adjudication of C1–C6** · explicit written answers to RQ1–RQ4 · Figures 1–5 and Tables 1–6 plus supplementary · figure/table registry · regeneration-test evidence · **frozen, hashed, tagged results.**

## Tests
Figure generation: every figure builds from frozen results with no manual input; regeneration is deterministic; **no figure code reads a model checkpoint** (asserted — figures come from artifacts, not models).
Table generation: every number traces to a result file; `SI-14` enforcement — the table builder refuses to emit AUROC without ECE, Brier, AURC, and coverage alongside.

## Quality gates
**GATE F — results freeze.** Result artifacts immutable · statistical scripts finalized · figures and tables reproducible · every claim traces to evidence.

## Scientific validation
1. Every number in every table traces to a result file, which traces to a prediction artifact, which traces to a run record, which traces to a manifest, which traces to a raw patient ID — **the complete §19 provenance chain, spot-checked end to end on at least three numbers.**
2. Independent verification by C.
3. Regeneration test passes.
4. Claim adjudication reviewed against verbatim criteria by someone other than the adjudicator.

## Acceptance criteria
1. All 108 result cells present, or absence justified in writing.
2. BH applied across the complete pre-registered family; family membership matches Phase 05.
3. C1–C6 adjudicated with support/refute stated plainly for internal and external conditions.
4. RQ1–RQ4 answered explicitly in writing with artifact references.
5. All figures and tables generated from frozen results by code; none hand-edited.
6. **Regeneration test passes** — delete and rebuild produces identical output.
7. Independent verification complete; every discrepancy resolved.
8. Provenance chain spot-checked end-to-end on ≥3 numbers.
9. Every refuted claim appears in `NEGATIVE_RESULTS.md`.
10. Metric hierarchy preserved — **no AUROC reported without ECE/Brier/AURC/coverage** (SI-14).
11. Wide CIs at coverage extremes reported honestly, not hidden by grid coarsening.
12. Results frozen, hashed, and the repository tagged `results-freeze`.

## Failure conditions
Regeneration test fails → the figure pipeline is not reproducible; fix before Gate F · a number cannot be traced to an artifact → find its provenance or **remove it from the paper** · independent verification finds a discrepancy → resolve before freezing · a claim's adjudication is ambiguous → return to the verbatim criterion; if it is genuinely ambiguous, that ambiguity is itself reported.

## Rollback / recovery
Results recompute from frozen prediction artifacts. The freeze is a tag, not a deletion, so a corrected analysis produces a new tag with a decision-log entry.

## Risks
R-S01–R-S06 (all scientific outcomes surfacing here) · R-M02 (if C is unavailable, verification is DEGRADED and disclosed) · the temptation to soften a refuted claim — **guarded by verbatim criteria and by `NEGATIVE_RESULTS.md` having been written when the refutation occurred, not now.**

## Decisions requiring Research Lead approval
Which results are primary vs. supplementary · whether any result is excluded from the paper (**requires strong justification and a decision-log entry**) · figure design choices affecting interpretation (axis ranges, CI display).

## Exit criteria
All acceptance criteria met; **Gate F passed**; results frozen, hashed, tagged.

## Dependencies for next phase
Phase 14 writes only from these frozen artifacts.
