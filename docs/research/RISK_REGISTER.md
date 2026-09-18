# RISK REGISTER

Live document. Reviewed at every phase gate. Each risk carries likelihood, impact, detection, prevention, mitigation, owner, phase, and an escalation trigger.

**L / I scale:** L = Low, M = Medium, H = High.

---

## CRITICAL — any one of these can invalidate the study

### R-C01 · Patient-level leakage within UTSW
**L:** M · **I:** H (study-invalidating) · **Owner:** A · **Phase:** 03, 05
**Detection.** Leakage regression test (CI, every commit): no patient ID in two splits; no excluded ID in any split.
**Prevention.** Split by patient only, computed after de-duplication, frozen with a committed hash. No slice- or scan-level splitting anywhere in the codebase.
**Mitigation.** If found post-training, discard every affected result and re-run from the corrected split. There is no partial remedy.
**Trigger.** Any test failure → halt all training until resolved.

### R-C02 · Cross-dataset overlap, especially UCSF-PDGM ⇄ BraTS-2021
**L:** **H (documented to exist)** · **I:** H · **Owner:** B (audit), A (sign-off) · **Phase:** 03
**Detection.** Phase 03 overlap matrix; the shipped UCSF-PDGM/BraTS-2021 ID-mapping file.
**Prevention.** Normalize IDs before matching (case, padding, prefixes). Compute every cell of the matrix including expected-empty ones. Exclude before any split is computed.
**Mitigation.** Exclude and re-freeze. If discovered after Gate E, the external claim for that cohort is void and must be re-run from a corrected manifest with a new freeze.
**Trigger.** Any non-empty overlap cell → Research Lead review before proceeding.

### R-C03 · External-test peeking
**L:** M (temptation is real and constant) · **I:** H (**voids C4**) · **Owner:** A · **Phase:** 02–11
**Detection.** `GATE_E_LOG.md`; CI runs with the authorization flag at 0; code review for external label access.
**Prevention.** `firewall.assert_external_eval_authorized()` on every external label path; agents instructed to stop and raise rather than work around; the operational/performance distinction documented in `EXTERNAL_VALIDATION_PROTOCOL.md` §1.
**Mitigation.** If a peek occurs, **record it honestly** in the decision log and disclose it in the manuscript. Do not conceal it — an undisclosed peek discovered by a reviewer is far worse than a disclosed one.
**Trigger.** Any external metric computed before Gate E → immediate Research Lead escalation.

### R-C04 · Preprocessing / normalization leakage
**L:** M · **I:** H · **Owner:** A · **Phase:** 04, 05
**Detection.** Unit test asserting normalization statistics derive from the UTSW training split alone; statistics artifact hashed and frozen.
**Prevention.** Preprocessing CLI refuses to fit statistics on any cohort other than UTSW-train.
**Mitigation.** Recompute statistics, re-preprocess, re-train. Expensive but recoverable if caught before Gate E.

### R-C05 · Wrong modality → channel mapping
**L:** M · **I:** H (silently wrong results that still look plausible) · **Owner:** B · **Phase:** 03, 04
**Detection.** Visual QC on a representative sample with modality labels shown; automated header/contrast heuristics cross-checked against filenames; per-cohort adapter tests.
**Prevention.** Cohorts name sequences differently; each adapter maps explicitly and is unit-tested against known cases. Never infer modality from file order.
**Mitigation.** Remap and re-preprocess. **Note:** this failure is invisible to loss curves — a model trained on shuffled channels still trains. Only QC catches it.

### R-C06 · Wrong or unfrozen patient split
**L:** L · **I:** H · **Owner:** A · **Phase:** 05
**Detection.** Split hash verified in every run record.
**Prevention.** Freeze at Phase 05; hash committed; post-freeze changes require a decision-log entry.
**Mitigation.** Any post-freeze split change invalidates all downstream results — treat as a full re-run.

### R-C07 · Label-definition mismatch across cohorts
**L:** M · **I:** H · **Owner:** B · **Phase:** 03
**Detection.** `manifests/label_definitions.md` comparison across UTSW/UCSF/EGD.
**Prevention.** Harmonize to WHO 2021 IDH1/IDH2 by sequencing or established IHC+sequencing algorithm before pooling any statistic. Flag assay/era differences (pre-2021 WHO criteria) rather than normalizing them away.
**Mitigation.** Exclude incompatible cases (`label:definition-mismatch`) or report cohort-stratified results.

### R-C08 · Architecture scope creep
**L:** **H (SPEC names it the project's main risk)** · **I:** M (schedule + budget) · **Owner:** A · **Phase:** 06–10
**Detection.** PR review against the non-scope list; run-count monitoring against the 9-run budget.
**Prevention.** Backbone frozen in the SPEC and SI-11. "Would a better backbone change the answer to RQ1?" — if no, don't build it.
**Mitigation.** Cut back to the frozen architecture; record the excursion in the decision log.

### R-C09 · Post-hoc threshold manipulation
**L:** M · **I:** H (**unfalsifiable claims**) · **Owner:** A · **Phase:** 05, 11
**Detection.** Pre-registration hash predates every external result; the α grid and tolerance band are in the freeze manifest.
**Prevention.** **D-003** and **D-004** resolved and frozen at Phase 05, before external data can influence them.
**Mitigation.** Report both the pre-registered and any revised analysis, clearly distinguished. The pre-registered one is primary regardless of which looks better.

---

## HIGH

### R-H01 · EGD data-use agreement delayed or refused
**L:** **H** · **I:** M · **Owner:** B · **Phase:** 02 → 11
**Detection.** Weekly status check logged in `DATA_ACCESS_LOG.md`.
**Prevention.** Submit on **day 1** of Phase 02. Nothing else waits on it.
**Mitigation.** Proceed with UCSF-PDGM as the sole external cohort (`EXTERNAL_VALIDATION_PROTOCOL.md` §5); add EGD later as a separately-frozen addendum.
**Trigger.** No response by week 6 → escalate to Health-RI directly and record the contingency decision.

### R-H02 · Corrupted or incomplete TCIA downloads
**L:** M · **I:** M · **Owner:** B · **Phase:** 02
**Detection.** Checksums where available; file-count and per-patient sequence-count inventory.
**Prevention.** Verify before preprocessing, not after. Record the inventory in the access log.
**Mitigation.** Re-download affected patients; exclude with `qc:corrupt` if irrecoverable.

### R-H03 · Insufficient class counts after exclusions
**L:** M (**H for 1p/19q — 63 positives before any exclusion**) · **I:** H for RQ4, M for IDH · **Owner:** A · **Phase:** 03, 05
**Detection.** Phase 03 verified counts (**D-009**); Phase 05 power check before the split is frozen.
**Prevention.** Check counts *before* committing to split sizes — SPEC §4.11 names this explicitly.
**Mitigation.** If IDH internal test falls below the power threshold, widen the internal test share and reduce coverage-grid granularity. If 1p/19q positives fall much below 63, **report RQ4 as descriptive only, or drop it** — do not present an underpowered inferential claim.

### R-H04 · GPU out-of-memory
**L:** M · **I:** L (schedule only) · **Owner:** A · **Phase:** 06–08
**Detection.** Phase 01 memory benchmark at the target patch size, before training is scheduled.
**Prevention.** Measure, don't assume — actual VRAM is unknown until Phase 01.
**Mitigation.** Documented ladder: reduce patch size 128³ → 96³ → gradient accumulation → batch size 1. **Any such change is recorded as a deviation and checked against the SPEC, not silently applied.**

### R-H05 · Remote GPU server downtime
**L:** M · **I:** M · **Owner:** A · **Phase:** 06–12
**Prevention.** All long runs under `tmux`/`nohup`; checkpoint every epoch plus `last.ckpt`; resume is a **tested** code path (Phase 06 authorization step 6).
**Mitigation.** Resume from the last checkpoint. If the server is lost for an extended period, SPEC §3.7 permits a single rented cloud GPU — subject to a DUA check before any data moves.

### R-H06 · Preprocessing pipeline failure on a subset
**L:** M · **I:** M · **Owner:** B · **Phase:** 04
**Detection.** Per-case status manifest; visual QC on a representative sample.
**Prevention.** Resumable, content-addressed pipeline; failure categories defined in advance.
**Mitigation.** Correct if systematic (a parameter), exclude if individual (`qc:*`). Document the exclusion count — never silently drop.

---

## HIGH — but these are **scientific outcomes, not engineering failures**

The SPEC is explicit that several "bad-looking" results are legitimate findings. They are registered here so they are recognized as *results* rather than debugged away.

| ID | Outcome | What it actually means | Required response |
|---|---|---|---|
| **R-S01** | Very wide CIs at extreme coverage | Expected — SPEC §5.3 predicts visibly wide bands at coverage extremes on a low-hundreds internal test set | Report the CIs honestly; do not narrow the coverage grid to hide them |
| **R-S02** | Non-monotonic risk–coverage curves | **Refutes C5.** Mirrors Zadorozhny et al.'s documented retinal/CXR failures | Report it. Quantify the violation magnitude with a bootstrap CI. This is a headline finding. |
| **R-S03** | Calibration collapse externally | **Answers RQ3 affirmatively.** Replicates GliomaVista-IDH external Brier 0.32 | Report ECE/Brier degradation directly; do not report only favorable conditions |
| **R-S04** | High abstention rate under shift | Conformal rejecting a large fraction to hit nominal coverage is informative | Report the coverage–accuracy trade-off transparently. **Do not loosen the threshold to make abstention "look reasonable."** |
| **R-S05** | Poor external discrimination | **Refutes C3.** Precedented — Elyassirad et al. saw external AUROC 0.734 | Valid, reportable outcome (SPEC §5.4). Not a bug to engineer away. |
| **R-S06** | Coverage deviation too noisy to characterize | **Refutes C4 by its own pre-registered criterion** | Report it as such. C4 was written to allow exactly this answer. |

**Standing rule.** No experiment is re-run, re-tuned, or re-scoped because its outcome refutes a claim. Refutations are recorded in `paper/NEGATIVE_RESULTS.md` when they occur.

---

## MEDIUM

| ID | Risk | L/I | Owner | Mitigation |
|---|---|---|---|---|
| R-M01 | Agents edit overlapping files, causing merge damage | M/M | A | Directory ownership table; no concurrent ownership |
| R-M02 | Collaborators B/C disengage | M/M | A | Every B/C task has a solo fallback; solo critical path published (+7 weeks) |
| R-M03 | Forward-dated citations unverifiable (**D-010**) | M/L | C | Verify-before-cite pass in Phase 14; drop rather than cite on faith |
| R-M04 | TRIPOD+AI or CLAIM updated before submission | M/L | C | Freshness re-check within 30 days of submission (SI-15) |
| R-M05 | A competing paper closes the gap during the project | M/M | A | Fresh novelty check at Phase 14; framing changes, experiment does not |
| R-M06 | Simulated-vs-natural missingness challenged by reviewers (**D-008**) | **H**/M | A | Preemptive Limitations paragraph; "simulated" in every relevant caption |
| R-M07 | External SSD failure | L/H | A | Raw data re-downloadable; manifests in Git; checkpoints and predictions backed up after each frozen run |
| R-M08 | Dirty git tree during a scientific run | M/M | A | Gate C blocks on `git_dirty` |
