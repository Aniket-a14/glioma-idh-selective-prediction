# LABEL DEFINITIONS

Phase 03 T03.6 (SPEC §5.7): IDH status "must be defined identically... across UTSW, UCSF-PDGM,
and EGD before pooling any statistics," with cohort-specific assay/era differences "flagged as a
potential source of label heterogeneity, not silently normalized away."

**This task is judgement work and degrades under solo operation** (`PHASE_03_LEAKAGE_AUDIT.md`
§ "T03.6 is judgement work"). No Person C exists to independently cross-check this document per
D-001's team model — it is executed solo (Claude), and that fact is disclosed in
`paper/LIMITATIONS.md`, not hidden. What follows is grounded in the actual downloaded metadata
files (verified, not assumed) plus the cohorts' published methodology papers where the file itself
doesn't state assay method — the two are clearly distinguished below.

---

## 1. UTSW-Glioma — verified directly from `UTSW_Glioma_Metadata-2-1.tsv`

**IDH determination.** The file itself records the assay per patient (`IDH_Testing Method`
column) — this cohort is **not** assayed by a single uniform method:

| IDH result | Tested by IHC | Tested by NGS | Total |
|---|---|---|---|
| mutated | 104 | 72 | 176 |
| wild type | 309 | 137 | 446 |
| NA (untested/unlabeled) | — | — | 3 |

**176 mutated + 446 wildtype = 622, matching the SPEC's claimed IDH n=622 exactly, and the 3 `NA`
rows are the literal source of the SPEC's own "625 patients but IDH n=622" gap D-009 flagged as
unexplained** — resolved here as a direct file finding, not an assumption: those 3 patients simply
have no IDH result recorded in the source metadata.

**This is real within-cohort assay heterogeneity**, not a cross-cohort issue: 413/622 labeled
patients (66%) were assessed by immunohistochemistry (IHC — typically an IDH1 R132H-specific
antibody stain, the most common mutation), 209/622 (34%) by next-generation sequencing (NGS,
which can detect the full range of IDH1/IDH2 variants IHC alone would miss). IHC-only assessment
can under-call non-R132H variants as wildtype. This is flagged, not normalized away, per SPEC
§5.7's explicit instruction — a patient's IDH label carries a different false-negative risk
depending on which assay produced it, and that's now a documented, queryable fact
(`IDH_Testing Method`) rather than an invisible one.

**1p/19q** (`1p19Q CODEL` column): `co-deleted` (63) / `non co-deleted` (272) / `NA` (290) — 63
codeleted matches the SPEC's claimed count exactly. **MGMT** (`MGMT` column, not a study endpoint
— recorded for completeness only): `methylated` (114) / `unmethylated` (167) / `NA` (344).

## 2. UCSF-PDGM — verified directly from `UCSF-PDGM-metadata_v2.csv`

**IDH determination.** The metadata file does not carry a per-patient assay-method column the way
UTSW's does, but the **IDH values themselves are specific molecular variants**, not a simple
binary — `IDH1 p.R132H` (54), `IDH1 p.R132C` (8), `IDH1 p.R132G` (5), `IDH1 p.R132S` (2),
`IDH1 p.Arg132His` (1), `IDH2 p.R172K` (1), `IDH2 p.Arg172Trp` (1), `mutated (NOS)` (31,
"not otherwise specified" — presumably a positive IHC screen without a follow-up variant-level
sequencing result), and `wildtype` (398). Variant-level resolution (R132H vs. R132C vs. R132G,
etc.) is only obtainable from sequencing, not a single-antibody IHC stain — so the specific-variant
rows are evidence this cohort's mutant-positive cases were sequenced, not just IHC-screened,
**inferred from the label granularity itself, not independently confirmed against the original
UCSF-PDGM publication's stated methods** (Calabrese et al., *Radiology: AI* 2022) — that
independent confirmation did not complete during this pass (a paper PDF fetch failed to render
readable text) and is flagged here as an open gap rather than silently assumed. Canonical mutant
count: 31+54+8+5+1+2+1+1 = **103** mutated, 398 wildtype (matches the file exactly; no blank/NA
IDH rows — consistent with TCIA's own statement that IDH status is recorded for all 501 patients).

**1p/19q** (`1p/19q` column): values are `intact` (395), `co-deletion` (6), `relative
co-deletion` (6), `Co-deletion` (3, differently capitalized — **a literal spelling
inconsistency within this single file**, not a semantic difference), blank (91). Codeletion-like
total (any spelling) = 15; combined with the 395 `intact` = 410 labeled, matching the SPEC's
claimed "1p/19q for 410/501" exactly.

**MGMT status** (not a study endpoint, recorded for completeness): `positive` (302, methylated),
`negative` (114, unmethylated), `indeterminate` (5), blank (80).

## 3. EGD — not yet available

EGD has not been downloaded (its DUA is pending, `DATA_ACCESS_LOG.md`). Its labeling methodology
per the SPEC's citation (van der Voort et al., *Data in Brief* 2021) is not independently verified
here and will be added to this document once the cohort itself arrives and its metadata can be
read directly, same standard as the two sections above — not filled in from the paper alone
without a file to check it against.

---

## 4. Cross-cohort harmonization mapping

The canonical vocabulary used everywhere downstream of this document:

| Canonical | UTSW-Glioma source value(s) | UCSF-PDGM source value(s) |
|---|---|---|
| `IDH_MUTANT` | `mutated` | `IDH1 p.R132H`, `IDH1 p.R132C`, `IDH1 p.R132G`, `IDH1 p.R132S`, `IDH1 p.Arg132His`, `IDH2 p.R172K`, `IDH2 p.Arg172Trp`, `mutated (NOS)` |
| `IDH_WILDTYPE` | `wild type` | `wildtype` |
| `IDH_UNLABELED` | `NA` | (none observed) |
| `1P19Q_CODELETED` | `co-deleted` | `co-deletion`, `Co-deletion`, `relative co-deletion` |
| `1P19Q_NONCODELETED` | `non co-deleted` | `intact` |
| `1P19Q_UNLABELED` | `NA` | blank |
| `MGMT_METHYLATED`* | `methylated` | `positive` |
| `MGMT_UNMETHYLATED`* | `unmethylated` | `negative` |
| `MGMT_INDETERMINATE`* | (none observed) | `indeterminate` |
| `MGMT_UNLABELED`* | `NA` | blank |

\* MGMT is **not a study endpoint** (project invariant) — this mapping exists only so the
acquisition record is complete and consistent, never for use in a model or an analysis.

**A named policy decision this mapping makes, stated explicitly rather than left implicit:**
UCSF-PDGM's specific IDH1/IDH2 variant labels and its `mutated (NOS)` label are all folded into
one `IDH_MUTANT` category, matching UTSW's binary `mutated`/`wild type` granularity. This is the
correct choice for this project (RQ1–RQ3 and C1–C6 are framed as binary IDH mutant-vs-wildtype
throughout the SPEC, never variant-specific), but it does discard real information UCSF-PDGM
happens to provide — noted here so it's a visible choice, not a silent loss.

**Relative co-deletion (UCSF-PDGM, n=6)** is folded into `1P19Q_CODELETED` for consistency with
the binary framing UTSW's file provides, though "relative" co-deletion is arguably a distinct,
weaker signal than the file's own separately-reported `co-deletion`/`Co-deletion` rows. **Resolved
by the Research Lead (D-019, T03.7):** fold into `CODELETED`. 1p/19q is explicitly exploratory-only
per the project's own invariants and D-007, so the practical stakes of this classification are low;
no patient is excluded by it.

---

## 5. What this document does not do

Per the phase file's own scope boundary, this document defines the harmonized label vocabulary and
flags heterogeneity. The two concrete ambiguous cases it surfaced (UTSW's 3 no-IDH patients,
UCSF-PDGM's relative co-deletion) were resolved by the Research Lead in T03.7/D-019, recorded
above. This document does not build the exclusion manifest itself or compute post-exclusion class
counts (T03.10/T03.11) — those consume this document's mapping table and D-019's decisions as
input, not the other way around.
