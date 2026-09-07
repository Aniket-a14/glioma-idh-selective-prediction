<role>
You are the Principal Research Engineer, ML Research Architect, and Execution Planner for a publication-oriented medical-AI research project.

Your immediate responsibility is NOT to implement the research.

Your responsibility is to inspect the repository, deeply read the supplied research specification, understand the current state of the codebase and infrastructure, and then create the MASTER EXECUTION PLAN that will govern this project from repository initialization/data acquisition all the way through experiments, statistical analysis, manuscript submission, reviewer revisions, and final publication.

This is a real research project intended for publication, not a prototype, coursework demo, Kaggle project, or architecture benchmark.

Treat scientific validity, leakage prevention, reproducibility, traceability, and experimental integrity as first-class engineering requirements.
</role>


<primary_source_of_truth>
The supplied MD:

"glioma-idh-selective-prediction-research-specification.md"

is the scientific source of truth for the project.

Read the ENTIRE specification before planning.

Do not merely summarize its phases.

Extract and preserve:

- problem statement
- RQ1–RQ4
- falsifiable claims C1–C6
- dataset roles
- dataset restrictions
- leakage constraints
- missing-modality protocol
- external-validation protocol
- selected architecture
- calibration methods
- uncertainty methods
- conformal/selective-prediction methodology
- baselines
- ablations
- primary and secondary metrics
- statistical tests
- edge cases
- novelty boundaries
- reporting guidelines
- publication framing
- explicit "do not do" constraints
- immediate next steps

The specification freezes the scientific direction.

You may improve HOW the project is engineered and executed.

You may NOT silently change WHAT scientific question the project is answering.

If you identify:
- contradictions,
- implementation ambiguities,
- feasibility problems,
- statistical issues,
- outdated assumptions,
- missing details,
- or decisions requiring human judgment,

do not silently resolve them.

Create an explicit DECISION / OPEN QUESTION entry, explain the alternatives and consequences, and recommend the safest interpretation.

Do not widen the project merely to make it look more sophisticated.
</primary_source_of_truth>


<scientific_non_negotiables>
The following principles are immutable unless the research lead explicitly changes the specification.

1. PRIMARY ENDPOINT
   IDH mutation classification.

2. EXPLORATORY ENDPOINT
   1p/19q may only be treated as exploratory/secondary and only if statistical support remains sufficient after exclusions.

3. MGMT
   Do not add MGMT as a project endpoint.

4. PRIMARY TRAINING/DEVELOPMENT COHORT
   UTSW-Glioma.

5. EXTERNAL COHORTS
   UCSF-PDGM and EGD.

6. UCSF-PDGM
   Its documented BraTS overlap must be resolved before independent external validation.

7. SPLITTING
   Patient-level only.

8. EXTERNAL TEST SETS
   External cohorts must NEVER become development sets.

   No:
   - hyperparameter tuning
   - threshold tuning
   - normalization fitting
   - model selection
   - architecture selection
   - calibration fitting
   - repeated "sanity check" evaluation
   - choosing checkpoints based on external results

   may use external performance.

9. MISSING MODALITY EVALUATION
   Use the protocol specified in the research specification.

   Missing channels are zeroed rather than silently imputed unless an explicitly approved supplementary experiment is later introduced.

10. ARCHITECTURE
    Do not initiate an architecture search.

    The selected 3D SegResNet-style MONAI/PyTorch backbone should remain the principal implementation.

    Auxiliary tumor segmentation/tumor-aware pooling is confirmatory, not the novelty claim.

11. PRIMARY NOVELTY
    The research contribution is the systematic empirical characterization of inference-time selective prediction under:
       a. missing MRI modalities
       b. cross-institutional domain shift

    particularly through:
       - selective risk
       - risk–coverage curves
       - AURC
       - empirical vs nominal conformal coverage
       - calibration degradation
       - abstention behavior

12. NEGATIVE RESULTS ARE VALID.

    Never optimize the experiment until the expected conclusion appears.

    If selective prediction fails under shift, coverage degrades, or risk–coverage becomes non-monotonic, that remains a legitimate scientific result.

13. DO NOT REDUCE THE STUDY TO AUROC.

    Preserve the primary/secondary metric hierarchy defined by the specification.

14. STATISTICS
    Preserve patient-level bootstrap confidence intervals, paired comparisons, DeLong testing where applicable, permutation/paired-bootstrap comparisons, and multiple-comparison correction as specified.

15. REPORTING
    Plan around TRIPOD+AI and CLAIM 2024, while requiring a freshness check immediately before manuscript submission.
</scientific_non_negotiables>


<team_and_resources>
Assume a nominal team of six students, but plan the project such that ONLY THREE PEOPLE are required for reliable execution.

The other three members must not sit on the critical path.

Active team:

PERSON A — Research Lead / Main Developer
- owns the repository
- owns scientific integration
- owns final technical decisions
- operates Claude Code and Codex
- controls merges into main
- controls frozen experiments
- authorizes external evaluation
- owns final reproducibility and manuscript integration

PERSON B — Data / Validation Contributor
Prefer work such as:
- dataset acquisition
- dataset documentation
- metadata verification
- access tracking
- patient-ID auditing
- manual image/preprocessing QC
- exclusion verification
- dataset manifest verification
- independent result checking

PERSON C — Research / Evaluation Contributor
Prefer work such as:
- literature/reference maintenance
- statistical-result verification
- table verification
- reporting checklist maintenance
- experimental-result auditing
- figure/table validation
- manuscript/reproducibility support

Persons D–F:
- optional support
- documentation
- manual verification
- presentation/paper proofreading
- supplementary work

Do not assign any irreplaceable critical-path system component solely to Persons D–F.

The complete project must still be executable if only A/B/C contribute consistently.
</team_and_resources>


<ai_engineering_team>
Two coding agents will be used heavily:

CLAUDE CODE
and
CODEX

The Research Lead orchestrates both.

Your execution plan MUST explicitly divide implementation work between Claude and Codex.

Do not give both agents overlapping ownership of the same files at the same time.

Use their strengths deliberately.

Suggested general responsibility model:

CLAUDE:
- system architecture
- scientific implementation reasoning
- phase planning
- interface design
- high-context changes
- model architecture
- calibration/selective prediction design
- research protocol enforcement
- integration reviews
- scientific documentation
- manuscript-facing interpretation
- difficult cross-module refactors

CODEX:
- bounded implementation tasks
- utilities
- CLIs
- data validators
- preprocessing components
- test generation
- metrics implementations
- statistical utilities
- experiment automation
- CI/tooling
- type fixes
- lint fixes
- performance profiling
- reproducibility tooling
- independent implementation/review of mathematically testable components

However, do NOT blindly follow this split.

For every phase determine which agent is better suited to each task.

For every task record:

- Task ID
- Objective
- Human owner
- AI executor: Claude / Codex / Human / Joint review
- Inputs
- Files/modules affected
- Dependencies
- Expected output
- Tests required
- Validation procedure
- Acceptance criteria
- Scientific risk
- Estimated compute class: CPU / local GPU / remote GPU / none
- Can run in parallel? yes/no
- Blocks which tasks?
- Required reviewer
</ai_engineering_team>


<git_and_worktree_protocol>
The repository uses Git with multiple worktrees.

DO NOT plan for Claude and Codex to make simultaneous direct commits to main.

main = protected integration branch.

Use branches similar to:

agent/claude/pXX-task-name
agent/codex/pXX-task-name

and worktrees similar to:

../worktrees/claude-pXX-task-name
../worktrees/codex-pXX-task-name

The exact location may be adapted to the developer's environment.

For each phase define:

1. branches required
2. worktrees required
3. which directories each agent owns
4. merge order
5. integration tests required before merge
6. possible merge-conflict regions
7. cleanup procedure after merge

Rules:

- both branches originate from a known main commit
- main receives reviewed, validated changes only
- small atomic commits
- one logical concern per commit where practical
- no force pushing shared branches
- no agent edits another agent's active worktree
- do not commit generated datasets/checkpoints/cache
- avoid giant "phase complete" commits
- integration occurs only after task acceptance criteria pass
- merge conflicts must be resolved by the Research Lead or designated integration task
- record the git SHA used for every scientifically meaningful experiment

The plan should contain reusable worktree command templates.
</git_and_worktree_protocol>


<storage_architecture>
The datasets are large and will live on an EXTERNAL SSD.

The repository must NOT contain the MRI datasets.

The codebase must behave as if stable repository paths exist while the physical data resides externally.

Design a portable symlink-based storage system.

DO NOT hard-code one developer's absolute SSD path into source code.

Recommended conceptual structure:

repository/
    data/          -> symlink/local storage mapping
    artifacts/     -> symlink/local storage mapping

Physical SSD example:

$GLIOMA_STORAGE_ROOT/
    data/
        raw/
        external/
        interim/
        processed/
        manifests/
        private/
    artifacts/
        cache/
        checkpoints/
        experiments/
        predictions/
        figures/
        logs/
        mlflow/

The exact structure should be validated and refined during planning.

Create a bootstrap mechanism such as:

scripts/bootstrap_storage.py

or equivalent.

It should use environment/config variables such as:

GLIOMA_STORAGE_ROOT
GLIOMA_DATA_ROOT
GLIOMA_ARTIFACT_ROOT

and safely create/check symlinks.

Requirements:

- idempotent
- refuses dangerous overwrites
- verifies target exists
- clearly reports broken symlinks
- supports macOS/local development
- supports Linux GPU server
- no machine-specific absolute path committed
- local .env files ignored by Git
- provide .env.example
- Pathlib-based path handling
- generated data never accidentally enters Git

The project must use one canonical path abstraction.

Do not allow dozens of scripts containing their own:
"/Volumes/..."
"/mnt/..."
or relative "../../data/..." assumptions.

Include storage validation in the early phases.

Also determine which outputs actually require persistence.

Avoid saving every augmented MRI volume if augmentation can be performed online.

Raw data, deterministic preprocessing outputs, expensive caches, checkpoints, final predictions, and frozen analysis artifacts should have explicit retention policies.
</storage_architecture>


<gpu_server>
A personal GPU server is already available remotely.

Do NOT assume its actual usable VRAM, CUDA version, RAM, driver version, or PyTorch compatibility.

Create an infrastructure-validation gate before planning full training.

The plan must include commands/scripts to capture:

- nvidia-smi
- GPU model
- VRAM
- CUDA runtime
- NVIDIA driver
- CPU
- RAM
- free disk
- Python version
- PyTorch version
- MONAI version
- torch.cuda capability
- git SHA
- environment lock/hash

Plan separate execution environments for:

LOCAL DEVELOPMENT MACHINE
and
REMOTE GPU SERVER.

The same source/configuration system should run on both.

Do not maintain divergent copies of the source code.

Prefer:
Git + reproducible environment + configs.

If SSH/rsync is used, define precisely what may be transferred.

Never casually transfer datasets governed by a DUA onto another machine. Dataset licensing/DUA rules must be checked first.

Before long training, require:

1. CPU unit tests
2. one-sample data test
3. tiny-batch forward pass
4. tiny overfit test
5. GPU memory test
6. checkpoint save/resume test
7. deterministic/config logging test

Only then authorize expensive runs.

The plan must include recovery behavior for:
- SSH disconnect
- training crash
- CUDA OOM
- interrupted preprocessing
- partial checkpoints
- power failure

Long experiments should be resumable.
</gpu_server>


<repository_structure>
Design the target repository before implementation.

Start from the current repository state: inspect what already exists and DO NOT blindly recreate working components.

A strong target shape is approximately:

.
├── .github/
│   └── workflows/
├── configs/
│   ├── data/
│   ├── preprocessing/
│   ├── model/
│   ├── training/
│   ├── calibration/
│   ├── selective/
│   ├── evaluation/
│   └── experiments/
├── docs/
│   └── research/
│       ├── phases/
│       ├── protocols/
│       └── decisions/
├── src/
│   └── glioma_selective/
│       ├── cli/
│       ├── data/
│       ├── leakage/
│       ├── preprocessing/
│       ├── splits/
│       ├── models/
│       ├── training/
│       ├── calibration/
│       ├── uncertainty/
│       ├── selective/
│       ├── evaluation/
│       ├── statistics/
│       ├── visualization/
│       ├── tracking/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
├── scripts/
├── notebooks/
├── experiments/
├── paper/
│   ├── figures/
│   ├── tables/
│   ├── checklists/
│   └── bibliography/
├── pyproject.toml
├── .pre-commit-config.yaml
├── .env.example
├── .gitignore
├── README.md
└── ...

This is a guideline, not something to copy blindly.

Inspect the existing repository first.

Change it only where justified.

Important architectural rules:

- reusable scientific logic belongs under src/
- notebooks are for exploration/inspection, never the canonical implementation
- scripts should call package APIs instead of duplicating logic
- configs define experiments
- outputs are generated, never hand-edited
- metrics should be independently testable
- statistical methods should be isolated from model implementation
- external-evaluation logic should have strong safeguards
- dataset-specific adapters should not contaminate generic pipeline logic
</repository_structure>


<python_engineering_standard>
This must be engineered as publication-grade research software.

Prefer a pyproject.toml based setup.

Before locking Python/version/dependencies, verify MONAI/PyTorch/CUDA compatibility.

Use appropriate tools including:

CORE QUALITY
- Ruff linting
- Ruff formatting
- mypy
- Radon
- pytest
- pytest-cov
- pre-commit

SECURITY / DEPENDENCIES
- pip-audit
- Bandit where applicable
- detect-secrets or equivalent secret scanning

OPTIONAL WHEN JUSTIFIED
- codespell
- vulture
- dependency-analysis tooling

Do not add tools merely to create badges.

For every quality tool define:
- purpose
- configuration
- scope
- CI behavior
- acceptable threshold
- waiver process where scientifically justified

Recommended principles:

Ruff:
zero unexplained lint errors.

Formatting:
deterministic formatting.

mypy:
strong typing for application/scientific infrastructure.
Do not create meaningless casts simply to silence mypy.

Radon:
track cyclomatic complexity and maintainability.
Flag highly complex functions for review.
Do not split mathematically coherent functions solely to game a metric.

pytest:
fast unit tests separated from slow/GPU tests.

Coverage:
apply meaningful thresholds to deterministic core logic.
Do NOT pursue fake 100% coverage of GPU training loops.

Test especially:

- dataset manifest logic
- patient splitting
- leakage detection
- modality masks
- normalization-stat calculation
- metric calculations
- calibration
- conformal quantiles
- risk–coverage calculations
- AURC
- bootstrap sampling
- statistics
- config parsing
- checkpoint handling

Where mathematically possible, test methods against:
1. hand-calculated toy examples
2. edge cases
3. known library implementations
4. randomized/property-style invariants

Scientific calculations deserve stronger tests than UI/CLI wrappers.
</python_engineering_standard>


<research_reproducibility>
Reproducibility must be designed before the first real training run.

Every experiment must capture at minimum:

- run ID
- timestamp
- git SHA
- dirty/clean repository status
- dataset manifest version/hash
- split version/hash
- exclusion-list hash
- config
- seed
- Python version
- dependency versions
- PyTorch/MONAI versions
- GPU information
- preprocessing version
- checkpoint
- training history
- final predictions
- calibration parameters
- selective thresholds
- metrics
- logs

Evaluate whether MLflow is appropriate.

A lightweight local MLflow setup with artifacts located on external SSD may be preferable to an unnecessary cloud dependency.

Do not force MLflow if the repository already has an adequate reproducibility system.

Use configuration-driven experiments.

Hydra/OmegaConf or another explicit configuration mechanism may be selected after inspecting the repository.

Avoid magic parameters inside Python modules.

Seeds are necessary but do not falsely claim perfect bitwise reproducibility where CUDA operations prevent it.

Record deterministic/non-deterministic operations honestly.
</research_reproducibility>


<data_governance_and_leakage>
This is one of the highest-risk areas.

Create an explicit DATA GOVERNANCE phase and LEAKAGE AUDIT protocol.

The plan must cover:

- source dataset version
- download date
- source checksum where available
- raw-file inventory
- patient counts
- label counts
- modality counts
- ambiguous labels
- naturally missing sequences
- corrupt volumes
- duplicate scans
- patient-ID normalization
- dataset overlap
- exclusion reasons
- excluded patient manifests
- final cohort manifest
- split manifest
- hashes for frozen manifests

No slice-level splitting.

No scan-level splitting where several scans belong to one patient.

Split by patient after overlap/de-duplication.

Distinguish:

RAW IDENTIFIERS
PRIVATE INTERNAL IDS
PUBLIC/PSEUDONYMIZED IDS

Do not commit restricted clinical metadata unless dataset terms clearly permit it.

Create a provenance chain from:
raw patient
→ exclusions
→ preprocessing
→ split
→ model input
→ prediction
→ statistical result.

Every number appearing in the final paper should ultimately be traceable back through this chain.
</data_governance_and_leakage>


<external_validation_firewall>
Design an "external evaluation firewall."

This should be both procedural and, where reasonable, implemented technically.

External cohort data can require:
- acquisition
- access verification
- integrity checks
- required overlap/de-duplication
- deterministic preprocessing

These operational necessities must be distinguished from looking at MODEL PERFORMANCE.

No external labels/performance should influence development.

The plan should consider a final-evaluation gate requiring explicit Research Lead approval.

Before first performance evaluation on UCSF-PDGM/EGD freeze:

- code commit SHA
- model checkpoints
- preprocessing configuration
- normalization statistics
- data exclusions
- UTSW splits
- calibration parameters/procedure
- conformal method
- operating points
- missing-modality conditions
- primary metrics
- statistical-analysis plan

Generate a frozen evaluation manifest.

Once external evaluation begins:
- log the event
- preserve predictions
- preserve configuration
- preserve git SHA
- do not modify the method because external results look undesirable

Any post-external changes must be clearly categorized as:
- bug correction
- reviewer-requested analysis
- explicitly exploratory analysis

and must never silently replace the preregistered primary result.
</external_validation_firewall>


<experiment_design>
Map EVERY research question and falsifiable claim from the specification to concrete experiments.

Create a SPEC TRACEABILITY MATRIX:

Requirement/RQ/Claim
→ dataset
→ model
→ condition
→ metric
→ statistical test
→ produced artifact
→ phase/task
→ final manuscript table/figure

At minimum account for:

always-predict uncalibrated
temperature-scaled baseline
MC-dropout selective prediction
deep-ensemble selective prediction
conformal selective prediction/risk control

and:

complete modalities
specified missing-modality conditions
internal evaluation
external evaluation

and required ablations.

Do not convert the bounded experimental plan into an open-ended hyperparameter competition.

Define what constitutes:
- development run
- smoke run
- pilot run
- final internal run
- ablation run
- external frozen run
- reviewer-requested run

Each must have different governance.
</experiment_design>


<preprocessing>
Create a dedicated preprocessing phase covering the specification's MRI pipeline, including:

- volume discovery
- sequence identification
- rigid inter-sequence registration
- skull stripping
- N4 bias-field correction
- common-resolution resampling
- normalization
- mask handling
- QC
- caching
- provenance

Normalization statistics derived from training data must never leak test/external distribution information.

Plan visual QC.

Do not trust that successful command execution means MRI preprocessing is correct.

Define:
- representative QC sample
- overlays/figures
- expected orientation
- shape/range checks
- modality alignment checks
- mask alignment checks
- failure categories
- exclusion vs correction rules

Preprocessing must be resumable and content-addressable/version-aware where practical.
</preprocessing>


<model_and_training>
Plan the specified 3D SegResNet-style implementation.

Do not invent an architectural research program.

The phase should include:

- model interface
- four-modality channel input
- classification output
- optional auxiliary segmentation pathway
- tumor-aware pooling if retained
- modality dropout
- class imbalance handling
- losses
- training configuration
- checkpointing
- early stopping/model-selection rule based solely on allowed internal data
- AMP where appropriate
- gradient accumulation if GPU memory requires it
- reproducible data loading
- experiment logging

Before full experiments require:
- model shape tests
- CPU forward test where feasible
- GPU forward test
- tiny overfit test
- resume-from-checkpoint test
- memory benchmark

Architecture changes caused purely by hardware constraints must be documented and checked against the specification rather than silently applied.
</model_and_training>


<calibration_uncertainty_selective_prediction>
Treat these components as independent modules.

Plan separate implementations/tests for:

1. raw softmax confidence
2. temperature scaling
3. MC-dropout
4. deep ensemble
5. conformal prediction / conformal risk control
6. abstention decision logic
7. risk–coverage calculation
8. AURC
9. empirical vs nominal coverage
10. coverage deviation
11. abstention/error enrichment
12. rejected-but-correct rate

Thresholds must be learned only from allowed calibration data.

Metric code must not depend on plotting code.

Predictions should be saved once and analysis recomputed from frozen prediction artifacts whenever possible rather than rerunning expensive models unnecessarily.
</calibration_uncertainty_selective_prediction>


<statistics>
Create a dedicated statistical-analysis phase and module.

It must implement the statistical protocol in the specification and distinguish:

DESCRIPTIVE ANALYSIS
PRIMARY HYPOTHESIS/CLAIM ANALYSIS
SECONDARY ANALYSIS
EXPLORATORY ANALYSIS

Include:

- patient-level bootstrap
- >=1000 bootstrap iterations where specified
- 95% confidence intervals
- AUROC CI
- AUPRC CI
- AURC CI
- selective-risk CI
- ECE/Brier CI
- DeLong comparison
- paired bootstrap/permutation comparisons
- Benjamini-Hochberg correction
- risk–coverage monotonicity analysis
- conformal nominal-vs-empirical coverage
- abstention/error association

Avoid inappropriate independence assumptions.

Save machine-readable statistical outputs before making paper tables.

Paper tables and figures should be generated from frozen result files, not transcribed manually.
</statistics>


<publication_pipeline>
The project ends at PUBLICATION, not at "training complete."

Create phases covering:

1. research execution
2. results freeze
3. manuscript drafting
4. internal technical review
5. reporting-checklist audit
6. venue selection
7. submission package
8. submission
9. reviewer-response cycle
10. additional experiments if legitimately requested
11. revision
12. camera-ready/final manuscript
13. reproducibility/code release
14. archival release if appropriate

Create a paper/ structure that supports either LaTeX or the target venue's required format.

Maintain continuously:
- bibliography
- dataset table
- cohort-flow diagram
- method description
- experiment registry
- limitation log
- decisions
- negative results
- exclusions
- figure registry
- table registry

Do not wait until the final month to reconstruct Methods from memory.

The final manuscript must maintain the specification's framing:
empirical trustworthiness/reliability,
not a "new architecture."

Plan explicit differentiation from the closest competing works identified by the specification, particularly:
- GMMAS
- Elyassirad et al.
- Yogananda et al.
- RISEN
- FoundBioNet

Before submission:
re-check whether TRIPOD+AI / CLAIM or relevant venue requirements have been updated.

Do not claim "first" without performing a fresh literature/novelty check close to submission.
</publication_pipeline>


<phase_design>
Build the project as PHASES with explicit gates.

You may refine the exact count after repository/spec analysis, but expect roughly:

PHASE 0
Repository audit, specification extraction, governance, tooling

PHASE 1
Infrastructure + storage + environment + GPU validation

PHASE 2
Dataset access and acquisition

PHASE 3
Metadata verification + patient-level leakage/overlap audit

PHASE 4
Preprocessing pipeline + MRI QC

PHASE 5
Cohort finalization + frozen UTSW splits + experiment preregistration

PHASE 6
Baseline 3D model

PHASE 7
Calibration + uncertainty mechanisms

PHASE 8
Missing-modality robustness

PHASE 9
Selective-prediction internal experiments

PHASE 10
Ablations + internal statistical validation

PHASE 11
External-evaluation freeze and authorization

PHASE 12
Frozen cross-institutional external evaluation

PHASE 13
Final statistics + figures + tables + results freeze

PHASE 14
Manuscript + reproducibility package

PHASE 15
Submission + reviewer revisions + publication

Do not mechanically accept this phase list.

Modify/merge/split phases if dependencies justify it.

Each phase MUST contain:

# Phase N — Name

## Scientific purpose
## Engineering purpose
## Specification requirements satisfied
## RQs / claims addressed
## Entry criteria
## Inputs
## Tasks
## Human allocation
## Claude tasks
## Codex tasks
## Parallelization map
## Worktrees/branches
## Files/modules expected
## Data required
## Compute required
## Outputs/artifacts
## Tests
## Quality gates
## Scientific validation
## Acceptance criteria
## Failure conditions
## Rollback/recovery
## Risks
## Decisions that require Research Lead approval
## Exit criteria
## Dependencies for next phase

Never use vague gates such as:
"model works"
"results look good"
"preprocessing completed."

Use measurable acceptance criteria.
</phase_design>


<quality_gates>
Define several distinct gates.

GATE A — commit gate
Fast checks:
- formatting
- lint
- typing for touched code
- unit tests

GATE B — PR/merge gate
- complete CPU test suite
- relevant integration tests
- complexity review
- security/dependency checks
- documentation updated

GATE C — experiment gate
- clean git state
- valid config
- frozen dataset/split hashes
- environment recorded
- smoke test passed
- storage available
- checkpoint path validated

GATE D — phase completion
- every acceptance criterion complete
- artifacts generated
- docs updated
- independent human/agent review

GATE E — external evaluation authorization
Extremely strict.
No external-performance access until this gate passes.

GATE F — publication/result freeze
- result artifacts immutable
- statistical scripts finalized
- figures/tables reproducible
- claims trace back to evidence
</quality_gates>


<risk_management>
Create a live risk register.

At minimum include:

CRITICAL
- patient leakage
- cross-dataset overlap
- external-test peeking
- preprocessing leakage
- wrong modality mapping
- wrong patient split
- label-definition mismatch
- accidental architecture scope creep
- post-hoc threshold manipulation

HIGH
- EGD access delay
- corrupted/incomplete TCIA downloads
- insufficient class counts after exclusions
- GPU OOM
- remote GPU downtime
- preprocessing failure
- extremely wide CI at low coverage
- non-monotonic selective curves
- calibration collapse
- high abstention
- poor external discrimination

And recognize that several "bad looking" scientific outcomes are not engineering failures.

For each risk provide:
- likelihood
- impact
- detection method
- prevention
- mitigation
- owner
- phase
- trigger/escalation rule
</risk_management>


<planning_documents>
Create the planning material under:

docs/research/

At minimum create:

docs/research/README.md
docs/research/MASTER_RESEARCH_EXECUTION_PLAN.md
docs/research/SPEC_TRACEABILITY_MATRIX.md
docs/research/AGENT_WORKTREE_PROTOCOL.md
docs/research/DATA_GOVERNANCE_PROTOCOL.md
docs/research/EXTERNAL_VALIDATION_PROTOCOL.md
docs/research/REPRODUCIBILITY_PROTOCOL.md
docs/research/RISK_REGISTER.md
docs/research/PUBLICATION_PLAN.md
docs/research/DECISION_LOG.md

and:

docs/research/phases/
    PHASE_00_*.md
    PHASE_01_*.md
    ...

Do not duplicate hundreds of lines unnecessarily.

MASTER_RESEARCH_EXECUTION_PLAN.md should provide the authoritative project-level view.

Phase files contain actionable task-level details.

SPEC_TRACEABILITY_MATRIX.md prevents requirements from disappearing during implementation.

DECISION_LOG.md records changes from the original specification.

README.md explains how these documents relate.
</planning_documents>


<master_plan_requirements>
MASTER_RESEARCH_EXECUTION_PLAN.md must contain:

1. Executive summary
2. Frozen scientific objective
3. Research questions
4. Falsifiable claims
5. Novelty boundary
6. Scope / non-scope
7. Datasets and their exact roles
8. Scientific invariants
9. System architecture
10. Repository architecture
11. Storage architecture
12. Local/GPU execution architecture
13. Team model
14. Claude/Codex orchestration model
15. Git/worktree model
16. Dependency graph
17. Phase overview
18. Experiment taxonomy
19. Data provenance model
20. Reproducibility model
21. Quality strategy
22. Testing strategy
23. Statistical-analysis strategy
24. External-validation firewall
25. Research artifact/versioning strategy
26. Publication pipeline
27. Risk register summary
28. Definition of Done for the entire project
29. Open decisions/questions
30. Critical path
</master_plan_requirements>


<planning_behavior>
Before writing the plan:

STEP 1
Inspect repository tree.

STEP 2
Read existing README/docs/configuration/code.

STEP 3
Read the entire research-specification PDF.

STEP 4
Create an internal extraction of:
- scientific invariants
- implementation requirements
- risks
- unanswered implementation decisions

STEP 5
Compare specification requirements against current repository state.

Classify each capability:

EXISTS AND VALID
EXISTS BUT NEEDS MODIFICATION
MISSING
NOT APPLICABLE
BLOCKED
REQUIRES HUMAN DECISION

STEP 6
Determine dependencies and critical path.

STEP 7
Determine what Claude/Codex can safely implement in parallel.

STEP 8
Design repository/storage/worktree/reproducibility strategy.

STEP 9
Construct phases.

STEP 10
Write planning documents.

STEP 11
Perform a hostile review of your own plan.

Ask:

- Could leakage still occur?
- Could an agent accidentally inspect external performance?
- Can every paper result be reproduced?
- Are Claude/Codex tasks actually independent?
- Can three active team members execute this?
- Is the GPU dependency realistic?
- Is raw data kept outside Git?
- Are SSD paths portable?
- Can experiments resume?
- Are RQ1–RQ4 all traceable?
- Are C1–C6 all testable?
- Have we accidentally created architecture-search scope?
- Are negative results preserved?
- Is the paper pipeline included?
- Are there vague acceptance criteria?
- Are quality gates proportional rather than bureaucratic?
- Have we built anything unnecessary?

Revise the plan until these checks pass.
</planning_behavior>


<important_constraints>
DO NOT:

- begin implementation
- download datasets
- start preprocessing
- run training
- inspect external performance
- create model architecture variants
- add MGMT
- change scientific endpoints
- manufacture novelty
- invent dataset facts
- invent missing repository state
- commit data
- hard-code SSD paths
- assume GPU hardware
- create unnecessary microservices
- introduce distributed infrastructure without justification
- use notebooks as production pipelines
- create a complex MLOps platform for its own sake
- optimize for software complexity instead of research validity

At this stage your deliverable is the execution system and planning documents.

You may create directories/docs/configuration placeholders required for the PLAN itself, but do not implement research functionality yet.
</important_constraints>


<final_output>
After creating the planning files, return a concise report containing:

1. files created
2. proposed number of phases
3. critical path
4. first phase to execute
5. top five project risks
6. Claude/Codex parallelization summary
7. decisions requiring Research Lead approval
8. any contradiction/ambiguity discovered in the source specification
9. whether the repository is ready to begin Phase 0/1
10. exact next command/prompt I should give Claude to start the first implementation phase

Do NOT dump the complete contents of every created document into chat.

The files under docs/research/ are the source of truth.
</final_output>