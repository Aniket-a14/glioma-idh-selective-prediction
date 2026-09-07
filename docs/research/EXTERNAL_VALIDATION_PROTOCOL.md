# EXTERNAL VALIDATION PROTOCOL — the firewall

A single early peek at UCSF-PDGM or EGD performance voids claim C4 and, with it, the paper's central contribution. This protocol exists to make that peek procedurally and technically hard.

> *"Even a single early 'peek' at external performance to adjust the conformal threshold invalidates the coverage-guarantee claim (C4) entirely."* — SPEC §4.11

---

## 1. The distinction the project rests on

External cohorts require real operational work — downloading, verifying, de-duplicating, preprocessing. **That work is not the same as looking at performance**, and conflating the two would either paralyze the project or destroy it. The line:

| PERMITTED from Phase 02 (operational) | **BLOCKED until Gate E** (performance) |
|---|---|
| Download UCSF-PDGM and EGD | Compute **any** metric against external labels |
| Verify checksums, file counts, integrity | View external AUROC, AURC, coverage, risk, ECE |
| Perform BraTS-2021 ID de-duplication | Tune any hyperparameter on external data |
| Count labels for the cohort table | Fit normalization statistics on external data |
| Inspect image headers, orientation, spacing | Fit calibration or conformal quantiles externally |
| Run deterministic preprocessing | Select a checkpoint using external results |
| Visual QC of preprocessing output | Any "quick sanity check" of external accuracy |
| Record cohort demographics | Compare an external result to an internal one |

**Rule of thumb:** if the operation requires the external *label* column, it is blocked. Counting labels for Table 1 is permitted; joining labels to predictions is not.

---

## 2. Technical enforcement

`.env` ships with:

```
GLIOMA_EXTERNAL_EVAL_AUTHORIZED=0
```

Every code path that joins external predictions to external labels calls:

```python
firewall.assert_external_eval_authorized(cohort="ucsf_pdgm")
```

which raises unless **both** hold: the flag is set, and a signed freeze manifest exists at `artifacts/experiments/gate_e/freeze_manifest.json` with a valid hash. The check lives in `src/glioma_selective/evaluation/firewall.py` and is covered by a unit test asserting that it raises by default.

Additional guards:
- External cohort adapters expose `load_images()` freely but `load_labels()` routes through the firewall.
- CI runs with the flag at `0`, so any test that accidentally evaluates externally fails in CI.
- Flipping the flag is a **logged, dated, Research-Lead-only** action recorded in `docs/research/protocols/GATE_E_LOG.md`.

This is defence in depth, not a guarantee. The procedural controls below matter more, because a determined operator can always bypass a flag they own.

---

## 3. Gate E — external evaluation authorization

The strictest gate in the project. Passed **exactly once**.

**Entry criteria — all must hold:**
1. Phases 00–10 complete; every prior gate passed.
2. All internal results final; no outstanding internal analysis.
3. Working tree clean; all work merged to `main`.
4. Leakage regression test passing on the final manifests.
5. `UCSF-PDGM ∩ BraTS-2021 = ∅` verified and hashed.
6. **D-002, D-003, D-004 resolved and pre-registered** — conformal method, abstention definition, and tolerance band frozen before external data can speak.
7. Statistical analysis plan complete and committed, including which comparisons are BH-corrected.
8. Research Lead has read and signed the freeze manifest.

**The freeze manifest** — generated, hashed, and committed *before* the flag flips:

| Field | Frozen value |
|---|---|
| Code commit SHA | exact, clean tree |
| Model checkpoints | paths + SHA-256 per file |
| Preprocessing configuration | resolved config + version |
| Normalization statistics | file + hash (UTSW-train derived) |
| Data exclusions | manifest + hash |
| UTSW splits | manifest + hash |
| Calibration parameters | temperature T, procedure |
| Conformal method | split CP vs. CRC (**D-002**), α grid, nonconformity score |
| Abstention definition | threshold vs. set-valued (**D-003**) |
| Operating points | the coverage/α values to be reported |
| Missing-modality conditions | the exact 6 conditions |
| Primary metrics | selective risk @ matched coverage, AURC, monotonicity, coverage deviation |
| C4 tolerance band | the frozen number (**D-004**) |
| Statistical analysis plan | tests, correction family, bootstrap iterations |
| Authorizing signature | Research Lead name + date |

---

## 4. After the flag flips

1. The event is logged with a timestamp in `GATE_E_LOG.md`.
2. Predictions, configs, environment record, and git SHA are preserved immutably under `artifacts/experiments/external_frozen/`.
3. **The method does not change because results look undesirable.** Not the threshold, not the checkpoint, not the preprocessing, not the α, not the tolerance band.
4. The external run happens **once**. Re-running requires a decision-log entry explaining why (e.g. a genuine, demonstrated bug), and the original result is retained alongside.

Any post-external change is categorized explicitly as one of:

| Category | Allowed? | Treatment in the manuscript |
|---|---|---|
| **Bug correction** | Yes, with evidence the bug is real and predates the run | Original and corrected results both reported; the bug described |
| **Reviewer-requested analysis** | Yes, after submission | Clearly labelled as post-hoc, reported separately |
| **Explicitly exploratory** | Yes | Labelled exploratory; no inferential claim |
| **Anything else** | **No** | — |

**Nothing in these categories may silently replace the pre-registered primary result.**

---

## 5. Contingency: EGD does not arrive

The EGD data-use agreement is the longest-latency item in the project. If it has not been granted by Phase 11:

- Proceed to Gate E with **UCSF-PDGM as the sole external cohort**. The 2×2 design survives with one external cohort; statistical power for RQ2/RQ3 is reduced and this is stated.
- Record the degradation in the decision log and the manuscript Limitations — do not quietly present a one-cohort external validation as if two were planned.
- If EGD arrives later, treat it as a **second, separately-frozen** external evaluation with its own freeze manifest, reported as an addendum or in the reviewer cycle. It does not retroactively join the primary result.

---

## 6. What agents must not do

Both Claude and Codex operate under these constraints, stated here because an agent with filesystem access could violate them without meaning to:

- Do not compute, print, log, or plot any metric on UCSF-PDGM or EGD before Gate E.
- Do not write a test whose fixture is an external label.
- Do not "verify the pipeline works" by running it end-to-end on external data.
- Do not read external label files to check parsing — validate parsers on UTSW, then apply.
- If a task appears to require external performance before Gate E, **stop and raise it** rather than finding a workaround.
