# SPEC-CLAIMED VS. FILE-VERIFIED COUNTS

Phase 03 T03.3 (**D-009**). SPEC §9 step 1: *"independently verify (do not trust this document
alone) the exact per-marker IDH/1p19q/MGMT counts by parsing the actual clinical-metadata files."*
Every count below comes from two independent computations against the real metadata files —
`src/glioma_selective/data/metadata.py` (T03.2, Codex) and the file-level counting done for
`LABEL_DEFINITIONS.md` (T03.6, Claude) — which agree exactly. No count here is taken from the SPEC
or from memory of an earlier draft.

---

## UTSW-Glioma (625 patients)

| Marker | SPEC-claimed | File-verified | Match |
|---|---|---|---|
| Patients | 625 | 625 | Exact |
| IDH | n=622 (176 mutant / 446 wildtype) | n=622 (176 mutant / 446 wildtype), 3 `NA` | Exact |
| 1p/19q | n=335 (63 codeleted / 272 non-codeleted) | n=335 (63 codeleted / 272 non-codeleted), 290 `NA` | Exact |
| MGMT (not an endpoint) | n=281 (114 methylated / 167 unmethylated) | n=281 (114 methylated / 167 unmethylated), 344 `NA` | Exact |

**The one numerical gap the SPEC itself names — 625 patients but IDH n=622 — is fully explained,
not just replicated:** exactly 3 patients (source TSV rows 140, 141, 171 — row numbers only, no
patient ID, per `DATA_GOVERNANCE_PROTOCOL.md` §3) have a literal `NA` in the `IDH` column. Every
other UTSW marker matches the SPEC's claimed split exactly, with zero unexplained residual.

## UCSF-PDGM (501 patients)

| Marker | SPEC-claimed | File-verified | Match |
|---|---|---|---|
| Patients | 501 | 501 | Exact |
| IDH | "labeled for essentially all patients" (no exact split given) | 501/501 labeled — 103 mutant (8 distinct variant categories + `mutated (NOS)`), 398 wildtype; **zero** blank/`NA` | Verified count is stronger than the SPEC's qualitative claim: literally all 501, not "essentially all" |
| 1p/19q | 410/501 labeled | 410/501 labeled (15 codeletion-type rows across 3 differently-spelled categories + 395 `intact`), 91 blank | Exact |

The three differently-spelled 1p/19q codeletion categories (`co-deletion`, `Co-deletion`,
`relative co-deletion` — see `LABEL_DEFINITIONS.md` §4) are a data-entry artifact in the source
file, not a count discrepancy; T03.2 reported them as distinct literal categories per its scope
(no harmonization), and their sum still reconciles to the SPEC's 410 exactly.

## EGD (774 patients, SPEC-claimed) — not yet downloaded

EGD's DUA submission is deferred by Research Lead choice (D-018); the cohort has not been
downloaded and no file exists to verify against. SPEC-claimed values are recorded here for later
verification, not treated as confirmed: IDH n=467, 1p/19q n=259, grade n=716. This is the only
part of D-009 still genuinely open.

---

## Conclusion

For both cohorts currently in hand, every SPEC-claimed count matches the source metadata files
exactly, and the SPEC's own internal gap (625 vs. 622) is now a documented file-level finding
rather than an unexplained wobble. **D-009 is resolved for UTSW and UCSF-PDGM; it stays formally
`OPEN` only pending EGD**, which cannot be verified until T02.1 completes. No count from this
document may be hard-coded into source or config — the verified reports remain the artifact of
record (`paths.manifests_dir()/label_verification.json`, not committed, reproducible from
`metadata.py`).
