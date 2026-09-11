# FIGURE / TABLE REGISTRY

Populated as figures and tables are generated (`docs/research/PUBLICATION_PLAN.md`
§5, finalized at Phase 13). Every row must resolve before Gate F — an empty
`Generated from` or `Regenerate command` cell at that point is a blocking
defect, mirroring the reverse-trace closure rule in
`docs/research/SPEC_TRACEABILITY_MATRIX.md` Part 4, which is this table's
source list.

**Regeneration test** (master plan §10): at Gate F, delete `paper/figures/`
and `paper/tables/`, run each `Regenerate command` below, and confirm
byte-identical (or numerically identical) regeneration from the frozen
`results/` files named in `Generated from`. A figure or table that cannot be
regenerated this way does not go in the paper.

| Element | Content | Generated from | Regenerate command | Status |
|---|---|---|---|---|
| Fig 1 | Cohort flow diagram (CONSORT-style) | `manifests/*` | — | PENDING |
| Fig 2 | Risk–coverage curves, 2×2 (complete/missing × internal/external) | `results/c1.json c2.json c3.json c5_*.json` | — | PENDING |
| Fig 3 | Nominal vs. empirical coverage, per condition | `results/rq2_coverage.json` | — | PENDING |
| Fig 4 | Reliability diagrams, internal vs. external | `results/rq3_calibration.json` | — | PENDING |
| Fig 5 | Abstention–error enrichment | `results/c6.json` | — | PENDING |
| Table 1 | Cohort characteristics | `manifests/cohort_manifest.json` | — | PENDING |
| Table 2 | Exclusions with reasons | `manifests/exclusions_*.json` | — | PENDING |
| Table 3 | AURC + selective risk @ matched coverage, all mechanisms × conditions | `results/` | — | PENDING |
| Table 4 | Coverage deviation vs. ±5pp band | `results/c4.json` | — | PENDING |
| Table 5 | Discrimination + calibration (AUROC, AUPRC, ECE, Brier) | `results/` | — | PENDING |
| Table 6 | Abstention analysis incl. rejected-but-correct rate | `results/c6.json` | — | PENDING |
| Supp S1 | Ablations (six axes) | `results/ablations/` | — | PENDING |
| Supp S2 | Auxiliary segmentation Dice/HD95 | `results/segmentation.json` | — | PENDING |
| Supp S3 | 1p/19q exploratory | `results/rq4_*.json` | — | PENDING |
| Supp S4 | TRIPOD+AI and CLAIM 2024 checklists | `paper/checklists/` | — | PENDING |

**Status legend:** PENDING · GENERATED · REGENERATION-VERIFIED · FROZEN (Gate F).
