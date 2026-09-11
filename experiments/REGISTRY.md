# Experiment Registry

This registry is the index of every scientific run. It is append-only after a
run record is created. The registry records where a run is described; it does
not replace the run record or the frozen manifest.

## Status

No experiments have been run. Phase 00 creates the registry only.

## Required entry fields

Each row must include:

| Field | Requirement |
|---|---|
| Run ID | Stable identifier, e.g. `R01` |
| Phase | Phase that authorized the run |
| Question / claim | RQ and/or claim being tested |
| Config | Relative path to the immutable config |
| Manifest | Relative path and SHA-256 of the input manifest |
| Git SHA | Commit used for the run |
| Seed(s) | All random seeds |
| Cohort / split | Cohort identity and split version |
| Status | `planned`, `running`, `complete`, or `aborted` |
| Artifacts | Relative paths to outputs and run record |
| Notes | Deviations, failures, or approvals |

## Registry

| Run ID | Phase | Question / claim | Config | Manifest | Git SHA | Seed(s) | Cohort / split | Status | Artifacts | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
