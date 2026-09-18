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
**Status:** OPEN · **Resolve by:** Phase 03 · **Blocking:** YES

**Conflict.** SPEC §9 step 1 instructs: *"independently verify (do not trust this document alone) the exact per-marker IDH/1p19q/MGMT counts by parsing the actual clinical-metadata files."* Yet the SPEC's own counts (625 patients, IDH 622 = 176/446, 1p19q 335 = 63/272, UCSF 501, EGD 774/467) are quoted throughout as if settled — and there is an internal wobble already: 625 patients but IDH n=622, which implies 3 unlabelled cases whose disposition is unspecified.

**Recommendation.** Treat every count as **provisional** until Phase 03 emits a hashed, verified cohort manifest. The plan must make cohort sizes a *verified artifact*, never a hard-coded constant — no count from the SPEC may be written into source code or a config. Phase 03's acceptance criterion is a table of SPEC-claimed vs. file-verified counts with every discrepancy explained. If verified counts differ materially (especially 1p/19q), D-007's power assumptions and Phase 05's split sizing are revisited before the freeze.

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

## Ongoing entries

New decisions append here using the same structure: conflict → alternatives → consequences → recommendation → owner → resolve-by phase. Any deviation from the SPEC's scientific content — as opposed to its engineering — requires an entry and Research Lead approval before it takes effect.
