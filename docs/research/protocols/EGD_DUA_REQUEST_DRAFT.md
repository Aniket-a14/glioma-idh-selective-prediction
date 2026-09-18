# EGD Data Use Agreement — request draft

**Status: DRAFT, NOT YET SENT.** This is a template with blanks for you to fill in and send
yourself from your own email — not something an agent submits on your behalf (it requires your
actual institutional identity and signature). Once sent, update `DATA_ACCESS_LOG.md`'s EGD section
with the send date and mark T02.1 as submitted there; that's the acceptance-criterion evidence
("a dated receipt in the access log"), not this file.

---

**To:** servicedesk@health-ri.nl
**Subject:** Data Use Agreement request — Erasmus Glioma Database (EGD)

---

Dear Health-RI Service Desk,

I am writing to request access to the Erasmus Glioma Database (EGD) (van der Voort et al.,
*Data in Brief* 2021, DOI 10.1016/j.dib.2021.107191) under a Data Use Agreement, for use as an
external validation cohort in an academic research project.

**Requester details**
- Name: `[YOUR NAME]`
- Institution / affiliation: `[YOUR INSTITUTION]`
- Department: `[YOUR DEPARTMENT]`
- Supervising PI (if applicable): `[PI NAME, OR "N/A — independent/capstone project"]`
- Institutional email: `[YOUR INSTITUTIONAL EMAIL]`
- Any existing XNAT portal account: `[YES/NO — include username if yes]`

**Project description**

This project develops and evaluates a calibrated selective-prediction system for MRI-based
glioma IDH mutation-status classification. The primary training and internal validation cohort
is UTSW-Glioma (TCIA, open access). UCSF-PDGM and EGD are intended as fully independent external
test cohorts — used only for a single, frozen final evaluation of model calibration and
selective-prediction coverage, never for training, tuning, or model selection. `[ADD ANY
INSTITUTIONAL/COURSE CONTEXT HERE, E.G. "This is a capstone research project supervised by
[ADVISOR] at [INSTITUTION]" — fill in or delete this bracket]`

**Data requested**

The full EGD imaging cohort (pre/post-contrast T1w, T2w, FLAIR) with available IDH mutation
status and other molecular/clinical labels, per the dataset's published description.

**Intended use and data handling**

- Used strictly as a held-out external test set — no training, hyperparameter tuning, or model
  selection will be performed on EGD data.
- Stored on `[DESCRIBE YOUR STORAGE — e.g. "an access-controlled local workstation/external
  drive, not shared cloud storage"]`, not redistributed.
- Results will be reported at the aggregate/statistical level; no patient-identifiable
  information will appear in any publication.
- `[ADD ANYTHING ELSE YOUR INSTITUTION'S DUA PROCESS TYPICALLY ASKS FOR — IRB/ethics approval
  reference if you have one, expected data retention period, etc.]`

Please let me know what documentation or forms are required to proceed, and the expected
timeline for review.

Thank you for your time.

`[YOUR NAME]`
`[YOUR INSTITUTION]`
`[DATE]`

---

## Notes for whoever sends this

- Fill every `[BRACKETED]` field before sending — an incomplete request will likely just bounce
  back asking for the same information, costing a review cycle.
- If your institution has a standard DUA/data-governance contact (e.g., a research office), it
  may be worth looping them in before sending, since Health-RI may ask your institution to
  countersign.
- Health-RI's own reply may include a specific DUA template/portal rather than approving by
  email directly — that's expected, not a rejection.
