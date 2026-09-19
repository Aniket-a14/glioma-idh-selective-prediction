# DECISION LOG

Records every point where the source documents were ambiguous, contradictory, infeasible, or required human judgement. **Nothing here was silently resolved.** Each entry states the conflict, the alternatives, the consequences, and a recommendation — decisions marked OPEN require Research Lead sign-off before the named phase proceeds.

**Format:** `D-NNN` · status `OPEN | RESOLVED | SUPERSEDED` · resolve-by phase · blocking?

---

## D-001 — Team model: solo researcher vs. three active contributors
**Status:** RESOLVED (2026-09-07, Research Lead) · **Blocking:** no

**Conflict.** SPEC header says *"Team size: Solo researcher (student project)."* `Master_Research_Execution_prompt.md` assumes six students with three (A/B/C) active and requires the project be executable by three.

**Alternatives.** (a) Solo — simplest, but loses independent verification of data QC and statistics, which are exactly the places where a single operator's blind spot becomes a retracted paper. (b) Three active — matches the master prompt, but the plan collapses if collaborators disengage mid-project, which is the common failure mode for student teams. (c) Three active with mandatory solo fallback per task.

**Decision.** (c). Every Person B/C task records `solo_fallback: <executor> (+N days)`. The critical path is published twice (§30 of the master plan): 3-person ≈34 weeks, solo-degraded ≈41 weeks. Where the fallback is "A + Codex", Codex re-derives the calculation from the specification text alone and results must agree — an independent-implementation check standing in for a second human.

**Consequence.** Two judgement-heavy tasks degrade rather than substitute: MRI visual QC (Phase 04) and label-definition adjudication (Phase 03). Both are marked `DEGRADED` and, if executed solo, **must be disclosed in the manuscript Limitations section.** The SPEC's "solo researcher" line is superseded for planning purposes; the scientific content is unaffected.

---

## D-002 — "Split conformal prediction" and "conformal risk control" are used interchangeably
**Status:** OPEN · **Resolve by:** Phase 07 (before any calibration is fitted) · **Blocking:** YES

**Conflict.** SPEC §4.6 titles the primary mechanism *"split conformal prediction / conformal risk control — selected as the PRIMARY mechanism"* and later describes the implementation as *"a calibration-split nonconformity-score computation plus a quantile threshold."* These are **different procedures**:

- **Split conformal prediction (CP)** produces prediction *sets* with a marginal coverage guarantee `P(y ∈ C(x)) ≥ 1−α`. Its guarantee is about set coverage.
- **Conformal risk control (CRC)** generalizes this to control the *expectation of a bounded loss*, `E[ℓ] ≤ α`. Its guarantee is about risk, not coverage.

RQ2 and C4 are both written in **coverage** language ("empirical coverage remain close to nominal"). The §4.6 implementation sketch (nonconformity quantile on a calibration split) describes split CP.

**Alternatives.** (a) Split CP primary — matches RQ2/C4's coverage framing and the implementation sketch; simplest defensible reading. (b) CRC primary — matches the section title and the "risk control" phrasing, but then C4's coverage language needs restating as a risk-control statement. (c) Both, with one designated primary.

**Recommendation.** **(a), with (c) as the reported form**: split conformal is the primary instrument because RQ2/C4 are coverage claims and coverage is what the study measures; CRC is implemented as a named secondary analysis on the selective-risk loss, reported alongside. This is the safest reading — it preserves the falsifiable claim exactly as pre-registered.

**Consequence if wrong.** Choosing CRC as primary silently changes what C4 asserts, which would be a scientific change made by an engineering decision. That is precisely what this log exists to prevent.

---

## D-003 — Abstention is operationalized two incompatible ways
**Status:** OPEN · **Resolve by:** Phase 05 (pre-registration, before any calibration fitting) · **Blocking:** YES

**Conflict.** SPEC §1.2 defines rejection as a **threshold on a score**: *"g(x) → {0,1} ... a rejection threshold τ on the conformal nonconformity score."* But split conformal on a **binary** label set naturally produces prediction sets `∅`, `{0}`, `{1}`, `{0,1}`, where the idiomatic abstention rule is "abstain iff the set is not a singleton." These give different objects:

| | Threshold-on-score | Non-singleton set |
|---|---|---|
| Coverage axis | Swept continuously by τ | Determined by α; one point per α |
| Risk–coverage curve | Natural — sweep τ | Requires sweeping α instead |
| Empirical-vs-nominal coverage | Not directly defined | Directly defined |
| Handles `∅` (both labels rejected) | N/A | Must be defined — abstain, presumably |

RQ1/C1–C3/C5 need a **continuous sweep** (risk–coverage curves, AURC). RQ2/C4 need a **nominal coverage target** to compare against. Neither operationalization serves both cleanly on its own.

**Recommendation.** Use **both, for the questions each is built for**, and pre-register the mapping: (i) the *nonconformity-score threshold* generates the risk–coverage curve and AURC (RQ1, C1–C3, C5, C6); (ii) the *set-valued conformal predictor at nominal 1−α* generates the empirical-vs-nominal coverage comparison (RQ2, C4), swept over a pre-registered α grid (e.g. α ∈ {0.05, 0.10, 0.20}). Report explicitly that these are two views of one calibrated score, and state the exact definition of "abstain" in each. Define `∅` as abstention and report its rate separately — an empty prediction set under shift is itself an informative signal.

**Consequence if unresolved.** The risk–coverage curves and the coverage claim would be computed under different definitions of abstention without saying so, making C4 and C5 non-comparable. Reviewers at the target venues will find this.

---

## D-004 — C4's tolerance band is an example, not a number
**Status:** OPEN · **Resolve by:** Phase 05, before any external data is touched · **Blocking:** YES

**Conflict.** C4 reads *"against a pre-registered tolerance band **such as** ±5 percentage points."* "Such as" is illustrative. **A claim with an unspecified threshold cannot be falsified**, and C4's own falsification condition ("the deviation cannot be reliably characterized ... at the pre-registered tolerance") explicitly presupposes that a tolerance exists.

**Why this must be frozen pre-externally.** If the band is chosen after seeing external coverage, C4 becomes unfalsifiable in the worst way — the threshold moves to wherever the result lands. This is the exact failure the SPEC's §1.5 pre-registration is designed to prevent.

**Alternatives.** (a) Adopt ±5 pp as written. (b) Derive the band from achievable precision: with an external cohort of n≈450–500, the bootstrap CI half-width on a coverage estimate near 0.90 is roughly ±2.7 pp, so ±5 pp is detectable — a band narrower than ~±3 pp would be indistinguishable from noise. (c) Set separate bands per cohort to reflect differing n.

**Recommendation.** **(a) informed by (b)**: freeze **±5 percentage points**, and record in the pre-registration the power calculation showing this band is resolvable at the expected external n. Also pre-register the answer to C4's *own* falsification clause: if the bootstrap CI half-width on coverage deviation exceeds the band itself, C4 is refuted (deviation not reliably characterizable) — and that is a reportable finding, not a failure.

**Owner.** Research Lead. Recorded in `docs/research/protocols/PREREGISTRATION.md` and hashed before Phase 06.

---

## D-005 — Compute budget cannot accommodate the deep ensemble as literally specified
**Status:** RESOLVED · **Blocking:** no

**Conflict.** SPEC §3.6 describes *"a bounded, enumerable set of runs"* and §3.4 budgets *"8–12 runs"* totalling 2–4 weeks of GPU. But §4.6 requires a deep ensemble of **N≈5**, and §4.9 lists five ablation axes. Read naively — one training run per mechanism per condition — the grid needs dozens of runs and does not fit.

**Resolution.** The budget only binds on *training*. M1 (raw softmax), M2 (temperature scaling), M3 (MC-dropout), M5 (conformal), and M6 (tumor-aware comparator) are all **post-hoc or inference-time** operations on already-trained weights. Only M4 (ensemble) needs multiple training runs, and its members are trained **once** and reused across all 18 evaluation conditions.

Final budget: **9 training runs** (R1 no-modality-dropout baseline; R2–R6 modality-dropout seeds 0–4, where R2 doubles as the primary single model; R7 whole-brain pooling ablation; R8 two-stage ablation; R9 reserve). Inside the 8–12 envelope. The 108 result cells are produced by cheap CPU analysis over frozen prediction artifacts.

**Consequence.** This is *why* the architecture freezes prediction artifacts to disk (master plan §9, §18). If analysis re-ran the model, the budget would not close.

---

## D-006 — Baseline 5 ("reproduced published comparator") is unbounded in scope
**Status:** OPEN · **Resolve by:** Phase 06 · **Blocking:** yes

**Conflict.** SPEC §4.8 baseline 5 asks for *"an always-predict, tumor-aware, joint-learning model in the style of COM-Net/MTS-UNET/GMMAS ... reproduced only to the extent needed to serve as a fair always-predict comparison point, not as an attempt to match published SOTA numbers exactly."* The hedge is present, but "reproduce a published multi-task architecture" is an open-ended engineering commitment inside a project whose SPEC closes with *"the risk in this project is scope creep, not insufficient novelty."*

**Alternatives.** (a) Full reimplementation of GMMAS/COM-Net — weeks of work, unverifiable without the original data, high risk of an unfair strawman. (b) Same SegResNet backbone + auxiliary segmentation head + tumor-aware pooling, trained always-predict — already built for the main model, costs one extra evaluation pass, no extra training run. (c) Cite published numbers without reimplementation — not comparable, different cohorts.

**Recommendation.** **(b).** M6 is our own backbone in its tumor-aware joint configuration, evaluated always-predict, described in the manuscript as *"a tumor-aware joint-learning comparator in the style of COM-Net/MTS-UNET/GMMAS, implemented on our backbone for cohort-matched comparability"* — explicitly **not** a reproduction of those systems, with published numbers cited separately as context. This is fair (same data, same preprocessing, same splits), cheap, and honest about what it is.

---

## D-007 — RQ4 (1p/19q) has a research question but no compute or cohort budget
**Status:** OPEN · **Resolve by:** Phase 05 · **Blocking:** yes

**Conflict.** RQ4 is a named research question and C-level analyses are expected for it, but SPEC §3.6's experiment grid and §3.4's compute estimate are sized for IDH alone. §5.3 separately warns 1p/19q (63 codeleted pre-exclusion) *"is underpowered for anything beyond a descriptive, wide-CI exploratory analysis."*

**Alternatives.** (a) Multi-head model — one training run predicts both IDH and 1p/19q; near-zero extra compute, but risks the 1p/19q head degrading IDH performance, which would compromise the primary endpoint. (b) Separate 1p/19q runs — clean, but adds ~4 training runs and breaks the budget resolved in D-005. (c) Frozen-encoder probe — train IDH as primary, then fit a small 1p/19q head on frozen features; ~1 GPU-hour, cannot harm the primary endpoint.

**Recommendation.** **(c).** It matches RQ4's *exploratory* status exactly, costs almost nothing, and structurally guarantees the primary endpoint is unaffected. Pre-register that RQ4 results are exploratory, reported with wide CIs and no inferential claim, and that a null result there is expected given n=63 rather than interpreted as evidence of absence.

---

## D-008 — Missingness is simulated by construction
**Status:** OPEN (reporting obligation) · **Resolve by:** Phase 14 · **Blocking:** no

**Conflict.** SPEC §3.8 concedes: *"UTSW, UCSF-PDGM, and EGD are all curated four-sequence cohorts, so true missing-modality evaluation must be simulated (dropped at inference), which is a construct-validity limitation to state plainly."* Meanwhile RQ1/C2 are stated as claims about *"missing MRI sequences"* generally.

**The gap.** Real-world missingness is not random — a sequence is absent because of motion artifact, patient intolerance, truncated protocol, or scanner failure, all of which correlate with image quality and possibly with disease severity. Zeroing a channel from a *complete, high-quality* study simulates the information loss but not the selection mechanism.

**Recommendation.** Not resolvable with these cohorts — it is a genuine limitation, and the honest response is disclosure rather than mitigation. Required: (i) a Limitations paragraph stating the construct-validity gap explicitly; (ii) **every missing-modality figure caption and table header carries the word "simulated"**; (iii) any naturally-missing cases found in Phase 03 are reported separately as a small natural-missingness sanity check (see D-012), explicitly underpowered. Do **not** soften RQ1/C2's wording after the fact — pre-registered claims stand as written, with the limitation stated alongside.

---

## D-009 — Every label count in the SPEC is unverified
**Status:** OPEN — resolved for UTSW/UCSF-PDGM, pending EGD only · **Resolve by:** Phase 03 · **Blocking:** YES (on EGD arrival, not on UTSW/UCSF-PDGM)

**Conflict.** SPEC §9 step 1 instructs: *"independently verify (do not trust this document alone) the exact per-marker IDH/1p19q/MGMT counts by parsing the actual clinical-metadata files."* Yet the SPEC's own counts (625 patients, IDH 622 = 176/446, 1p19q 335 = 63/272, UCSF 501, EGD 774/467) are quoted throughout as if settled — and there is an internal wobble already: 625 patients but IDH n=622, which implies 3 unlabelled cases whose disposition is unspecified.

**Recommendation.** Treat every count as **provisional** until Phase 03 emits a hashed, verified cohort manifest. The plan must make cohort sizes a *verified artifact*, never a hard-coded constant — no count from the SPEC may be written into source code or a config. Phase 03's acceptance criterion is a table of SPEC-claimed vs. file-verified counts with every discrepancy explained. If verified counts differ materially (especially 1p/19q), D-007's power assumptions and Phase 05's split sizing are revisited before the freeze.

**Partial finding (T03.6, label harmonization pass, 2026-09-18).** The "625 patients but IDH
n=622" gap is now explained, from the actual UTSW metadata file, not assumption: exactly 3 patients
have `IDH = NA` in `UTSW_Glioma_Metadata-2-1.tsv`. The remaining 622 split 176 mutated / 446
wildtype, matching the SPEC's claimed breakdown exactly. UCSF-PDGM's IDH (103 mutant variants /
398 wildtype) and 1p/19q (410 labeled, matching SPEC) also verified from its metadata CSV — see
`docs/research/protocols/LABEL_DEFINITIONS.md` for the full per-cohort breakdown.

**T03.3 resolution (2026-09-18).** `docs/research/protocols/SPEC_VS_VERIFIED_COUNTS.md` is the
formal SPEC-claimed vs. file-verified table this decision's acceptance criterion requires. Every
UTSW marker (IDH, 1p/19q, MGMT) and every UCSF-PDGM marker (IDH, 1p/19q) matches the SPEC's claimed
count exactly, computed independently twice (T03.2's `metadata.py` and T03.6's direct file
counting agree). The SPEC's own internal wobble (625 patients, IDH n=622) is fully explained as 3
literal `NA` rows, with no other unexplained residual anywhere in either cohort. **D-009 is
resolved for both cohorts currently downloaded.** It stays formally `OPEN` only because EGD (n=774,
IDH n=467 claimed) has not been downloaded — T02.1's DUA submission is deferred by Research Lead
choice (D-018) — so its counts cannot be verified yet. Re-open the blocking flag if EGD's verified
counts, once available, disagree materially with the SPEC's claim.

---

## D-010 — Several cited works are forward-dated or unverifiable
**Status:** OPEN · **Resolve by:** Phase 14 · **Blocking:** no

**Conflict.** The SPEC was prepared 2026-08-11 and cites items including arXiv 2606.23172 and arXiv 2605.23183 (2026 preprints), plus multiple 2026 journal entries. Some are marked *"not verified"* in the SPEC itself (e.g. PROBAST+AI, *"bibliographic detail only, not independently read in full"*).

**Recommendation.** A verify-before-cite pass in Phase 14: every reference resolved to a real, retrievable record; DOIs checked; preprint vs. peer-reviewed status confirmed and labelled as the SPEC does; anything unresolvable is dropped rather than cited on faith. Separately, the SPEC's §8.3 sentence claims **"first"** — per the master prompt, no "first" claim ships without a fresh literature/novelty check dated close to submission. If that check finds a competing paper, the framing changes; the experiment does not.

---

## D-011 — BraTS pretraining is permitted but not required
**Status:** OPEN · **Resolve by:** Phase 06 · **Blocking:** yes

**Conflict.** SPEC §2.5 permits BraTS *"only as a source of segmentation pretraining weights (if at all)"* and, if used, requires excluding every subject ID also appearing in UCSF-PDGM, TCGA-GBM/LGG, or EGD — *"or the 'external' claim for those cohorts is void."* SPEC §4.1 does not require pretraining at all.

**Alternatives.** (a) No BraTS pretraining — removes an entire leakage class outright; possibly slightly weaker segmentation head, which is an *auxiliary confirmatory* component, not the claim. (b) BraTS pretraining with full ID exclusion — marginally better auxiliary Dice, at the cost of a mandatory second exclusion audit whose failure silently voids C3 and the entire external-validation contribution.

**Recommendation.** **(a), strongly.** The upside accrues to the one component explicitly designated non-novel; the downside risks the paper's central claim. Cost-benefit is lopsided. If (b) is ever chosen, it requires its own Gate-D-level exclusion audit and Research Lead sign-off, recorded here.

---

## D-012 — Naturally-missing sequences conflict with a completeness inclusion criterion
**Status:** OPEN · **Resolve by:** Phase 03 · **Blocking:** yes

**Conflict.** SPEC §5.4 says: *"if any UTSW/UCSF/EGD case is naturally missing a sequence ... handle it identically to the simulated-missing pipeline and flag it as a naturally-occurring instance in reporting."* But the missing-modality design requires **complete** four-sequence studies as the baseline condition (you cannot drop T2 from a study that never had it), and §2.3 notes Elyassirad et al. imposed a complete-sequence inclusion criterion for exactly this reason.

**The tension.** A naturally-incomplete case cannot serve in the `full` condition, cannot be dropped-from, and if included in the denominator makes coverage across modality conditions non-comparable (different patient sets per condition).

**Alternatives.** (a) Exclude naturally-incomplete cases from the primary analysis; report them as a separate, explicitly underpowered natural-missingness check. (b) Include them, accepting non-comparable denominators. (c) Include them only in the matching simulated condition (a case missing T2 joins the `−T2` condition).

**Recommendation.** **(a).** It keeps the patient set identical across all 18 evaluation conditions — which is what makes matched-coverage comparison and paired statistics valid in the first place — and it turns the naturally-missing cases into a small bonus analysis that partly addresses D-008's construct-validity gap. Record the count and reason for every such exclusion in the exclusion manifest (`missing:sequence`).

**Partial finding (T03.9, naturally-missing sequence inventory, 2026-09-18).** Ran the inventory this decision's policy depends on against the real UTSW and UCSF-PDGM downloads: **zero** naturally-incomplete cases in either cohort — UTSW 625/625 and UCSF-PDGM 501/501 have all four canonical sequences (T1, T1ce, T2, FLAIR). Policy (a) therefore has nothing to exclude for these two cohorts; the tension this decision describes doesn't materialize here. **Status stays OPEN** — EGD hasn't been downloaded yet and could still surface naturally-incomplete cases once it arrives, and the exclusion-manifest wiring (T03.10) that actually applies this policy hasn't run.

---

## D-013 — Config system: Hydra vs. plain OmegaConf vs. pydantic-settings
**Status:** OPEN (provisional default adopted; skeleton built on it) · **Resolve by:** Phase 00, confirmed no later than Phase 05 freeze · **Blocking:** yes, for Phase 05

**Conflict.** Phase 00's own task list (T00.7) and "Decisions requiring Research Lead approval" section name this as an explicit judgement call, not an engineering detail: *"Config system choice (Hydra vs. plain OmegaConf vs. pydantic-settings)."* The master plan (§10) commits only to *"Hydra/OmegaConf, decided in Phase 00"* — the choice between the two, and against pydantic-settings, was left open.

**Why it matters enough to log rather than just pick.** `configs/` is where "experiments are DEFINED, not in code" (master plan §10) — the composition mechanism shapes how every later phase expresses a run (Phase 06 baselines, Phase 08 modality-dropout seeds, Phase 10's six ablation axes). Changing it later means touching every config file that exists by then.

**Alternatives.**
- **(a) Hydra** (structured configs over OmegaConf). Config-group composition (`configs/<group>/<name>.yaml`) matches the already-scaffolded directory layout exactly; built-in multirun/sweep support fits the ablation grid (§4.9) and the modality-dropout seed sweep (D-005's R2–R6) without hand-rolled iteration; CLI overrides give reproducible run records almost for free (REPRODUCIBILITY_PROTOCOL's run-record fields). Cost: Hydra's global ConfigStore and working-directory-changing behavior are known rough edges that the implementer (Codex, downstream) must account for explicitly (`hydra.job.chdir=False`).
- **(b) Plain OmegaConf**, no Hydra runtime. Simpler, no global state, no CLI/working-directory surprises. Cost: config-group composition, multirun sweeps, and override syntax would all be hand-rolled — reimplementing a fraction of what (a) provides for free, for a project whose stated main risk is scope creep (R-C08), not insufficient tooling.
- **(c) pydantic-settings.** Strongest runtime validation and typing ergonomics, and native environment-variable loading — but its design center is a flat settings object from env/CLI, not hierarchical multi-file YAML composition across the eight `configs/<group>/` directories already scaffolded. Would need to be paired with something else for composition, making it a validation layer on top of (a) or (b) rather than a replacement.

**Decision (provisional).** **(a), Hydra with structured configs.** It is the only option that matches the already-committed `configs/{data,preprocessing,model,training,calibration,selective,evaluation,experiments}/` layout without extra machinery, and the multirun/override mechanics directly serve two already-budgeted needs (D-005's seed sweep, §4.9's ablation grid) rather than hypothetical future ones. `hydra.job.chdir=False` is adopted from the start so run working directories stay predictable for `utils/paths.py` consumers.

**What is built now vs. deferred.** T00.7 ships the *decision* and a minimal *skeleton*: one `configs/config.yaml` root composing empty per-group `base.yaml` placeholders, and `configs/README.md` documenting the composition convention. It deliberately contains **no scientific parameter values** — populating `model/`, `training/`, etc. with real hyperparameters is Phase 06+ work and would be scope creep here (Risk R-C08). The structured-config dataclasses / `ConfigStore` registration and the actual config-loading entry point are implementation, not design, and belong to whichever agent owns the consuming module (`utils/`, `cli/` — Codex) once there is real content to validate.

**Consequence if this default is wrong.** Reversing after Phase 05 freeze means restructuring every experiment config that exists by then, which is why this is marked blocking for Phase 05 rather than Phase 00 itself — Phase 00 can close on the provisional default; Phase 05 pre-registration should not proceed without an explicit Research Lead confirmation (or override) of this choice.

**Owner.** Research Lead confirms or overrides before Phase 05.

---

## D-014 — External storage falls short of SPEC §3.2, and already holds unrecorded data
**Status:** RESOLVED (2026-09-18, Research Lead, live) · **Blocking:** no (Phase 01 proceeds under the accommodation below)

**Conflict.** Phase 01 (`PHASE_01_INFRASTRUCTURE.md`) requires ≥500 GB free on the storage root (acceptance criterion 3) and treats <250 GB as an explicit failure condition. Two external USB drives are connected: `Research_1` (256 GB total, 95 GB free, exFAT) and `Research_2` (128 GB total, 96 GB free, exFAT). Combined free space is 191 GB — below the 250 GB floor even summed across both, and neither drive individually approaches 500 GB.

**Second finding, discovered in the same pass.** Both drives already contain dataset content that predates Phase 01/02 formally starting — `Research_1/Glioma/PKG - UCSF-PDGM Version 5` (143 GB, the external test cohort) and `Research_2/Glioma/PKG - UTSW-Glioma` (23 GB, the primary dev cohort) plus `UTSW_Glioma_Metadata-2-1.tsv`. Per the Research Lead, this was downloaded following instructions given in an earlier session, prior to this repository's Phase 01/02 process existing in its current form. Neither package is laid out per the canonical `$GLIOMA_STORAGE_ROOT/data/{raw,external,...}` structure, and no acquisition record, checksum, or manifest exists anywhere in the repo for either (`docs/research/DATA_GOVERNANCE_PROTOCOL.md` §1–2 require both) — because Phase 02, which is where those artifacts are produced, hasn't started yet.

**Alternatives considered for the capacity shortfall.** (a) Wait for additional/larger storage before starting Phase 01. (b) Free existing capacity or acquire bigger hardware first. (c) Proceed on the 191 GB actually available, logging the deviation and accepting a tighter operating margin (aggressive `cache/`/`interim/` pruning, no long-tail checkpoint retention) as the accommodation.

**Decision.** **(c).** Research Lead confirmed live: "this is genuinely all we have — log a deviation and proceed." Phase 01 continues on the two drives as-is rather than blocking on hardware that isn't coming.

**Storage layout implication (for whoever writes T01.1 `scripts/bootstrap_storage.py`, Codex per the phase table).** `utils/paths.py` supports exactly two independent root overrides (`GLIOMA_DATA_ROOT`, `GLIOMA_ARTIFACT_ROOT`) on top of `GLIOMA_STORAGE_ROOT` — there is no per-subdirectory override, so `data/external` cannot be routed to a second physical volume through env vars alone. The two datasets already sit on separate drives (dev cohort on `Research_2`, external cohort on `Research_1`), which happens to line up naturally with the external-validation firewall. Recommended treatment: `GLIOMA_STORAGE_ROOT=/Volumes/Research_2` (dev cohort + artifacts), with `data/external` created as a plain symlink to `/Volumes/Research_1/...` *after* `bootstrap_storage.py` runs, not inside the script itself — keeps the idempotent-symlink-creation script generic (single root in, `data/`+`artifacts/` out) while accommodating the two-drive reality as a documented one-off. `bootstrap_storage.py`'s "refuses dangerous overwrites" requirement must tolerate `data/external` already existing as a symlink rather than treating it as a conflict.

**Consequence.** (i) Phase 02 must retroactively produce the acquisition record and checksums for both already-downloaded packages before either is treated as a verified project input — nothing computes against them until that exists, consistent with D-009's "every count is provisional until verified." (ii) Operating margin is tight (191 GB vs. the 500 GB target); if raw+processed+checkpoints approach the ceiling before Phase 05, revisit hardware rather than silently letting `cache/`/`interim/` growth crowd out `raw/`. (iii) `Research_1`/`Research_2` being exFAT is fine functionally (large-file support, readable without extra drivers) but carries no Unix permission bits — not a blocker, noted for completeness.

**Owner.** Research Lead (this entry). Layout implication is input to whoever executes T01.1.

---

## D-015 — T01.9 names five recovery-runbook failure modes but requires six
**Status:** RESOLVED (2026-09-18, Claude, non-blocking editorial gap) · **Blocking:** no

**Conflict.** `PHASE_01_INFRASTRUCTURE.md`'s T01.9 task row names five failure modes: *"SSH drop, OOM, crash, partial checkpoint, power loss."* Acceptance criterion 8 requires *"Recovery runbook covers all six failure modes."* The row and the criterion disagree on count.

**Resolution.** The same phase file's Risks section names R-M07 (external SSD failure) as in-scope for Phase 01 specifically because "nothing irreplaceable is stored yet" — and R-M07 isn't covered by any of the five named modes ("crash" is process/host crash, not storage-media failure). Treating SSD/storage failure as the implied sixth mode is the only reading consistent with the rest of the same document, so `RECOVERY_RUNBOOK.md` covers six: SSH drop, OOM, process crash, partial/corrupt checkpoint, power loss, and external storage failure.

**Consequence.** None — this is a documentation completeness question, not a scientific one. Flagging here rather than silently picking a number, per the confusion protocol, since it's a direct textual contradiction rather than a judgment call resolvable purely by reading harder.

**Owner.** Research Lead may override if a different sixth mode was intended.

---

## D-016 — Dependency-lock tool: uv (`requirements.lock.txt`)
**Status:** RESOLVED (2026-09-18, Research Lead) · **Blocking:** yes, for T01.3/T01.5

**Conflict.** `REPRODUCIBILITY_PROTOCOL.md` §6 requires "a committed lock file" but leaves the tool unspecified. `SETUP_PROMPT.md` step 4 names three candidate conventions (`requirements*.lock.txt`, `uv.lock`, `poetry.lock`) without committing to one. This surfaced as a real blocker when Codex's T01.3 (`capture_environment.py`) hit the "dependency-lock hash" field: it can't hash a lock file whose format isn't decided, and correctly stopped rather than guessing.

**Alternatives.** (a) `uv pip compile pyproject.toml -o requirements.lock.txt` — `uv` is already installed on the primary dev machine, `poetry` is not; keeps the existing `setuptools` build backend untouched; smallest change. (b) Full `uv.lock` project (adds `[tool.uv]`, converts the project to uv-managed installs) — more idiomatic uv workflow, but a larger infrastructure change than Phase 01 needs to make right now. (c) `poetry.lock` — requires installing poetry and migrating the dependency spec to poetry's format; biggest change of the three.

**Decision.** **(a).** `requirements.lock.txt`, generated via `uv pip compile pyproject.toml -o requirements.lock.txt`, committed to the repo. The lock hash field in `capture_environment.py`'s fingerprint is `sha256(requirements.lock.txt)` when the file exists, and explicitly reported as absent (not an error) when it doesn't — since T01.4's first environment-capture pass runs *before* T01.5 creates this file (see the phase's own `T01.3 → T01.4 → T01.5` ordering).

**Consequence.** T01.5 ("pin `pyproject.toml`") is now concretely: run `uv pip compile` after the GPU-server driver/CUDA measurement from T01.4, commit `requirements.lock.txt`, and both machines install from it (T01.6). Unblocks T01.3.

**Owner.** Research Lead (this entry).

---

## D-017 — Measured GPU VRAM and system RAM are below SPEC §3.1/§3.5
**Status:** OPEN, substantially clarified (2026-09-18, Research Lead) · **Resolve by:** Phase 06
(before any real training run) · **Blocking:** YES until the A100 access below is confirmed and
scheduled

**Conflict.** T01.4's environment capture on the home GPU server (`capture_environment.py`,
recorded in `ENVIRONMENT_RECORD.md`) measured:

| | SPEC target | Measured |
|---|---|---|
| VRAM (§3.1) | 16–24 GB (RTX 3090/4090, A5000, or equivalent) | **RTX 2060 SUPER, 8 GB** |
| System RAM (§3.5) | ≥32 GB | **15.48 GB** |

This is precisely the scenario `PHASE_01_INFRASTRUCTURE.md` names as a failure condition
("Measured VRAM < 16 GB") and flags as needing Research Lead approval ("patch size if the
benchmark forces a change from 128³ · whether cloud GPU fallback is provisioned now or
deferred") — not something T01.5/T01.7 can silently accommodate on their own. SPEC §3.4 says
96³/128³ patches at batch 1–2 fit "in 16–24 GB VRAM" — at 8 GB, neither patch size is guaranteed
to fit even at batch 1 without measuring (T01.7's job), and the OOM ladder (R-H04:
128³→96³→gradient accumulation→batch 1) may bottom out without headroom to spare. The RAM
shortfall (15.48 GB vs. ≥32 GB) is arguably the more structural problem: it constrains data
loading/preprocessing concurrency independent of anything patch-size tuning can fix.

**Alternatives.** (a) Proceed on this hardware, accepting the OOM ladder's smallest rung (96³,
batch 1, gradient accumulation) once T01.7 actually measures what fits, and treat the RAM
constraint as a data-loader worker-count/prefetch limit rather than a hard blocker — SPEC §3.8
already states compute is not expected to be the real bottleneck for this project, and this may
still hold even at reduced settings. (b) Cloud GPU rental, sanctioned explicitly by SPEC §3.7 as
"a reasonable fallback... not a structural requirement" — a single rented instance (16–24 GB
class) for the training-heavy phases (06, 08, 09, 10), keeping the home GPU server for
CPU-bound/lightweight work. (c) Different/upgraded local hardware before Phase 06.

**Recommendation.** **(a) first, informed by T01.7's actual benchmark**, with **(b) held in
reserve** exactly as SPEC §3.7 frames it — a fallback for intermittent access or a deadline
crunch, not a default. Concretely: T01.5 pins a PyTorch/CUDA build compatible with this GPU's
driver (CUDA 13.2 max, compute capability 7.5/Turing — no compatibility conflict expected, this
GPU is well within range of any current PyTorch build); T01.7 benchmarks 96³/128³ × batch 1/2 on
the *actual* 8 GB card, not the SPEC's assumed 16–24 GB one; whatever config survives that
benchmark is what Phase 06 uses, recorded as a deviation from the SPEC's stated envelope (not
from its scientific claims — patch size and batch size are engineering, not something RQ1–RQ4 or
C1–C6 depend on). If T01.7 shows nothing workable even at batch 1 with gradient accumulation,
that is the trigger for (b), decided then rather than preemptively now.

**Consequence if unaddressed.** Silently training at whatever settings happen not to OOM, without
recording the deviation, would be exactly the kind of unreviewed engineering-driven scientific
change this log exists to prevent (same principle as R-H04's OOM-ladder rule and
`RECOVERY_RUNBOOK.md`'s cross-cutting rule).

**Update (2026-09-18).** The Research Lead confirms the real plan is closer to a variant of (b)
than (a): upcoming NVIDIA Labs access to an **A100** (40/80 GB class — well above the SPEC §3.1
envelope, not just meeting it) is where Phase 06+'s actual training runs happen. The home GPU
server (RTX 2060 SUPER, 8 GB) is *not* the target training environment for the real experiment
grid — it's useful for CPU-bound work, lightweight smoke tests, and exercising the training loop
end-to-end on toy data (exactly what the master plan's §12 "pre-training authorization sequence"
steps 2–4 need — one-sample data test, tiny-batch forward pass, tiny overfit test — none of which
need 16+ GB). T01.7's benchmark on the 8 GB card is still worth running for that purpose, but its
result is no longer the number that decides Phase 06's patch/batch size — the A100's actual specs
are, once that access exists.

**What's still open, not yet resolved by this update.** (i) Timeline: A100 access is described as
"later," not yet provisioned or scheduled — Phase 06 cannot start real training until it exists,
so this remains a genuine blocker for that phase, just a different one than originally framed.
(ii) `REPRODUCIBILITY_PROTOCOL.md` §6 says "both machines install from the same lock" — a third
environment (the A100 cluster) means either a third lock/environment record, or confirming one
lock works across all three, which can't be settled until the A100 environment's own driver/CUDA
is captured via `capture_environment.py` there too, same as T01.4 did for the other two. (iii)
Whether the A100 environment counts as this project's canonical "GPU server" for
`GLIOMA_MACHINE`/run-record purposes, or as a fourth machine class alongside local-mac/gpu-server,
is undecided — matters for `REPRODUCIBILITY_PROTOCOL.md`'s run-record schema field 13 (`gpu_info`).

**Owner.** Research Lead. T01.5 proceeds now (pins a build compatible with both the home GPU's
Turing/CUDA-13.2-max card and, when it exists, an A100 — no known conflict, both are well within
range of any current stable PyTorch release). T01.7 runs on the home GPU as a smoke-test
benchmark, explicitly labeled as not the Phase 06 sizing decision. Points (i)–(iii) above need
Research Lead input once A100 access details are known — flag again then, not now.

---

## D-018 — EGD DUA submission (T02.1) explicitly deferred, not silently missed
**Status:** RESOLVED (2026-09-18, Research Lead) · **Blocking:** no for now — revisit before
Phase 11 · **Resolve by:** before Gate E (Phase 11) at the latest

**Context.** `PHASE_02_DATASET_ACQUISITION.md` frames EGD DUA submission as the phase's single
"DAY-1 ACTION" — the highest-priority item, specifically because its 4–8 week external latency
(R-H01, Health-RI review time) cannot be compressed by working harder on anything else. It is the
one task explicitly designed to start immediately, in parallel with everything else, precisely so
the latency clock starts early.

**Decision.** Research Lead explicitly deferred it (asked directly, answered "not ready to start
EGD yet") rather than it slipping unnoticed. This is a real cost: every week of delay here is a
week added to the critical path before Phase 11 (Gate E, external evaluation authorization) can
close, since EGD is one of the two external test cohorts the SPEC's claims depend on.

**Consequence.** Phase 02 otherwise closes out with 6/9 tasks complete (T02.3–T02.8 done, T02.9
mostly populated) — this is the one open item, and it's open by choice, not oversight.
`DATA_ACCESS_LOG.md`'s EGD section states this explicitly. No other phase is blocked by this deferral
right now — Phase 03 explicitly "does not wait for EGD" per the phase file's own dependency note.
The real deadline pressure lands at Phase 11, not sooner.

**Owner.** Research Lead — resume T02.1 whenever ready; no agent should treat this as something to
chase or escalate on its own.

---

## D-019 — T03.7 ambiguous-label exclusion boundary (UTSW no-IDH, UCSF-PDGM relative co-deletion)
**Status:** RESOLVED (2026-09-18, Research Lead) · **Blocking:** no · **Resolve by:** Phase 03

**Context.** T03.6/T03.2 surfaced two concrete ambiguous-label cases, not a general policy
question — no duplicate or conflicting patient rows exist in either the UTSW or UCSF-PDGM metadata
files (verified directly: 625/625 and 501/501 unique `Subject ID`/`ID` values). The phase file
names both cases explicitly under "Decisions requiring Research Lead approval."

**Decision 1 — 3 UTSW patients with a literal blank/`NA` IDH result** (source TSV rows 140, 141,
171 — row numbers only, no patient ID recorded here per `DATA_GOVERNANCE_PROTOCOL.md` §3).
**Excluded from the cohort manifest entirely**, not just from IDH modeling. IDH is the primary
endpoint; a patient with no IDH result contributes nothing to any analysis this project runs.
Reason code for the exclusion manifest (T03.10): `label:idh_unavailable`.

**Decision 2 — UCSF-PDGM's `relative co-deletion` 1p/19q value (n=6).** **Folded into
`1P19Q_CODELETED`**, consistent with `LABEL_DEFINITIONS.md` §4's existing mapping — this decision
formally resolves that document's "flagged for review" note rather than leaving it open. 1p/19q is
exploratory-only (project invariant), so the practical stakes of this classification are low; no
patient is excluded by this decision, only classified.

**Consequence.** `LABEL_DEFINITIONS.md` updated to remove the "flagged for review" language on
relative co-deletion (now settled). Feeds T03.10's exclusion manifest directly: 3 UTSW patients
excluded (`label:idh_unavailable`); 0 patients excluded by the 1p/19q classification decision.

---

## D-020 — BraTS-2021/TCGA-GBM/TCGA-LGG ID lists: acquisition method and the `openpyxl` dependency
**Status:** RESOLVED (2026-09-18) · **Blocking:** no · **Resolve by:** Phase 03

**Context.** T03.4 (full overlap matrix) and T03.5 (UCSF-PDGM ⇄ BraTS-2021 exclusion) need the
subject-ID rosters of three cohorts not otherwise in hand. TCIA's public REST API
(`getCollectionValues`, `getPatient`) does not index TCGA-GBM, TCGA-LGG, or any BraTS-2021 name
variant — confirmed directly (all return HTTP 200 with a zero-byte body), not assumed from
documentation.

**Method found and verified live (not from memory):**
- **TCGA-GBM / TCGA-LGG** — the GDC API (`api.gdc.cancer.gov/cases`), public, no account, filtered
  by `cases.project.project_id`, field `submitter_id`. Returns the same `TCGA-XX-XXXX` barcode
  format TCIA uses for imaging Patient IDs. Confirmed counts: **TCGA-GBM 617 cases, TCGA-LGG 516
  cases** (all registered GDC cases, not filtered to imaging-only — a safe overinclusion for an
  overlap check, since it can only add candidate IDs, never hide a true overlap).
- **BraTS-2021** — no API; TCIA's DOI wiki page hosts a public attachment,
  `BraTS2021_MappingToTCIA.xlsx` (CC BY 4.0, no DUA, no cookie/auth wall), the official BraTS-ID ⇄
  source-cohort-PatientID crosswalk. Confirmed by opening it: 1,488 rows, columns include `Data
  Collection`, `PatientID on TCIA Radiology Portal`, and `BraTS2021 ID`; 135 rows tagged
  `TCGA-GBM` and 108 tagged `TCGA-LGG`, cross-validating against T03.1's independent finding that
  298 UCSF-PDGM patients have a non-blank `BraTS21 ID` (this file's own `UCSF-PDGM` + additional
  rows total 438, a superset consistent with that count). **Caveat, not silently absorbed:** this
  file covers BraTS-2021's training + validation pool only (~1,480 patients). The official
  challenge **test set is sequestered on Synapse** (`syn25829067`) and is genuinely not obtainable
  through any open API — T03.4's overlap matrix must state this gap explicitly rather than imply
  the BraTS-2021 side of every cell is exhaustively checked.

**Storage.** All three files are raw identifiers "as shipped by the cohort" per
`DATA_GOVERNANCE_PROTOCOL.md` §3 — written to `paths.private_data_dir() / "external_cohort_ids"`
(external SSD, reached through `data/private/`, **not committed**), the same tier UTSW/UCSF-PDGM
raw IDs already use. No patient ID from any of these files appears in this entry or in any
committed file.

**Dependency decision.** The `.xlsx` format has no acceptable non-library parse path. Chose
`openpyxl` (`>=3.1,<4`) over `pandas` — this is a single small, read-only spreadsheet parsed once
into ID lists; pulling in all of pandas for that is unjustified weight. Added to `pyproject.toml`,
`requirements.lock.txt` regenerated via `uv pip compile --universal` (installs and parses correctly
on this machine).

---

## D-021 — UCSF-PDGM's "501 patients" hides 6 duplicate-scan patients and 6 with no imaging at all
**Status:** RESOLVED (2026-09-18, Research Lead) · **Blocking:** no · **Resolve by:** Phase 03

**Context.** Every prior Phase 03 task (T02.6, T02.8, T03.6, T03.8, T03.9, T03.4) reported "UCSF-PDGM
501 patients," because the metadata file has 501 rows and the imaging archive has 501 directories,
and those two counts matched. **Both counts are individually correct and still mask a real
discrepancy underneath them**, found while independently re-verifying T03.5's own two internal
consistency checks (`ucsf_pdgm_input_unique_patient_count`: 501 from metadata vs. 495 from
directories, after correct ID normalization — a gap T03.5's own code surfaced honestly rather than
silently reconciling).

**Finding 1 — 6 patients have two directories, not one** (`UCSF-PDGM-0391`, `-0396`, `-0409`,
`-0429`, `-0431`, `-0433`): each has both a base scan directory (`UCSF-PDGM-NNNN_nifti`) and a
separate follow-up scan directory (`UCSF-PDGM-NNNN_FU<days>d_nifti`, e.g. `_FU016d` = a follow-up
16 days later) — a real second imaging timepoint for the same real-world patient, not a re-upload
or accidental duplicate. T03.8 (duplicate-scan detection, already merged) did not catch this,
correctly by its own design: T03.8 detects byte-identical file content across directories, and a
genuine follow-up scan is not byte-identical to the primary scan — it is a different acquisition.
This is not a bug in T03.8; it is a different category of "duplicate" (same patient, second
timepoint) that a content-hash check structurally cannot see, and it is squarely within T03.8's own
stated scope ("Duplicate-scan detection within cohorts; **retention rule**").

**Finding 2 — 6 different patients have metadata but zero downloaded imaging at all**
(`UCSF-PDGM-0138`, `-0175`, `-0181`, `-0278`, `-0289`, `-0315`, confirmed disjoint from Finding 1's
set). T03.9's "naturally-missing sequence inventory" (501/501 complete, zero missing) did not catch
this either, correctly by its own scope: T03.9 checks *sequence*-level completeness for patients
that *have* a directory; it never checked whether every *metadata* patient has a directory at all.

**Arithmetic, verified directly against both real files:** 501 metadata patients = 489 with exactly
one directory + 6 with two directories (12 directories) + 6 with zero directories. 489 + 12 = 501
raw directories (matches every prior "501" directory count). 489 + 6 + 6 = 501 metadata rows
(matches every prior "501" metadata count). Both widely-cited "501" figures were correct as stated
and still concealed this.

**Consequence for the BraTS-2021 exclusion (T03.5, D-020).** Unaffected — verified directly. The
293-patient exclusion count already normalizes Finding 1's duplicates correctly (both directories
collapse to one canonical ID, no double-counting) and already excludes Finding 2's 6 no-imaging
patients from the overlap count by construction (a patient absent from the downloaded directories
was never a candidate for a directory-based overlap check). No correction needed to D-020 or the
merged exclusion roster.

**Decision 1 — Finding 1's retention rule: keep the baseline scan, exclude the follow-up.**
Research Lead first asked whether using both scans could help the research; answered no, for two
independent reasons specific to how this project actually uses UCSF-PDGM: (a) it is external-test-only,
never a development/training cohort (project invariant) — the usual benefit of multi-timepoint
data (more training examples) doesn't apply to a set that's never trained on; (b) IDH mutation
status is fixed at diagnosis and does not change over a 16–175 day gap, so both scans would carry
an identical label — using both would not add label information, only two correlated images of the
same patient in what must be an *independent*-observations evaluation set. Counting a patient twice
would inflate the reported N and violate the independence assumption underlying every metric this
project reports on UCSF-PDGM (AUROC confidence intervals, DeLong, calibration/AURC), with no
compensating benefit. **All 6 `_FU<days>d` follow-up directories are excluded; the 6 base
directories are retained.** Reason code for the exclusion manifest: `duplicate:followup_timepoint`.

**Decision 2 — Finding 2's 6 no-imaging patients: excluded from the cohort manifest**, as
recommended (a patient without any downloaded imaging cannot be used regardless of label
completeness). Reason code: `no_imaging_available`.

**Owner.** Research Lead — both decisions final. Feeds directly into T03.10 (exclusion manifest uses
these two reason codes) and the final cohort count T03.11/Phase 05 will use — the true UCSF-PDGM
external test set is 495 patients before any other exclusion (D-020's 293 BraTS overlap etc. still
apply on top), not 501.

---

## D-022 — T03.11's committed final cohort manifest carries a hash, not the raw patient roster
**Status:** RESOLVED (2026-09-18) · **Blocking:** no · **Resolve by:** Phase 03

**Context.** `PHASE_03_LEAKAGE_AUDIT.md` lists T03.11 as "Final cohort manifest, SHA-256,
committed" — the one manifest this phase actually commits to Git, unlike every other Phase 03
derived report (which stays on external storage per `DATA_GOVERNANCE_PROTOCOL.md`). The phrase
doesn't itself specify whether the committed file contains the roster of patient IDs or only a hash
of it.

**Resolution — already settled by existing protocol, not decided fresh here.**
`DATA_GOVERNANCE_PROTOCOL.md` §3's identifier-tier table and its explicit instruction ("Restricted
clinical metadata is not committed unless the dataset terms clearly permit it... When in doubt, do
not commit; the manifest can carry a hash instead of a value") already resolve this in the cautious
direction. UTSW-Glioma and UCSF-PDGM are both CC BY 4.0 with no DUA, so redistributing patient IDs
would not be a *license* violation — but this project has not built any separate pseudonymization
scheme, and every other Phase 03 task this far has kept raw/normalized patient IDs off Git
regardless of license permission, treating "permitted by license" and "should be published in a
public repo" as separate questions. Consistency with that established practice, not a new
argument, is the basis for this decision: **the committed `cohort_manifest.json` (T03.11) carries
per-cohort counts, exclusion-reason breakdowns, and a SHA-256 digest of the canonical sorted
patient-ID roster — never the roster itself.** Anyone holding the actual raw data (which the manifest
does not gate access to) can recompute the same digest and confirm the committed manifest matches
exactly which patients were included, without the repository itself ever naming a real patient.

**Owner.** Research Lead — this closes the "committed vs. hashed" ambiguity for T03.11 before it runs.

---

## D-023 — T04.6 needs the UTSW training split, but Phase 05 creates it and requires Phase 04 first
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no (resolved before T04.6) · **Resolve by:** Phase 04

**Conflict.** `PHASE_04_PREPROCESSING.md` T04.6 fits per-modality z-score statistics "exclusively
from the UTSW training split". The split is produced by Phase 05 (T05.2/T05.3), and Phase 05's entry
criteria require Phases 03 and 04 complete with "normalization statistics ... frozen and hashed".
Each phase waits on the other, so as written neither can start its half.

**Alternatives.** (a) Reorder: run the per-patient stages and QC exclusions first, freeze the split
on the post-QC roster, then fit and freeze the normalization statistics on that train set. (b) Compute
a provisional split for the statistics only, then freeze the real split after QC; rejected in
principle because QC exclusions can move patients between splits, so the statistics could include
patients who end up in calibration or internal test — a quiet break of the "training split only" invariant.

**Decision.** (a). Order of work:
1. T04.1–T04.5, T04.7, T04.8 (per-patient, no split needed), then T04.9 visual QC, T04.10–T04.12 and
   QC-based exclusions. The automated z-score range check in T04.8 runs after step 3 (it needs the
   statistics); every other T04.8 check runs before.
2. Phase 05 T05.1–T05.3: power check, patient-level IDH-stratified split on the **post-QC** roster,
   frozen and hashed.
3. T04.6: fit statistics on the frozen UTSW-train partition only, hash and freeze them, apply unchanged
   to every cohort and split. The CLI still refuses any other fitting cohort.

**Phase-file amendments (applied 2026-09-19).** `PHASE_04` T04.6 now follows Phase 05 T05.3 and the
Phase 04 exit criterion moves with it; `PHASE_05` entry criteria drop "normalization statistics ...
frozen"; `PHASE_06` entry criteria add "Phase 04 T04.6 complete".

**Owner.** Research Lead. Phase 05 remains a Research Lead phase whatever `integration_mode` says.

---

## D-024 — Phase 04 preprocessing choices: registration target, skull-stripper, QC exclusion rule
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

The Phase 04 file lists these under "Decisions requiring Research Lead approval".

- **Registration target (T04.2): within-patient T1CE.** T1, T2 and FLAIR are rigidly registered to the
  same patient's T1CE. No template, so no second interpolation and no template-shape bias across cohorts.
  The visual QC overlays (each modality against T1CE) use the same reference.
- **Skull-stripper (T04.3): HD-BET, one pinned release.** The exact version is chosen when it is
  installed, recorded in `ENVIRONMENT_RECORD.md` and the lock, and not changed mid-cohort. Adding
  HD-BET and the imaging libraries (`SimpleITK`, `nibabel`) is a `pyproject.toml` dependency change,
  approved and logged as D-025.
- **QC exclusion rule (T04.12): the phase file's rule, unchanged.** A systematic failure (one parameter
  causes it) is corrected and the affected cases re-run. An individual failure is excluded with a
  `qc:*` reason (`registration-failed`, `skullstrip-over`, `skullstrip-under`, `n4-artifact`,
  `orientation-wrong`, `corrupt`, `modality-mislabelled`). A failure rate above 10% in any cohort stops
  the phase for a systematic investigation before proceeding.
- **Visual QC (T04.9, role B): the Research Lead does it (2026-09-19).** This is the phase file's
  solo fallback for a Person B task: +8 days, and the phase is marked DEGRADED and disclosed (R-M02).
  Collaborators may still be assigned second-reader QC on a subset once overlays exist.
- **Whole-cohort re-run after a systematic failure:** not decided now. It only arises if QC finds a
  systematic failure; the cache (T04.10) makes a re-run cheap, so the default is to re-run affected
  cases only, and a whole-cohort re-run needs a fresh entry.

**Compute note.** Phase 04 is CPU-bound and does not need the A100 (D-017 blocks Phase 06 only). The
SSD is with the Mac and the GPU server is not reachable, so real runs happen on the Mac with limited
workers; the first real-data smoke test (3–5 patients) decides whether the full batch fits there.

**Owner.** Research Lead.

---

## D-025 — Phase 04 imaging dependencies: SimpleITK, nibabel, HD-BET
**Status:** RESOLVED (2026-09-19, Research Lead approval) · **Blocking:** no · **Resolve by:** Phase 04

**Context.** Phase 04 needs volume I/O, rigid registration, N4 bias correction and resampling, and the
HD-BET skull-stripper chosen in D-024. None of these are installed, and `pyproject.toml` dependency
edits are Research-Lead territory (`AGENT_WORKTREE_PROTOCOL.md` §6). Same pattern as D-020's `openpyxl`.

**Decision.** Add `SimpleITK>=2.4,<3` (registration, N4, resampling — one library covers all three, no
separate ANTs/FSL binaries to install on each machine), `nibabel>=5,<6` (NIfTI I/O, orientation) and
`hd-bet==2.0.1` (exact pin: the skull-strip release must not change mid-cohort). The lock was
regenerated with `uv pip compile --universal`.

**Verified.** The lock resolves on the universal target with `torch==2.14.0` and `monai==1.6.0`
unchanged; the environment installs from it; `SimpleITK 2.5.6`, `nibabel 5.4.2` and `hd-bet 2.0.1` import,
and the `hd-bet` CLI starts.

**Consequence.** HD-BET depends on `nnunetv2`, so the lock grows by about 250 lines (batchgenerators,
scikit-image, pandas and others). HD-BET downloads its model weights on first use, which needs network
once per machine and is recorded in `ENVIRONMENT_RECORD.md` when the first real run happens.

**Owner.** Research Lead.

---

## D-026 — UTSW and UCSF-PDGM core volumes are already pre-processed; Phase 04 verifies instead of redoing
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

**Conflict.** `PHASE_04_PREPROCESSING.md` (T04.2, T04.3, T04.5) and D-024 assume raw scans: register
each sequence to T1CE, skull-strip with HD-BET, resample to ~1 mm isotropic. Inspecting the real files
(headers and voxel statistics only, first 60 patients per cohort for geometry, first 40 for alignment)
shows the four core volumes of **both** cohorts are already in a BraTS-style common space:

| Check | UTSW-Glioma (`brain_t1/t1ce/t2/flair`) | UCSF-PDGM (`_T1/_T1c/_T2/_FLAIR`) |
|---|---|---|
| Shape / spacing | 240×240×155, 1.0 mm isotropic (60/60) | 240×240×155, 1.0 mm isotropic (60/60) |
| Orientation | LPS | LPS |
| Data type | float32 | int16 |
| Affine identical across the 4 sequences | 40/40 | 40/40 |
| Non-zero mask overlap across sequences (Dice) | 1.000 (a single shared brain mask) | 1.000 |
| Zero-voxel fraction | ~85% (background outside the brain is zero) | ~84% |

The affine differs between the two cohorts (one distinct affine in each sample), so the grids share
shape and spacing but not necessarily origin metadata. UCSF-PDGM additionally ships `_bias` variants
(N4-corrected by the dataset authors); the adapter uses the non-bias files. UTSW ships `*_ants`
registered variants that the adapter ignores. No claim is made about how the authors produced these
volumes beyond what the headers and voxel statistics show.

**Alternatives.** (a) Verify, do not redo: assert the expected geometry, skull-strip state and
cross-sequence alignment; skip re-registration, HD-BET and resampling on volumes that pass; lossless
LPS→RAS reorientation; uniform N4; run the heavy stages only on a case that fails verification and on
EGD if its files turn out to be raw. (b) Redo everything per the phase file: a second interpolation on
already-resampled data and HD-BET on stripped images. (c) (a) plus rigid refinement on cases whose
measured misalignment exceeds a threshold.

**Decision.** (a). Consequences for Phase 04:
- T04.2/T04.3/T04.5 are built and unit-tested as designed (registration, HD-BET, resample), but the
  production run on UTSW and UCSF-PDGM executes a **verification** for each of them, recorded per case in
  the T04.11 status manifest as `verified-passthrough`, not a transformation.
- A case that fails verification is a QC event: correct and re-run if systematic, exclude with the
  matching `qc:*` reason if individual (D-024's rule). Whether the failure rate exceeds 10% per cohort is
  measured on these verification results.
- T04.4 (N4) still runs, uniformly, on the non-bias volumes of both cohorts, so the two cohorts do not
  differ in bias-field treatment. Using UCSF's `_bias` files for one cohort only was rejected for that reason.
- Orientation: LPS→RAS is done by axis flips only (no interpolation) and asserted after the pipeline
  (acceptance criterion 5).
- HD-BET stays a pinned dependency (D-025) because EGD, and any failing case, may still need it.
- The per-cohort verification reports, not "the pipeline exited 0", are what acceptance criteria 5 and 6
  are checked against; T04.9 visual QC is unchanged.

**Owner.** Research Lead. This changes how Phase 04 is engineered, not what the study asks; the
scientific invariants (normalization from UTSW-train only, zeroed missing modalities, no external labels)
are unaffected.

---

## D-027 — The lock and the local venv are Python ≥3.12 in practice; the project and CI say 3.11
**Status:** RESOLVED (2026-09-19, Research Lead: option (a)) · **Blocking:** no · **Resolve by:** before the Phase 06 environment freeze

**Conflict.** `pyproject.toml` said `requires-python = ">=3.11"` and CI runs Python 3.11, but
`requirements.lock.txt` pins `numpy==2.5.3` and `contourpy==1.4.0`, which need Python ≥3.12
(`uv pip install --python-version 3.11 -r requirements.lock.txt` reports the lock unsatisfiable). The
local venv is Python 3.14. CI installs `.[dev]` rather than the lock, so it resolves `numpy==2.4.6` on
3.11 and passes. Found while reviewing T04.1: once `src/` imports numpy (first true in `preprocessing/`),
local `mypy` fails on numpy 2.5.3's stubs (`type` statement) because `[tool.mypy] python_version = "3.11"`.

**Verified (2026-09-19).** On a fresh Python 3.11 venv with `pip install -e ".[dev]"` (what CI does),
`mypy` reports no issues in 17 files and `pytest tests/unit tests/regression` gives 100 passed, 6 skipped.
`mypy --python-version 3.12` on the local venv is also clean. So the failure is environmental, not a
code defect.

**Alternatives.** (a) Raise `requires-python` to `>=3.12`, CI to 3.12, and keep the lock as is. (b) Keep
3.11 and regenerate the lock with `--python-version 3.11` so it installs everywhere. (c) Set
`[tool.mypy] python_version = "3.12"` only, which fixes local mypy but leaves the unsatisfiable lock.

**Recommendation.** (a): every machine in use (Mac 3.14, GPU server, and the expected A100 environment)
already runs a newer Python, and the lock is what the reproducibility protocol installs from. It is a
`pyproject.toml` and CI edit, so it needs your approval; until then, run local mypy with
`--python-version 3.12`.

**Resolution (2026-09-19).** Option (a) applied: `requires-python = ">=3.12"`, `[tool.ruff] target-version =
"py312"`, `[tool.mypy] python_version = "3.12"`, and Python 3.12 in `gate_a.yml` and `gate_b.yml`. The lock
needed no change (same pins; `uv pip install --dry-run --python-version 3.12 -r requirements.lock.txt`
resolves). Verified on a fresh Python 3.12.14 venv installed the way CI installs (`pip install -e ".[dev]"`,
numpy 2.5.3): full-tree pre-commit passes, `mypy` reports no issues in 17 files, invariants pass, 100 tests
pass with 6 skipped. The local Python 3.14 venv also passes `mypy` without a flag now.

**Owner.** Research Lead.

---

## D-028 — Phase 04 segmentation policy, QC reason codes, and how the visual-QC sample is drawn
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

**T04.7 — which segmentation labels feed the auxiliary head (SPEC §4.3).** Decision: **FeTS labels
only** (`tumorseg_FeTS` for UTSW). Evidence from the real files (sampled, aggregate only): FeTS masks use
the BraTS labels {1, 2, 4}; UCSF-PDGM `tumor_segmentation` uses the same convention; the UTSW
manual-correction masks contain an extra label 3 in 12 of 29 sampled masks (a few are label-3-only) whose
meaning is not documented in anything checked here. FeTS vs registered manual whole-tumour Dice over 24
sampled patients: median 0.986, p10 0.877, min 0.025. Benefits: one label vocabulary, one provenance, 619 of
622 patients, the SPEC's multi-label head, and auxiliary Dice comparable across cohorts. The manual-correction
masks are **not used for training**; they remain available for a later sensitivity check once the label-3
meaning is confirmed against the UTSW-Glioma paper, which is an open follow-up, not a Phase 04 blocker.
Alternatives rejected: best-available manual-else-FeTS (needs a label-3 mapping; a wrong one silently corrupts
subregion targets and mixes two annotation sources) and whole-tumour binary (deviates from the SPEC's
multi-label head).

**No-mask cases.** Three UTSW patients have an all-zero FeTS mask and no manual mask. Decision: **kept** in
the 622-patient cohort for classification; their segmentation loss is masked (zero weight), never imputed.
The cohort manifest and its hashes are unchanged. Phase 06 must implement the masked loss and record the
count of affected patients.

**QC reason codes.** `DATA_GOVERNANCE_PROTOCOL.md` §5 lists `qc:registration-failed`, `qc:skullstrip-failed`,
`qc:corrupt`, `qc:orientation`; the Phase 04 file defines seven failure categories. Decision: reasons are
`qc:<category>` with the phase file's categories (`registration-failed`, `skullstrip-over`, `skullstrip-under`,
`n4-artifact`, `orientation-wrong`, `corrupt`, `modality-mislabelled`); the governance table was updated to match.

**Visual-QC sample (T04.9).** The phase file asks for ≥30 cases "stratified by cohort and IDH status", but
`EXTERNAL_VALIDATION_PROTOCOL.md` blocks any operation that needs the external label column before Gate E.
Decision: IDH stratification is applied to **UTSW only**; UCSF-PDGM cases are drawn by seeded random sampling
without reading its labels. Every borderline case (currently 4) is included regardless.

**Dependency.** `matplotlib>=3.9,<4` was added to `pyproject.toml` for the QC overlay figures. It was already
pinned in the lock (3.11.2) as a transitive dependency of `nnunetv2`, so the resolved environment is unchanged; it is
declared because `src/` imports it directly. Flagged here because dependency edits are Research-Lead territory.

**Owner.** Research Lead.

## D-029 — N4 on volumes with a few negative voxels
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

**Conflict.** The full Phase 04 batch failed N4 for 4 UTSW patients (7 volumes: 3 T2, 3 FLAIR, 1 T1ce) with
`image intensities inside the mask must be positive`. `correct_bias` uses the non-zero voxels as its mask and N4
takes a log, so any voxel below zero inside that mask is rejected. Aggregate measurement on the 7 source volumes:
1 to 68 negative voxels out of about 1.5 million non-zero voxels (at most 4.4e-5), smallest value -0.9 to -511
on volumes whose median is 320 to 7000. That is interpolation ringing already present in the source files
(D-026), not a QC failure category.

**Decision: estimate the field on positive voxels only.** The N4 estimation mask is the non-zero mask restricted
to voxels above zero; the estimated field is still applied to the whole non-zero mask, and negative voxels keep
their sign (they are divided by the field, not clamped). Volumes without negative voxels are unaffected, so the
3,281 volumes already published stay bit-identical and only the 7 failed volumes are recomputed. Alternatives
rejected: clamping negatives to 0 (edits source data, can open holes at the brain edge and change the brain
fraction that QC measures) and excluding the 4 patients (drops 4 of 620 UTSW patients for a reason unrelated to
image quality and needs a reason code outside the 7 approved categories).

**Consequences.** `preprocessing/n4.py` changes and gets a test; `_STAGE_VERSION` is not bumped, because the change
does not alter any output that already exists. The manuscript Limitations note that a few volumes carry
isolated negative voxels left as-is.

**Owner.** Research Lead.

## D-030 — How Phase 04 QC exclusions relate to the frozen Phase 03 manifests (T04.12)
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

**Conflict.** T04.12 says QC failures are "appended to the exclusion manifest", and Phase 05 needs a post-QC
roster. But `build_real_exclusion_manifest()` regenerates the Phase 03 manifest from raw data on every call
(an append to the SSD file would be lost), and the committed `docs/research/manifests/cohort_manifest.json`
(UTSW 622 retained, roster digest pinned by `tests/regression/test_leakage.py`) is the frozen T03.11 artifact.

**Decision: layered.** The Phase 03 exclusion manifest, `cohort_manifest.json`, its digests, and the 622/202
counts in the Phase 03 protocol docs stay as the **pre-QC** record. T04.12 adds (1) a post-QC exclusion manifest
on the SSD, built as the Phase 03 manifest plus one `qc:<category>` row per QC-excluded patient taken from
`preprocessing_status.json` (`append_qc_exclusions`, pure and idempotent-safe), and (2) a committed, roster-free
`docs/research/manifests/cohort_manifest_post_qc.json` with its own roster digests. Phase 05 reads the post-QC
files. Currently 2 UTSW patients (`qc:skullstrip-over`), so UTSW 622 to 620 and UCSF-PDGM 202 unchanged.
Alternative rejected: regenerating `cohort_manifest.json` in place (rewrites a frozen artifact, loses the pre-QC
digest, and changes the regression test and several Phase 03 documents).

**Consequences.** The pre-QC to post-QC drop stays auditable for the paper's cohort-flow figure. A patient with
several QC reasons gets one row whose reason joins the sorted reasons with `+`. The Phase 03 accounting checks in
the manifest describe the pre-QC state and are left unchanged. The 10% per-cohort stop rule (D-024) is enforced
by the builder script, which refuses to write when it is exceeded.

**Owner.** Research Lead.

## D-031 — Recalibrating the automated brain-fraction screen after a human-caught miss (T04.9)
**Status:** RESOLVED (2026-09-19, Research Lead) · **Blocking:** no · **Resolve by:** Phase 04

**Conflict.** The Phase 04 file requires: if automated QC misses failures the human catches, thresholds are
recalibrated before the full run is trusted. Visual QC of 77 overlays found 2 UTSW failures. The screen flagged one
(`qc_0030`, brain fraction 0.0526, below the 0.08 borderline bound) and missed the other (`qc_0055`, 0.1002).
Aggregate sensitivity over all cases (per-case verification file): UTSW cases below a lower bound of 0.08 / 0.10 /
0.11 / 0.12 / 0.15 = 2 / 6 / 20 / 32 / 205; UCSF-PDGM = 0 / 0 / 0 / 1 / 18. Of the UTSW cases below 0.11, 16 of 20 were
already reviewed (14 pass, 2 fail). Fragmentation, convex-hull solidity and closing gain did not separate the miss
from passing cases.

**Decision: raise `borderline_min_brain_fraction` from 0.08 to 0.11** (the automated `failed` bound stays 0.05) and
have the Research Lead review the newly flagged unreviewed cases (4 UTSW, 0 UCSF). Every case below 0.11 is then
human-reviewed. The bound comes from one observed failure, so it is **provisional** and is reported as such: it is not
a validated operating point, and the QC report gives the sensitivity table instead of a sensitivity estimate (the
reviewed sample was selected on the tails). Alternatives rejected: 0.12 (14 more overlays for a wider margin around
one miss) and keeping 0.08 (leaves 4 unreviewed UTSW cases at 0.103 to 0.11 beside the miss and leaves the phase rule
unmet).

**Consequences.** Re-run verification and the status merge; the merge resets a verdict when a case's verification
outcome changes, so the 14 existing passes and the `qc_0055` fail are re-applied from the archived review sheet (same
images, same human verdict, recorded transparently). `make_qc_overlays.py` gains an incremental mode that appends
overlays for newly borderline cases without regenerating existing files. Manuscript Limitations state that the
automated screen missed one failure and was recalibrated on it.

**Update (2026-09-19, Research Lead): bound raised again, 0.11 to 0.12.** Reviewing the 4 cases newly flagged at 0.11
found 2 more failures (`qc_0078`, `qc_0080`, brain fractions 0.108 and 0.109, both `qc:skullstrip-over`), so failures now
sit at 0.100, 0.108 and 0.109, against the 0.11 bound. Among UTSW cases below 0.11, 4 of 20 failed; the 12
UTSW cases in [0.11, 0.12) have 3 reviewed passes and 9 unreviewed. Decision: raise `borderline_min_brain_fraction`
to **0.12** and review the 9 unreviewed cases; extend again only if failures appear in the new band. The bound stays
provisional. UTSW exclusions are now 4 of 622 (0.64%), far below the 10% stop threshold; UCSF-PDGM 0 of 202.

**Update 2 (2026-09-19, Research Lead): bound raised to 0.13, with a stopping rule.** The 9 cases newly flagged at 0.12
gave 1 more failure (`qc_0089`, brain fraction 0.115, `qc:skullstrip-over`; 8 passes), so failures reach into the
0.11 to 0.12 band (1 of 12 reviewed). Failure density by band is falling: 4 of 20 below 0.11, 1 of 12 in 0.11 to 0.12.
A left-right mask-asymmetry screen was tried as an alternative detector and rejected: the 5 failures rank 1, 11, 23,
44 and 75 of 90 reviewed cases, so it does not separate them. Decision: raise `borderline_min_brain_fraction` to
**0.13** and review the unreviewed UTSW cases in [0.12, 0.13). **Stopping rule (fixed now):** stop extending as soon
as one full 0.01 band has zero failures; if a band has a failure, extend by one more 0.01 band. Cases above the final
bound were reached only through the random and stratified samples (0 failures in 24 UTSW random draws). UTSW
exclusions: 5 of 622 (0.80%), UCSF-PDGM 0 of 202, far below the 10% stop threshold.

**Update 3 (2026-09-19, Research Lead): sequential extension ends at 0.13; residual failure rate is measured by a random sample.**
The 25 cases in [0.12, 0.13) gave 1 failure (`qc_0105`, brain fraction 0.129, `qc:skullstrip-over`; 24 passes), so the
stopping rule of update 2 (stop after a band with no failure) would extend to 0.14, but band sizes grow (UTSW cases
unreviewed: 50 in [0.13, 0.14), 80 in [0.14, 0.15), 111 in [0.15, 0.16)) while density stays near 4% per band, so the rule has no
economical end point. Decision: `borderline_min_brain_fraction` stays at **0.13**; the Research Lead reviews a seeded
random sample of **40** UTSW cases from above 0.13 (`verified-passthrough`, not yet reviewed), reason `residual_sample`.
The QC report gives the observed failures and an exact (Clopper-Pearson) one-sided 95% upper bound for the failure
rate above 0.13, from the residual sample alone and from all randomly selected reviewed cases above 0.13 (22 earlier
IDH-stratified UTSW draws, 0 failures, plus the 40). These are estimates of residual risk for the Limitations section,
not thresholds. Unreviewed cases above 0.13 stay in the cohort. UTSW exclusions: 6 of 622 (0.96%), UCSF-PDGM 0 of 202.

**Owner.** Research Lead.

## D-032 — One mask-alignment audit finding accepted as a boundary effect (Phase 04 output audit)
**Status:** RESOLVED (2026-09-19, Claude; confirmed by the Research Lead at the T04.9 sign-off) · **Blocking:** no · **Resolve by:** Phase 04

**Conflict.** `scripts/audit_preprocessing_outputs.py` (thresholds set in advance: at least 0.99 of non-zero mask voxels
inside the T1ce non-zero footprint) passes every check on all 818 cases (616 UTSW + 202 UCSF-PDGM, 3,272 volumes, masks) except this
one for 1 UTSW case: 0.9889 of its mask lies inside the footprint. The mask and volume grids are identical for that case
(the exact shape and affine check passed for all 616 UTSW cases).

**Finding.** The mask has 146,572 voxels (a very large tumour reaching the brain surface); 1,625 lie outside the T1ce
footprint, at a median of 1 voxel and a maximum of 2.2 voxels from its edge (only 4 voxels are more than 2 voxels
out). That is the skull-strip boundary cutting 1 to 2 voxels into a tumour that touches the surface, not a
misalignment.

**Decision.** Keep the case, keep the audit threshold and the failing audit result unchanged (the threshold is not
loosened after seeing the case), and record this exception here. `preprocessing_output_audit.json` therefore shows
`passed: false` with exactly this one supplementary-check failure and nothing else. The alignment criterion
(acceptance criterion 6) rests on the exact grid equality (616/616 UTSW, 202/202 UCSF-PDGM) and on the visual overlays.
Alternative rejected: switching the check to a distance-tolerant form now, which would be a threshold change chosen
after observing the data. If a later phase wants that form it should be pre-specified.

**Owner.** Research Lead.

New decisions append here using the same structure: conflict → alternatives → consequences → recommendation → owner → resolve-by phase. Any deviation from the SPEC's scientific content — as opposed to its engineering — requires an entry and Research Lead approval before it takes effect.
