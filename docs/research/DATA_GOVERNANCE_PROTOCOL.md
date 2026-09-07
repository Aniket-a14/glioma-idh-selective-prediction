# DATA GOVERNANCE PROTOCOL

The highest-risk area in the project. Patient-level leakage silently inflates every reported number and can invalidate the study if discovered after publication.

---

## 1. Provenance chain

Every number in the final paper traces backward through this chain without a gap. Any break is a Gate F failure.

```
raw patient ID (cohort, download date, source checksum)
  → ID normalization        (raw → private internal → public pseudonymized)
  → cross-dataset overlap audit
  → exclusion manifest      (a REASON per excluded patient, not just an ID)
  → final cohort manifest   (SHA-256, committed)
  → preprocessing           (version + parameter hash + per-volume content hash)
  → split manifest          (SHA-256, patient-level, stratified, FROZEN)
  → model input
  → prediction artifact     (run ID + git SHA + checkpoint hash)
  → statistical result      (frozen JSON)
  → manuscript table/figure cell
```

---

## 2. Per-cohort acquisition record

Recorded in `docs/research/protocols/DATA_ACCESS_LOG.md` for each of UTSW-Glioma, UCSF-PDGM, EGD:

source dataset version · download date · download method · source checksum where available · raw-file inventory (counts by type) · patient count · label counts per marker · modality counts · ambiguous labels · naturally missing sequences · corrupt volumes · duplicate scans · licence/DUA terms and what they permit · who downloaded it.

---

## 3. Identifier tiers — never mixed

| Tier | Example form | Where it may live |
|---|---|---|
| **Raw identifiers** | As shipped by the cohort | `data/private/` only. Used inside the audit. **Never committed.** |
| **Private internal IDs** | `UTSW-0001` | The join key across manifests. Committed only if the cohort's terms permit. |
| **Public pseudonymized IDs** | `P0001` | Released artifacts, the paper, the reproducibility package. |

The raw → private mapping lives in `data/private/id_map.json`, is never committed, never synced to the GPU server, and is excluded by `.gitignore` patterns on `*private*`.

**Restricted clinical metadata is not committed unless the dataset terms clearly permit it.** When in doubt, do not commit; the manifest can carry a hash instead of a value.

---

## 4. The overlap audit (Phase 03)

Every cell computed and its result recorded **even when empty** — "we checked and found nothing" is a result that must be evidenced.

```
                BraTS-2021   TCGA-GBM   TCGA-LGG   UCSF-PDGM   EGD
UTSW-Glioma         ?            ?          ?          ?         ?
UCSF-PDGM     MUST RESOLVE       ?          ?          —         ?
EGD                 ?            ?          ?          ?         —
```

**UCSF-PDGM ⇄ BraTS-2021 is not optional.** UCSF-PDGM ships a BraTS-2021 ID-mapping file *specifically* so overlapping cases can be excluded. Overlapping subject IDs are removed before the cohort counts as external. If BraTS-derived pretraining were ever used (see **D-011**, recommendation: don't), every subject ID also appearing in UCSF-PDGM, TCGA-GBM/LGG, or EGD must be excluded from BraTS first — otherwise the external claim for those cohorts is void.

**ID normalization must precede matching.** Cohorts differ in case, zero-padding, prefixes, and separators. Compare normalized forms *and* record the raw forms, so a match is auditable rather than asserted.

---

## 5. Exclusion vocabulary

Every excluded patient carries a machine-readable reason. Free text is not acceptable.

| Code | Meaning |
|---|---|
| `overlap:brats2021` / `overlap:tcga-gbm` / `overlap:tcga-lgg` / `overlap:ucsf` | Cross-dataset duplication |
| `label:missing` | No label for the endpoint |
| `label:ambiguous` | Conflicting or uncertain in the source record — **excluded, never imputed** (SPEC §5.4) |
| `label:definition-mismatch` | Assay/era incompatible with the harmonized definition (SPEC §5.7) |
| `missing:sequence` | Naturally incomplete four-sequence study (see **D-012**) |
| `qc:registration-failed` / `qc:skullstrip-failed` / `qc:corrupt` / `qc:orientation` | Preprocessing QC failure |
| `duplicate:scan` | Same patient, multiple studies — one retained, selection rule recorded |

---

## 6. Splitting rules

- **Patient-level only.** No slice-level splitting. No scan-level splitting where several scans belong to one patient.
- Split is computed **after** the overlap audit and de-duplication, never before.
- Stratified on the primary endpoint (IDH) — and the resulting 1p/19q balance is *reported*, not optimized for.
- UTSW only: train / calibration / internal test. UCSF-PDGM and EGD are never split; they are evaluated whole.
- Frozen at Phase 05 with a SHA-256 hash committed to Git. **Post-freeze changes require a Research Lead decision-log entry and invalidate every downstream result.**

---

## 7. Label harmonization (SPEC §5.7)

IDH status must be defined identically across UTSW, UCSF-PDGM, and EGD before any statistic is pooled: IDH1/IDH2 mutation by sequencing or an established IHC+sequencing algorithm, per WHO 2021. Each cohort's exact labelling methodology is documented in `manifests/label_definitions.md` and reproduced in the manuscript Methods. Cohort-specific differences in assay or era — older cases assessed under pre-2021 WHO criteria — are **flagged as potential label heterogeneity, not silently normalized away.**

---

## 8. Normalization-statistic leakage control

Per-modality z-score statistics are computed **exclusively from the UTSW training split** and applied unchanged to calibration, internal test, UCSF-PDGM, and EGD. Computing them on pooled train+test — or worse, train+external — would leak external distribution information into the model's effective input space and silently invalidate the entire domain-shift evaluation.

Enforced by: a unit test asserting the statistics artifact's provenance is the training split alone; the statistics file is hashed and frozen at Phase 05; and the preprocessing CLI refuses to fit statistics on any cohort other than UTSW-train.

---

## 9. The leakage regression test

The most important test in the repository. Runs in CI on every commit; **never skipped, never marked xfail.**

Given the frozen manifests, assert:
1. No patient ID appears in more than one UTSW split.
2. No excluded ID appears in any split.
3. `UTSW ∩ UCSF-PDGM = ∅` and `UTSW ∩ EGD = ∅` (post-normalization).
4. `UCSF-PDGM ∩ BraTS-2021 = ∅` after the shipped ID-map exclusion.
5. Every ID in every split exists in the final cohort manifest.
6. Manifest hashes match their recorded values.

---

## 10. Retention

| Data | Retention |
|---|---|
| `raw/` | Permanent, read-only after checksum. Never modified in place. |
| `processed/` | Permanent, content-addressed by preprocessing parameter hash. |
| `interim/` | Disposable; regenerable; resumable. |
| `manifests/` | **Permanent, committed to Git** (hashes and, where terms permit, IDs). |
| `private/` | Permanent on the SSD; never committed; never synced off the machine. |
| Augmented volumes | **Never persisted** — augmentation is online only. |
