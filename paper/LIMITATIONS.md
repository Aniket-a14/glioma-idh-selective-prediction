# LIMITATIONS LOG

Updated continuously as the project proceeds (`docs/research/PUBLICATION_PLAN.md`
§5), not reconstructed from memory before submission. Every entry traces to a
`docs/research/DECISION_LOG.md` decision or a phase's own finding — nothing is
added here without a recorded reason.

Pre-seeded at Phase 00 with limitations already known from the decision log,
before any code exists, because they were disclosure obligations from the
moment the corresponding decision was made — not findings to wait for.

## Known at Phase 00

| Source | Limitation | Manuscript disclosure obligation |
|---|---|---|
| **D-001** | Team model is one active contributor with Codex as an independent-implementation check standing in for a second human, not the three-person model the execution plan was written for. Two judgement-heavy tasks are consequently `DEGRADED`: MRI visual QC (Phase 04) and label-definition adjudication (Phase 03). | State explicitly in Limitations if either task is executed solo. |
| **D-008** | UTSW, UCSF-PDGM, and EGD are all curated, complete four-sequence cohorts. True missing-modality evaluation cannot be observed in them — it is **simulated** by zeroing a channel from a complete, high-quality study, which reproduces the information loss but not the real-world selection mechanism (motion artifact, patient intolerance, truncated protocol, scanner failure — all of which plausibly correlate with image quality or disease severity). | (i) A Limitations paragraph stating the construct-validity gap explicitly. (ii) Every missing-modality figure caption and table header carries the word "simulated". (iii) RQ1/C2's wording is **not** softened after the fact — the limitation is stated alongside the claim as pre-registered, not folded into it. |
| **D-012** | Naturally-missing sequences (if any are found in Phase 03) are excluded from the primary analysis to keep the patient set identical across all 18 evaluation conditions, and reported only as a small, explicitly underpowered natural-missingness sanity check. | State the exclusion count and reason (`missing:sequence`) in the exclusion manifest and cite the natural-missingness check as underpowered by construction, not as confirmatory. |

## Log

| Source | Limitation | Manuscript disclosure obligation |
|---|---|---|
| **Phase 03 T03.6 (D-001 DEGRADED task, realized)** | Label-definition harmonization across UTSW/UCSF-PDGM/EGD (`docs/research/protocols/LABEL_DEFINITIONS.md`) was executed solo — no independent second reviewer cross-checked the harmonization mapping, as D-001's three-person model assumed. | State explicitly that label-definition harmonization was performed by a single reviewer without independent cross-check. |
| **T03.6 finding** | UTSW-Glioma's IDH labels are assayed by two different methods within the same cohort — 413/622 (66%) by immunohistochemistry (IHC, which can under-call non-R132H variants as wildtype), 209/622 (34%) by next-generation sequencing. This is real within-cohort assay heterogeneity, not a data-entry artifact. | State the IHC/NGS split explicitly in the methods section; note the differential false-negative risk of IHC for non-R132H variants. |
| **T03.6 finding** | UCSF-PDGM's IDH assay methodology was not independently re-confirmed against the original publication (Calabrese et al. 2022) — the label granularity (specific variant names) implies sequencing, but this is an inference from the data, not a verified methods-section citation. | State this as an unverified inference if it appears in the manuscript's cohort description; do not present it as confirmed. |

*(Further entries append here as later phases surface them — e.g. cohort
verification discrepancies (D-009), RQ4's exploratory power limits (D-007),
or anything Phase 04's visual QC find. Each entry: source, limitation,
disclosure obligation.)*
