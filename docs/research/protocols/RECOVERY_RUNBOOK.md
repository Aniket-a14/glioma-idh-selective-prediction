# RECOVERY RUNBOOK

Phase 01 task T01.9. Six failure modes (see `DECISION_LOG.md` D-015 for why six, not the five
named in the phase file's task row: SSH drop, OOM, process crash, partial/corrupt checkpoint,
power loss, and external storage failure — the sixth follows from R-M07 in `RISK_REGISTER.md`).

None of these procedures are hypothetical: `REPRODUCIBILITY_PROTOCOL.md` §1's run-record schema
(`checkpoint_hash`, `training_history`, `git_dirty`, `preprocessing_version`) and §5's
frozen-prediction-artifact design exist specifically so that every mode below is recoverable
without re-deriving or re-tuning anything — recovery must never become a backdoor for a result to
quietly change.

---

## 1. SSH drop (connection to the GPU server lost mid-run)

**Cause.** Network interruption, laptop sleep, Wi-Fi drop — the training process itself is on the
remote GPU server, not the local machine, and does not die just because the SSH session does,
provided it was started correctly.

**Prevention (must be true before any run starts, R-H05).** Every long-running job is launched
under `tmux` or `nohup` on the GPU server, never as a foreground process tied to the SSH session.
`tmux new -s glioma-<run_id>` before starting training; `tmux attach -t glioma-<run_id>` to
reconnect.

**Recovery.**
1. Reconnect: `ssh <gpu-server>`.
2. `tmux ls` — if the session is present, the job survived the drop regardless of duration.
   `tmux attach -t glioma-<run_id>` and confirm the process is still advancing (check the log
   timestamp, not just that the process exists).
3. If the session is gone (server itself rebooted, not just the SSH link — distinguish this from
   mode 5/6 below), go to **§4 Partial/corrupt checkpoint** to resume from the last checkpoint.
4. Never assume progress from wall-clock time alone; confirm from the log / MLflow run record.

**Not recovery.** Restarting the run from scratch because reconnecting seems easier. A dropped SSH
session with the job still alive in `tmux` costs nothing — treat re-launching as a last resort,
not a default.

---

## 2. GPU out-of-memory (R-H04)

**Cause.** Actual VRAM is unmeasured until this phase's benchmark (T01.7) runs; a later training
job may exceed it if the benchmark's numbers weren't respected, or if a genuinely different config
(larger crop, larger batch) is used without re-benchmarking.

**Prevention.** T01.7's benchmark table (patch size × batch size → peak VRAM) is the source of
truth for what fits. No training config is authorized above the benchmarked envelope without
re-running the benchmark first.

**Recovery — the ladder, in this order, per R-H04's documented mitigation. Stop at the first step
that fits; do not skip ahead "to be safe."**
1. Confirm this is actually OOM (check the error — `CUDA out of memory` — not a different crash;
   see §3 if it isn't).
2. Reduce patch size: 128³ → 96³.
3. If still OOM at 96³: gradient accumulation (same effective batch size, smaller per-step memory).
4. If still OOM: reduce batch size to 1.
5. **Any step taken beyond step 1 is recorded as a deviation in `DECISION_LOG.md` and checked
   against SPEC §4.2's 96³/128³ patch specification before the run resumes.** This is not
   optional — R-H04's mitigation and this phase's own "genuine gate, not a formality" framing for
   T01.5 both exist to stop a hardware constraint from silently becoming an unreviewed
   architecture change.
6. Resume from the last checkpoint (§4), not from scratch, once the config is fixed.

---

## 3. Process crash (non-OOM: unhandled exception, driver error, segfault)

**Cause.** Anything that kills the training process without it being memory pressure or the host
itself going down — a data-loading exception, a CUDA driver fault, an unhandled edge case in a
batch.

**Recovery.**
1. Read the actual traceback / log tail before doing anything else — do not guess the cause from
   the fact that it crashed.
2. Check `git status` / the run record's `git_dirty` field: was the code that produced the last
   checkpoint clean? If the tree was dirty, that run's results are already suspect independent of
   the crash (R-M08) — do not resume into a dirty tree; fix the tree first.
3. If the cause is a genuine bug: fix it, and treat the fix like any other code change — tests,
   commit, Gate A — before resuming. Do not patch around it with a `try/except` that swallows the
   condition.
4. If the cause is transient (a flaky driver fault with no reproduction): resume from the last
   checkpoint (§4) and note the transient failure in the run's log; if it recurs, it isn't
   transient and needs actual investigation, not a second retry.
5. Never resume by silently changing the config to avoid the crash — that's an unreviewed
   deviation, same principle as step 5 in §2.

---

## 4. Partial or corrupt checkpoint

**Cause.** Interruption (any of modes 1, 2, 3, 5, 6) mid-write to the checkpoint file, or a
resume-equivalence bug (the exact thing Phase 06 authorization step 6 — "checkpoint save/resume
equivalence test" — exists to catch before this ever happens in a real run).

**Recovery.**
1. Never trust the most recent checkpoint file by file-existence alone. Verify
   `checkpoint_hash` (SHA-256, `REPRODUCIBILITY_PROTOCOL.md` §1 field 15) against what the run
   record expects, and confirm the file loads (state-dict keys match the model) before resuming
   from it.
2. If the most recent checkpoint fails verification: fall back to the previous one. Both `last`
   and periodic epoch checkpoints are retained (R-H05's mitigation) precisely so a single bad
   write doesn't lose the whole run.
3. If no checkpoint verifies: this is a real loss, not a recovery scenario. Report it — recompute
   from the last **verified** checkpoint, accepting the lost epochs; never fabricate or interpolate
   a checkpoint state.
4. Resume must reproduce the pre-interruption trajectory closely enough to trust the merged
   training history — this is exactly what the Phase 06 resume-equivalence test verifies in
   advance. If that test doesn't exist yet or wasn't run for this config, resuming here is
   unverified and should be flagged as such in the run record, not silently treated as equivalent
   to an uninterrupted run.

---

## 5. Power loss (local machine or GPU server)

**Cause.** Outage, hardware fault, accidental shutdown.

**Recovery.**
1. On restart, do not immediately relaunch anything. First confirm state: `git status` on both
   machines (uncommitted work survives a power loss only if it was on disk, not just staged in an
   editor buffer — check for exactly this), `tmux ls` on the GPU server (a `tmux` session does not
   survive a reboot — its absence here does not indicate a bug, it indicates the reboot happened
   as expected).
2. External storage (the symlinked `data/`/`artifacts/` volumes): confirm the mount is intact
   before trusting any path under it — `bootstrap_storage.py`'s idempotence (T01.1) means
   re-running it after a remount is always safe and is the correct first step, not a workaround.
3. Follow §4 for any in-flight checkpoint at the time of the outage.
4. If the GPU server's driver/CUDA state looks different after restart (a power event can
   sometimes coincide with a driver update or a changed GPU state), re-run
   `capture_environment.py` (T01.3) and diff against the recorded fingerprint before resuming
   training — silently training on a changed environment without noticing is worse than the
   outage itself.

---

## 6. External storage failure (R-M07)

**Cause.** The external SSD (or the GPU server's local large volume) fails, is disconnected
improperly, or becomes unreadable.

**Why this phase can absorb it cheaply.** Per R-M07: at this point in the project nothing
irreplaceable lives on external storage yet — raw data is re-downloadable, manifests are in Git,
and (once real runs exist) checkpoints and predictions are backed up after each frozen run. This
runbook entry exists so that guarantee is actually exercised, not just asserted.

**Recovery.**
1. Diagnose before acting: `df -h` / `diskutil info` (macOS) or the Linux equivalent to determine
   whether this is disconnection (remount fixes it) versus genuine media failure (does not).
2. If remountable: re-run `bootstrap_storage.py` (idempotent by T01.1's own requirement) rather
   than manually recreating symlinks.
3. If not remountable:
   - `data/raw/`, `data/external/` — re-acquire per `DATA_GOVERNANCE_PROTOCOL.md`'s acquisition
     record; these are documented as re-downloadable by design.
   - `data/manifests/` — recoverable from Git; never solely lives on external storage.
   - `artifacts/checkpoints/`, `artifacts/predictions/` — recoverable only if a backup was taken
     after the last frozen run, per R-M07's stated mitigation. If no backup exists for
     in-progress (non-frozen) work, that work is lost; this is the cost of "dev runs pruned /
     not yet backed up" and is exactly why **frozen** results are backed up but transient dev
     runs are treated as reproducible-from-config instead of precious.
4. This project currently has two physical drives in play (see `DECISION_LOG.md` D-014) — a
   failure of one does not necessarily affect the other; check the D-014 layout to know which
   dataset (dev cohort vs. external test cohort) is actually at risk before assuming both are
   lost.

---

## Cross-cutting rule for every mode above

**Recovery restores the run to where it was; it never becomes an opportunity to adjust the run.**
Any change made in the course of recovering — a patch size, a batch size, a config value, a
retried step with different parameters — is a deviation, and every deviation in this project is
recorded in `DECISION_LOG.md` and checked against the specification before the run continues, not
applied silently because the alternative (stopping to log it) felt like it would slow recovery
down. This is the same principle `PHASE_01_INFRASTRUCTURE.md` states for the OOM ladder
specifically (§2 above), generalized to all six modes.
