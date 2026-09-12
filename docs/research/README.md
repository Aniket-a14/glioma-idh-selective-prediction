# Research Planning Corpus

Planning documents for **Calibrated Selective Prediction for MRI-Based Glioma IDH Classification under Missing Modalities and Cross-Institutional Domain Shift**.

---

## The two sources of truth

| Document | Governs | Location |
|---|---|---|
| `glioma-idh-selective-prediction-research-specification.md` | **The science.** Endpoints, RQs, claims, datasets, methodology, novelty boundary. | repository root |
| `MASTER_RESEARCH_EXECUTION_PLAN.md` | **The execution.** Phases, gates, agents, storage, firewall, publication. | here |

The specification freezes *what* question is being answered. This corpus governs *how* it gets answered. **Engineering improvements do not require a specification change; scientific changes do** — and those go through `DECISION_LOG.md` with Research Lead approval.

---

## Reading order

**If this is a new machine** (fresh clone, new collaborator, the GPU server): `prompts/SETUP_PROMPT.md` first — "read this and set up the system." Everything below is about the science and the process, not the environment.

**If you are one of the team's other collaborators picking up small side-work** (not a research phase): `CONTRIBUTOR_TASKS.md` + `prompts/CONTRIBUTOR_PROMPT.md` — "read this and pick up a task." You don't need anything else on this page.

**If you are new to the project**, read in this order:

1. `MASTER_RESEARCH_EXECUTION_PLAN.md` §1–8 — objective, RQs, claims, datasets, invariants. *(20 min)*
2. `DECISION_LOG.md` — the known ambiguities, several of which block early phases. *(15 min)*
3. `EXTERNAL_VALIDATION_PROTOCOL.md` — the single easiest way to destroy this project. *(10 min)*
4. The phase file for whatever you are about to work on.

**If you are about to write code:** `AGENT_WORKTREE_PROTOCOL.md` (directory ownership, branch naming) and the master plan §21–22 (quality and testing strategy).

**If you are about to touch data:** `DATA_GOVERNANCE_PROTOCOL.md` in full, before downloading anything.

**If you are about to run an experiment:** `REPRODUCIBILITY_PROTOCOL.md` §1 (the twenty-field run record) and Gate C in the master plan.

---

## Document map

| Document | Authoritative for |
|---|---|
| `MASTER_RESEARCH_EXECUTION_PLAN.md` | Project-level view; 30 sections; the critical path |
| `SPEC_TRACEABILITY_MATRIX.md` | Every RQ/claim → artifact → manuscript element. Prevents requirements silently disappearing. |
| `DECISION_LOG.md` | Every deviation, ambiguity, and judgement call. **Append here rather than resolving silently.** |
| `AGENT_WORKTREE_PROTOCOL.md` | Claude/Codex division, branches, worktrees, merge order, directory ownership |
| `DATA_GOVERNANCE_PROTOCOL.md` | Provenance chain, ID tiers, overlap audit, exclusion vocabulary, splitting rules |
| `EXTERNAL_VALIDATION_PROTOCOL.md` | The firewall; Gate E; what "operational access" means vs. "performance access" |
| `REPRODUCIBILITY_PROTOCOL.md` | Run records, tracking, seeding, prediction artifacts, the release package |
| `RISK_REGISTER.md` | Live risks; and which "bad" outcomes are findings rather than failures |
| `PUBLICATION_PLAN.md` | Venue, framing, differentiation, checklists, submission→publication |
| `phases/PHASE_NN_*.md` | Task-level detail for one phase |
| `PROJECT_STATE.md` | **Where the project is right now.** Agents read it first and update it last. |
| `prompts/CLAUDE_PHASE_PROMPT.md` | Self-advancing prompt — invoke with "read this and continue working" |
| `prompts/CODEX_PHASE_PROMPT.md` | Same, for Codex's tasks; never advances the phase |
| `prompts/SETUP_PROMPT.md` | Any collaborator, any machine, any AI agent — invoke with "read this and set up the system" to get a fresh clone to the same working environment as everyone else's |
| `CONTRIBUTOR_TASKS.md` | Standing backlog of small, bounded, off-critical-path work for the team's other collaborators |
| `prompts/CONTRIBUTOR_PROMPT.md` | Any collaborator, any AI agent — invoke with "read this and pick up a task" |
| `prompts/WEEKLY_STATUS_PROMPT.md` | Generates the Friday capstone demo report — invoke with "read this and generate this week's update" |

---

## Quality gates

| Gate | When | Blocks on |
|---|---|---|
| **A** | Every commit | Format, lint, typing on touched code, fast unit tests, secret scan |
| **B** | Every merge to `main` | Full CPU suite, integration tests, complexity review, security/dependency checks, docs updated |
| **C** | Before any scientific run | Clean tree, valid config, frozen manifest hashes, environment recorded, smoke test passed, storage available, checkpoint path valid |
| **D** | Phase completion | Every acceptance criterion met, artifacts generated, docs updated, independent review |
| **E** | **External evaluation authorization** | The strictest gate. Passed exactly once. Signed freeze manifest. |
| **F** | Results/publication freeze | Results immutable, statistics final, figures/tables regenerable, every claim traces to evidence |

---

## The three things that would invalidate this project

1. **Patient-level leakage** across UTSW / UCSF-PDGM / EGD / BraTS / TCGA.
2. **Looking at external performance before Gate E** — voids claim C4 outright.
3. **Scope creep into architecture search** — the specification names this as the project's main risk.

Most of the machinery in this corpus exists to make those three procedurally hard.

---

## Standing scientific rule

**Negative results are valid results.** If selective prediction fails under shift — non-monotonic risk–coverage curves, coverage collapse, calibration degradation — that is the finding, and it is publishable. No experiment is re-run, re-tuned, or re-scoped because its outcome refutes a claim. The falsification table in the master plan §4 is the pre-registered commitment against that temptation.

---

## Current status

Plan version 1.0. **Phase 00 not started.** Repository contains this corpus and a directory skeleton; no research functionality is implemented.

Next action: open a session and say *"read `docs/research/prompts/CLAUDE_PHASE_PROMPT.md` and continue working."*
Current position is tracked in [`PROJECT_STATE.md`](PROJECT_STATE.md).
