# Gate D independent review — Phase 07

Date: 2026-11-18. Reviewed code: `df8ef236a5b7114a3d13a391052d647dd7d54518`, branch `agent/codex/gate-d-review`.

Reviewer: Codex, independent of the phase author. **D-001 degraded solo fallback: a second agent, not a second human.** No claim is made that a human Person C reviewed or signed anything.

**Gate D verdict: FAIL — calibration-isolation test missing; D-058 exceptions acknowledged.** Review task status: **DONE_WITH_CONCERNS**. Acceptance counts: 7 met, 3 not met, 0 cannot tell.

Criteria source: [PHASE_07_CALIBRATION_UNCERTAINTY.md](../phases/PHASE_07_CALIBRATION_UNCERTAINTY.md). Author briefs/readiness tables were treated as assertions to check. The embedded read-only checker below was actually executed, exit 0, using the requested virtualenv and `PYTHONPATH=src`. Each criterion repeats its exact command; shared commands were run once, not once per repeated listing. Outputs are trimmed.

Storage was resolved through `glioma_selective.utils.paths` with `GLIOMA_STORAGE_ROOT=/Volumes/Research_2`. Only the named UTSW run artifacts and UTSW manifest summary were used (plus R8’s explicitly referenced stage-1 record). No external image/label file was opened; the authorization flag was unset and was never assigned. No installation, training, inference, refit of the IDH model, or write to the SSD occurred. A historical “met” GPU outcome means its frozen report was checked; a new live GPU measurement is not claimed.

## Criterion 1: met

**D-002 resolved**; the primary conformal instrument fixed and recorded.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
D-002 "D-002 \u2014 \"Split conformal prediction\" and \"conformal risk control\" are used interchangeably\n**Status:** RESOLVED 2026-10-05 (Research Lead: recommendation adopted) \u00b7 **Resolve by:** Phase 07 (before any calibration is fitted) \u00b7 **Blocking:** YES until Phase 07 starts\n\n**Resolution 2026-10-05.** Alternative (a) with (c) as the reported form: split conformal prediction is the primary instrument (M5), conformal risk control is a named secondary on an accepted-error loss (see D-045 for the exact loss). C4 keeps its coverage wording unchanged. T07.1 is closed by this entry.\n\n**Conflict.** SPEC \u00a74.6 titles the pri ... [remaining decision entry trimmed]
```

Comparison and judgment: The dated resolution fixes split conformal as primary and CRC as named secondary before any real calibration fit. Compared with criterion 1 and D-045.

## Criterion 2: met

All four mechanisms implemented as independent modules with no shared hidden state.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
module_calibration/temperature.py ["_MIN_TEMPERATURE = 0.05", "_MAX_TEMPERATURE = 20.0", "_W_TOLERANCE = 1e-8", "def _validated_inputs(", "def _sigmoid(values: NDArray[np.float64]) -> NDArray[np.float64]:", "def _mean_binary_cross_entropy(", "def fit_temperature(", "def apply_temperature("]
module_calibration/conformal.py ["__all__ = [", "def _exact(value: float) -> Fraction:", "def _probability(value: float) -> Fraction:", "def _label(value: int) -> int:", "def _alpha(alpha: float) -> Fraction:", "def nonconformity_score(p_hat: float, label: int) -> float:", "def nonconformity_scores(p_hat: Sequence[float], labels: Sequence[int]) -> list[float]:", "def conformal_quantile(scores: Sequence[float], alpha: float) -> float:", "def prediction_set(p_hat: float, quantile: float) -> tuple[int, ...]:", "def prediction_sets(p_hat: Sequence[float], quantile: float) -> list[tuple[int, ...]]:", "def empirical_coverage(sets: Sequence[tuple[int, ...]], labels: Sequence[int]) -> float:", "def conformal_summary("]
module_calibration/crc.py ["__all__ = [\"accept\", \"confidence\", \"crc_threshold\"]", "def _exact(value: float) -> Fraction:", "def _probability(value: float) -> Fraction:", "def confidence(p_hat: float) -> float:", "def accept(p_hat: float, tau: float) -> bool:", "def crc_threshold(p_hat: Sequence[float], labels: Sequence[int], alpha: float) -> float:"]
module_uncertainty/mc_dropout.py ["__all__ = [\"DEFAULT_PASSES\", \"mc_dropout_probabilities\"]", "def _dropout_layers(head: nn.Module) -> list[nn.Dropout]:", "def mc_dropout_probabilities(", "def _head_pass("]
module_selective/abstention.py ["__all__ = [", "def _probability(value: float) -> Fraction:", "def confidence_scores(p_hat: Sequence[float]) -> list[float]:", "def binary_entropy(probability: float) -> float:", "def _matrix(", "def mc_dropout_scores(", "def ensemble_variance_scores("]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Comparison and judgment: Read temperature.py, conformal.py, crc.py, mc_dropout.py and selective/abstention.py. Fits return values, scores take explicit arrays, and there is no shared fitted mutable state. MC-dropout exposes its RNG/generator choice and restores dropout modes in finally; test_dropout_modes_are_restored_and_the_backbone_stays_in_eval passed. M2/M5 intentionally share the same calibrated probability under D-045/D-047.

## Criterion 3: not met

Every parameter fitted on the calibration split only; asserted by test.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
fit_source ["src/glioma_selective/evaluation/internal_analysis.py:230:     calibration_logits, calibration_raw, calibration_labels = _split_arrays(", "src/glioma_selective/evaluation/internal_analysis.py:231:         frame, \"utsw_calibration\"", "src/glioma_selective/evaluation/internal_analysis.py:232:     )", "src/glioma_selective/evaluation/internal_analysis.py:233:     test_logits, test_raw, test_labels = _split_arrays(frame, \"utsw_internal_test\")", "src/glioma_selective/evaluation/internal_analysis.py:234: ", "src/glioma_selective/evaluation/internal_analysis.py:235:     temperature = fit_temperature(calibration_logits, calibration_labels)", "src/glioma_selective/evaluation/internal_analysis.py:236:     calibration_scaled = apply_temperature(calibration_logits, temperature)", "src/glioma_selective/evaluation/internal_analysis.py:237:     test_scaled = apply_temperature(test_logits, temperature)", "src/glioma_selective/evaluation/internal_analysis.py:238:     raw_test = _classification_metrics(test_raw, test_labels)", "src/glioma_selective/evaluation/internal_analysis.py:239:     scaled_test = _classification_metrics(test_scaled, test_labels)", "src/glioma_selective/evaluation/internal_analysis.py:240:     raw_selective = _selective_metrics(test_raw, test_labels)", "src/glioma_selective/evaluation/internal_analysis.py:241:     scaled_selective = _selective_metrics(test_scaled, test_labels)", "src/glioma_selective/evaluation/internal_analysis.py:242:     conformal = _co ... [trimmed]
separate_condition_fits ["src/glioma_selective/evaluation/condition_analysis.py:250:     full_calibration = _rows(condition_frames[\"full\"], \"utsw_calibration\", \"full\")", "src/glioma_selective/evaluation/condition_analysis.py:251:     full_cal_logits, _full_cal_raw, full_cal_labels, _ = _arrays(full_calibration)", "src/glioma_selective/evaluation/condition_analysis.py:252:     full_temperature = fit_temperature(full_cal_logits, full_cal_labels)", "src/glioma_selective/evaluation/condition_analysis.py:253:     full_cal_scaled = apply_temperature(full_cal_logits, full_temperature)", "src/glioma_selective/evaluation/condition_analysis.py:254:     condition_results: dict[str,
... [remaining output trimmed]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Comparison and judgment: F01: code inspection and independent fits support calibration-only fitting, but the required test asserting that *every* fitted parameter excludes test data is absent. test_internal_analysis uses the same perfectly ordered ±0.8 logits in both splits, so a fit on the wrong split can still pass. test_condition_analysis changes calibration inputs and checks carried != refit, without asserting test-label/logit changes leave T, all q values and CRC thresholds unchanged. There is no end-to-end isolation assertion for all three fit paths in these tests. This is missing required regression coverage, not evidence that external or test labels were used.

## Criterion 4: met

Conformal quantile includes the n+1 correction; hand-calculated test passing.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
quantile_source ["src/glioma_selective/calibration/conformal.py:65: ", "src/glioma_selective/calibration/conformal.py:66: ", "src/glioma_selective/calibration/conformal.py:67: def conformal_quantile(scores: Sequence[float], alpha: float) -> float:", "src/glioma_selective/calibration/conformal.py:68:     \"\"\"The ``ceil((n + 1) * (1 - alpha))``-th smallest score, or ``+inf`` (K2).", "src/glioma_selective/calibration/conformal.py:69: ", "src/glioma_selective/calibration/conformal.py:70:     With ``n`` calibration scores the finite-sample correction asks for the", "src/glioma_selective/calibration/conformal.py:71:     ``k``-th order statistic, ``k = ceil((n + 1)(1 - alpha))``. When ``k > n`` no", "src/glioma_selective/calibration/conformal.py:72:     finite threshold carries the guarantee, so the answer is ``+inf`` and every", "src/glioma_selective/calibration/conformal.py:73:     label stays in every set. The result is a member of ``scores`` or ``+inf``.", "src/glioma_selective/calibration/conformal.py:74:     \"\"\"", "src/glioma_selective/calibration/conformal.py:75:     values = [float(score) for score in scores]", "src/glioma_selective/calibration/conformal.py:76:     if not values:", "src/glioma_selective/calibration/conformal.py:77:         raise ValueError(\"scores must not be empty\")", "src/glioma_selective/calibration/conformal.py:78:     if any(not math.isfinite(score) for score in values):", "src/glioma_selective/calibration/conformal.py:79:         raise ValueErro ... [trimmed]
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
```

Output (trimmed):

```text
83 passed in 0.73s
```

Comparison and judgment: The implementation uses the exact ceil((n+1)(1-alpha)) order statistic and handles k>n as infinity. Hand fixtures and the separately written conformal reference passed, including decimal-boundary and n+1 cases. Compared with the Phase 07 K2 contract, not an approximate floating ceil.

## Criterion 5: not met

**Conformal empirical coverage within ±2pp of nominal on exchangeable internal data**, for every α in the grid.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
calibration_R1 {"conformal": [{"alpha": 0.05, "coverage": 0.967741935483871, "delta_pp": 1.774193548387104, "frozen_coverage": null, "q": 0.8455394494903339, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.9193548387096774, "delta_pp": 1.9354838709677358, "frozen_coverage": null, "q": 0.6974491435277447, "within_2pp": "True"}, {"alpha": 0.2, "coverage": 0.7580645161290323, "delta_pp": -4.193548387096779, "frozen_coverage": null, "q": 0.5125601524011015, "within_2pp": "False"}], "frozen_temperature": 1.3522186414952444, "metrics": {"M1_raw": {"brier": 0.17122640446513873, "ece10": 0.18632296135242835, "ece15": 0.20086028558006136, "ece5": 0.18106110911802012, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1690488053601114, "ece10": 0.1912250297111532, "ece15": 0.20264670276718383, "ece5": 0.1837739074667965, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.352218637025625}
calibration_R2 {"conformal": [{"alpha": 0.05, "coverage": 0.9596774193548387, "delta_pp": 0.967741935483879, "frozen_coverage": null, "q": 0.777272182418763, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.8709677419354839, "delta_pp": -2.9032258064516148, "frozen_coverage": null, "q": 0.6621427078933437, "within_2pp": "False"}, {"alpha": 0.2, "coverage": 0.7258064516129032, "delta_pp": -7.41935483870968, "frozen_coverage": null, "q": 0.39233359333855317, "within_2pp": "False"}], "frozen_temperature": 1.1247560944350967, "metrics": {"M1_raw": {"brier": 0.13992721006181305, "ece10": 0.11886621431386386, "ece15": 0.11986276143409659, "ece5": 0.0958629546491839, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1387178219344037, "ece10": 0.12216069353330185, "ece15": 0.13631738075696587, "ece5": 0.10760289362523177, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.1247561048090786}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/check_conformal_exchangeable.py --run-id 01M46999FB083AX4WW0067YM13 --reps 1000 --seed 0
```

Output (trimmed):

```text
synthetic, 124/124 (nominal: mean coverage, sd):
  0.95: 0.953, 0.025
  0.90: 0.905, 0.036
  0.80: 0.801, 0.051
01M46999FB083AX4WW0067YM13 pooled re-splits, n=248 (nominal: mean, sd):
  0.95: 0.953, 0.027
  0.90: 0.905, 0.038
  0.80: 0.801, 0.050
```

Comparison and judgment: F06: the literal ±2pp criterion fails in 3/6 cells (R1 alpha=.2; R2 alpha=.1,.2). Independent calculations match PHASE07_INTERNAL_RESULTS.md to its displayed precision. D-058 resolution 2026-11-18 accepts the replication check as replacement implementation evidence; that check reproduces means 0.953/0.905/0.801 and SD 0.025–0.051. This approved exception does not make the six original gaps vanish.

## Criterion 6: not met

Temperature scaling reduces internal-test ECE relative to raw softmax.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
calibration_R1 {"conformal": [{"alpha": 0.05, "coverage": 0.967741935483871, "delta_pp": 1.774193548387104, "frozen_coverage": null, "q": 0.8455394494903339, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.9193548387096774, "delta_pp": 1.9354838709677358, "frozen_coverage": null, "q": 0.6974491435277447, "within_2pp": "True"}, {"alpha": 0.2, "coverage": 0.7580645161290323, "delta_pp": -4.193548387096779, "frozen_coverage": null, "q": 0.5125601524011015, "within_2pp": "False"}], "frozen_temperature": 1.3522186414952444, "metrics": {"M1_raw": {"brier": 0.17122640446513873, "ece10": 0.18632296135242835, "ece15": 0.20086028558006136, "ece5": 0.18106110911802012, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1690488053601114, "ece10": 0.1912250297111532, "ece15": 0.20264670276718383, "ece5": 0.1837739074667965, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.352218637025625}
calibration_R2 {"conformal": [{"alpha": 0.05, "coverage": 0.9596774193548387, "delta_pp": 0.967741935483879, "frozen_coverage": null, "q": 0.777272182418763, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.8709677419354839, "delta_pp": -2.9032258064516148, "frozen_coverage": null, "q": 0.6621427078933437, "within_2pp": "False"}, {"alpha": 0.2, "coverage": 0.7258064516129032, "delta_pp": -7.41935483870968, "frozen_coverage": null, "q": 0.39233359333855317, "within_2pp": "False"}], "frozen_temperature": 1.1247560944350967, "metrics": {"M1_raw": {"brier": 0.13992721006181305, "ece10": 0.11886621431386386, "ece15": 0.11986276143409659, "ece5": 0.0958629546491839, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1387178219344037, "ece10": 0.12216069353330185, "ece15": 0.13631738075696587, "ece5": 0.10760289362523177, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.1247561048090786}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python scripts/person_c_recompute.py --results-root /Volumes/Research_2/artifacts/experiments --reference /Volumes/Research_2/artifacts/experiments/01M46999FB083AX4WW0067YM13/phase10_analysis.json
```

Output (trimmed):

```text
124 internal-test patients, 35 IDH-mutant; reference phase10_analysis.json
188 of 188 numbers agree
```

Comparison and judgment: F06: independent 10-bin ECE rises R1 0.1863229614 -> 0.1912250299; R2 0.1188662143 -> 0.1221606934. Brier falls R1 0.1712264045 -> 0.1690488054; R2 0.1399272101 -> 0.1387178220. These agree with PHASE07_INTERNAL_RESULTS.md. D-058 explicitly accepts “not met, reported”, no refit. Phase 10 D1 raw-minus-scaled ECE is -0.00329448, 95% [-0.0276,0.0223], p about 0.668; this does not demonstrate improved ECE.

## Criterion 7: met

ECE, Brier, and reliability computed and stored for M1 and M2.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
calibration_R1 {"conformal": [{"alpha": 0.05, "coverage": 0.967741935483871, "delta_pp": 1.774193548387104, "frozen_coverage": null, "q": 0.8455394494903339, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.9193548387096774, "delta_pp": 1.9354838709677358, "frozen_coverage": null, "q": 0.6974491435277447, "within_2pp": "True"}, {"alpha": 0.2, "coverage": 0.7580645161290323, "delta_pp": -4.193548387096779, "frozen_coverage": null, "q": 0.5125601524011015, "within_2pp": "False"}], "frozen_temperature": 1.3522186414952444, "metrics": {"M1_raw": {"brier": 0.17122640446513873, "ece10": 0.18632296135242835, "ece15": 0.20086028558006136, "ece5": 0.18106110911802012, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1690488053601114, "ece10": 0.1912250297111532, "ece15": 0.20264670276718383, "ece5": 0.1837739074667965, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.352218637025625}
calibration_R2 {"conformal": [{"alpha": 0.05, "coverage": 0.9596774193548387, "delta_pp": 0.967741935483879, "frozen_coverage": null, "q": 0.777272182418763, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.8709677419354839, "delta_pp": -2.9032258064516148, "frozen_coverage": null, "q": 0.6621427078933437, "within_2pp": "False"}, {"alpha": 0.2, "coverage": 0.7258064516129032, "delta_pp": -7.41935483870968, "frozen_coverage": null, "q": 0.39233359333855317, "within_2pp": "False"}], "frozen_temperature": 1.1247560944350967, "metrics": {"M1_raw": {"brier": 0.13992721006181305, "ece10": 0.11886621431386386, "ece15": 0.11986276143409659, "ece5": 0.0958629546491839, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1387178219344037, "ece10": 0.12216069353330185, "ece15": 0.13631738075696587, "ece5": 0.10760289362523177, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.1247561048090786}
```

Comparison and judgment: Raw and scaled positive-class ECE at 5/10/15 bins, Brier, and ten reliability bins are stored in each hash-verified internal_analysis.json. Independently derived point estimates match the results document; reliability bin count is 10 for both views.

## Criterion 8: met

Ensemble members R3–R6 trained; the 6-run total (R1–R6) is on budget.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
ensemble_R3 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 1, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R4 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 2, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R5 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 3, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R6 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 4, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
```

Comparison and judgment: All four completed records have seeds 1–4, clean recorded Git state, 248 frozen internal rows and matching actual checkpoint hashes. R1–R6 are six named configurations. D-051 later counts both stages of R8 as one budget item; the total is eight named configurations, nine training stages including R8 stage 1.

## Criterion 9: met

Independent implementations agree within tolerance on all fixtures; disagreements investigated and recorded.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
calibration_R1 {"conformal": [{"alpha": 0.05, "coverage": 0.967741935483871, "delta_pp": 1.774193548387104, "frozen_coverage": null, "q": 0.8455394494903339, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.9193548387096774, "delta_pp": 1.9354838709677358, "frozen_coverage": null, "q": 0.6974491435277447, "within_2pp": "True"}, {"alpha": 0.2, "coverage": 0.7580645161290323, "delta_pp": -4.193548387096779, "frozen_coverage": null, "q": 0.5125601524011015, "within_2pp": "False"}], "frozen_temperature": 1.3522186414952444, "metrics": {"M1_raw": {"brier": 0.17122640446513873, "ece10": 0.18632296135242835, "ece15": 0.20086028558006136, "ece5": 0.18106110911802012, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1690488053601114, "ece10": 0.1912250297111532, "ece15": 0.20264670276718383, "ece5": 0.1837739074667965, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.352218637025625}
calibration_R2 {"conformal": [{"alpha": 0.05, "coverage": 0.9596774193548387, "delta_pp": 0.967741935483879, "frozen_coverage": null, "q": 0.777272182418763, "within_2pp": "True"}, {"alpha": 0.1, "coverage": 0.8709677419354839, "delta_pp": -2.9032258064516148, "frozen_coverage": null, "q": 0.6621427078933437, "within_2pp": "False"}, {"alpha": 0.2, "coverage": 0.7258064516129032, "delta_pp": -7.41935483870968, "frozen_coverage": null, "q": 0.39233359333855317, "within_2pp": "False"}], "frozen_temperature": 1.1247560944350967, "metrics": {"M1_raw": {"brier": 0.13992721006181305, "ece10": 0.11886621431386386, "ece15": 0.11986276143409659, "ece5": 0.0958629546491839, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}, "M2_scaled": {"brier": 0.1387178219344037, "ece10": 0.12216069353330185, "ece15": 0.13631738075696587, "ece5": 0.10760289362523177, "reliability_bins": 10, "stored_keys": ["classification", "selective"]}}, "temperature": 1.1247561048090786}
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-pytest --ignore=tests/unit/test_external_evaluation.py --ignore=tests/unit/test_freeze_manifest.py --ignore=tests/unit/test_paper_artifacts.py --ignore=tests/unit/test_firewall.py --ignore=tests/unit/test_prediction_freeze.py --ignore=tests/unit/test_audit_external_leak.py
```

Output (trimmed):

```text
966 passed, 1 skipped, 1 warning in 63.07s
SKIPPED tests/unit/test_dataset.py:224: sandbox blocks PyTorch worker shared memory
```

Additional exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -m pytest tests/reference -q -p no:cacheprovider --basetemp=/private/tmp/gate-d-reference
```

Output (trimmed):

```text
83 passed in 0.73s
```

Comparison and judgment: The existing independently written calibration/conformal references were re-run, not accepted from the contract prose. Unit calibration metrics cross-check 200 random cases at 1e-12; reference suite checks conformal fixtures and randomized agreement. Reviewer numeric rederivation also agrees. No disagreement requiring reconciliation was observed.

## Criterion 10: met

Prediction artifacts frozen for all mechanisms on the internal test set.

Exact command run:

```sh
env GLIOMA_STORAGE_ROOT=/Volumes/Research_2 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/private/tmp/gate-d-mpl /Users/aniketsaha/4th_Year/Glioma/.venv/bin/python -c 'from pathlib import Path; p=Path("docs/research/protocols/GATE_D_REVIEW_PHASE07_CODEX.md"); exec(compile(p.read_text().split("<!-- BEGIN REVIEW CHECKER -->\n```python\n",1)[1].split("\n```",1)[0],str(p),"exec"))'
```

Output (trimmed):

```text
mc_dropout {"columns": ["patient_id", "cohort", "modality_condition", "run_id", "checkpoint_hash", "p_hat", "logit", "mc_dropout_samples", "ensemble_member_probs", "nonconformity_score", "label"], "pass_counts": [30], "rows": 248}
ensemble_R3 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 1, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R4 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 2, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R5 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 3, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
ensemble_R6 {"checkpoint_hash_matches": true, "git_dirty": false, "rows": 248, "seed": 4, "splits": {"utsw_calibration": 124, "utsw_internal_test": 124}, "status": "completed"}
```

Comparison and judgment: The frozen substrate contains R1/R2 probabilities/logits, R2 MC passes (30 per row), and R2–R6 member predictions. Calibration and conformal parameters/metrics are in hash-verified JSON. Later condition files extend this to all masks. M4 variance and M5 nonconformity are derived from these frozen primitives; separate parquets for every named mechanism are not required to reproduce them.

## Additional check of every Phase 07 result table

The criterion commands above also run `full_phase07_tables()` in this report. It independently derives the classification, selective-risk, rejected-correct, conformal-set and CRC tables from the original frozen R1/R2 files, plus the M3 table from the original MC artifact. All values match the displayed precision in PHASE07_INTERNAL_RESULTS.md; numeric assertions compare against the original internal_analysis.json blocks. This includes the previously uninvestigated ECE/coverage failures; no result was changed.

Output (trimmed only by selecting these tags):

```text
full_document_tables_R1 {"CRC": [{"accepted_and_wrong_rate": 0.03225806451612903, "alpha": 0.05, "coverage": 0.28225806451612906, "risk_among_accepted": 0.11428571428571428, "tau": 0.8459276602189897}, {"accepted_and_wrong_rate": 0.08064516129032258, "alpha": 0.1, "coverage": 0.5887096774193549, "risk_among_accepted": 0.136986301369863, "tau": 0.7005336637865482}, {"accepted_and_wrong_rate": 0.24193548387096775, "alpha": 0.2, "coverage": 0.9838709677419355, "risk_among_accepted": 0.2459016393442623, "tau": 0.5127867884014318}], "classification_selective": {"M1_raw": {"accuracy": 0.7419354838709677, "always_predict_error": 0.25806451612903225, "auprc": 0.7429757990636939, "aurc_mean": 0.13425844311173038, "aurc_trapezoid": 0.13321786038540365, "auroc": 0.8719101123595505, "operating_points": {"0.5": {"coverage": 0.5, "rejected_correct": 0.6129032258064516, "risk": 0.12903225806451613}, "0.6": {"coverage": 0.6048387096774194, "rejected_correct": 0.5510204081632653, "risk": 0.13333333333333333}, "0.7": {"coverage": 0.7016129032258065, "rejected_correct": 0.5405405405405406, "risk": 0.1724137931034483}, "0.8": {"coverage": 0.8064516129032258, "rejected_correct": 0.5, "risk": 0.2}, "0.9": {"coverage": 0.9032258064516129, "rejected_correct": 0.5, "risk": 0.23214285714285715}}, "sensitivity": 0.8571428571428571, "specificity": 0.6966292134831461, "violations": 706}, "M2_scaled": {"accuracy": 0.7419354838709677, "always_predict_error": 0.25806451612903225, "auprc": 0.7429757990636939, "aurc_mean": 0.13425844311173038, "aurc_trapezoid": 0.13321786038540365, "auroc": 0.8719101123595505, "operating_points": {"0.5": {"coverage": 0.5, "rejected_correct": 0.6129032258064516, "risk": 0.12903225806451613}, "0.6": {"coverage": 0.6048387096774194, "rejected_correct": 0.5510204081632653, "risk": 0.13333333333333333}, "0.7": {"coverage": 0.7016129032258065, "rejected_correct": 0.5405405405405406, "risk": 0.1724137931034483}, "0.8": {"coverage": 0.8064516129032258, "rejected_correct": 0.5, "risk": 0.2}, "0.9": {"coverage": 0.9032258064516129, "rejected_correct": 0.5, "risk": 0.23214285714285715}}, "sensitivity": 0.8571428571428571, "specificity": 0.6966292134831461, "violations": 706}}, "conformal": [{"abstention_rate": 0.717741935483871, "alpha": 0.05, "coverage": 0.967741935483871, "empty_count": 0, "full_count": 89, "singleton_count": 35, "singleton_true_label_fraction": 0.8857142857142857}, {"abstention_rate": 0.4032258064516129, "alpha": 0.1, "coverage": 0.9193548387096774, "empty_count": 0, "full_count": 50, "singleton_count": 74, "singleton_true_label_fraction": 0.8648648648648649}, {"abstention_rate": 0.016129032258064516, "alpha": 0.2, "coverage": 0.7580645161290323, "empty_count": 0, "full_count": 2, "singleton_count": 122, "singleton_true_label_fraction": 0.7540983606557377}]}
full_document_tables_R2 {"CRC": [{"accepted_and_wrong_rate": 0.04032258064516129, "alpha": 0.05, "coverage": 0.5887096774193549, "risk_among_accepted": 0.0684931506849315, "tau": 0.7776559975334465}, {"accepted_and_wrong_rate": 0.12903225806451613, "alpha": 0.1, "coverage": 0.8064516129032258, "risk_among_accepted": 0.16, "tau": 0.6656220612666907}, {"accepted_and_wrong_rate": 0.21774193548387097, "alpha": 0.2, "coverage": 1.0, "risk_among_accepted": 0.21774193548387097, "tau": 0.5043350889303098}], "classification_selective": {"M1_raw": {"accuracy": 0.782258064516129, "always_predict_error": 0.21774193548387097, "auprc": 0.7782311870661562, "aurc_mean": 0.07553439802055385, "aurc_trapezoid": 0.07465640634521564, "auroc": 0.878330658105939, "operating_points": {"0.5": {"coverage": 0.5, "rejected_correct": 0.6129032258064516, "risk": 0.04838709677419355}, "0.6": {"coverage": 0.6048387096774194, "rejected_correct": 0.5918367346938775, "risk": 0.09333333333333334}, "0.7": {"coverage": 0.7016129032258065, "rejected_correct": 0.5405405405405406, "risk": 0.11494252873563218}, "0.8": {"coverage": 0.8064516129032258, "rejected_correct": 0.5416666666666666, "risk": 0.16}, "0.9": {"coverage": 0.9032258064516129, "rejected_correct": 0.3333333333333333, "risk": 0.16964285714285715}}, "sensitivity": 0.7428571428571429, "specificity": 0.797752808988764, "violations": 253}, "M2_scaled": {"accuracy": 0.782258064516129, "always_predict_error": 0.21774193548387097, "auprc": 0.7782311870661562, "aurc_mean": 0.07553439802055385, "aurc_trapezoid": 0.07465640634521564, "auroc": 0.878330658105939, "operating_points": {"0.5": {"coverage": 0.5, "rejected_correct": 0.6129032258064516, "risk": 0.04838709677419355}, "0.6": {"coverage": 0.6048387096774194, "rejected_correct": 0.5918367346938775, "risk": 0.09333333333333334}, "0.7": {"coverage": 0.7016129032258065, "rejected_correct": 0.5405405405405406, "risk": 0.11494252873563218}, "0.8": {"coverage": 0.8064516129032258, "rejected_correct": 0.5416666666666666, "risk": 0.16}, "0.9": {"coverage": 0.9032258064516129, "rejected_correct": 0.3333333333333333, "risk": 0.16964285714285715}}, "sensitivity": 0.7428571428571429, "specificity": 0.797752808988764, "violations": 253}}, "conformal": [{"abstention_rate": 0.4112903225806452, "alpha": 0.05, "coverage": 0.9596774193548387, "empty_count": 0, "full_count": 51, "singleton_count": 73, "singleton_true_label_fraction": 0.9315068493150684}, {"abstention_rate": 0.18548387096774194, "alpha": 0.1, "coverage": 0.8709677419354839, "empty_count": 0, "full_count": 23, "singleton_count": 101, "singleton_true_label_fraction": 0.8415841584158416}, {"abstention_rate": 0.12096774193548387, "alpha": 0.2, "coverage": 0.7258064516129032, "empty_count": 15, "full_count": 0, "singleton_count": 109, "singleton_true_label_fraction": 0.8256880733944955}]}
full_document_M3 {"aurc_mean": 0.08036748109202108, "aurc_trapezoid": 0.07948948941668285, "mean_sample_SD": 0.09335963428020477, "p_hat_max_abs_difference": 1.1324882507324219e-06, "risk_grid": {"0.5": 0.06451612903225806, "0.6": 0.10666666666666667, "0.7": 0.11494252873563218, "0.8": 0.17, "0.9": 0.17857142857142858}, "violations": 217}
```

## Findings requiring disposition

F01 blocks an unqualified pass: no required calibration-isolation regression test. F06 records the two already-approved D-058 exceptions; it is not a request to refit anything. D-058’s heading and closing resolution say resolved while its original Status line still says OPEN; the dated closing resolution is the operative decision. PHASE07_INTERNAL_RESULTS.md’s trailing “decision ... owes” is stale.

Next action: Research Lead assigns the isolation test and records D-058 exceptions without altering the frozen results.

## Reproducible read-only checker

The command above executes this embedded code. It contains reviewer calculations and source inspection only; it never calls artifact-writing analysis entry points.

<!-- BEGIN REVIEW CHECKER -->
```python
import sys, os, json, hashlib, math, re, subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import minimize_scalar
from scipy.special import expit
from glioma_selective.utils import paths
assert 'GLIOMA_EXTERNAL_EVAL_AUTHORIZED' not in os.environ
RUNS = ['01M45268QDQ2CFBSPNH117MF41','01M46999FB083AX4WW0067YM13','01M4FPECM9DKAR7F6B7VFRQNC5','01M60CYFD2AYA8DCPBTDSJS4DM','01M66E2KR6ZV2YPBTNPF5FD53T','01M776GTZC70FTB1ABD2DDMYHH','01M7C0KRNY5M2SNH59PH97XZ8K','01M7JZYEBFCJF8WY0W1WJ3RZX7']
ROOT = paths.experiments_dir()
CONDS = ['full','drop_t1','drop_t1ce','drop_t2','drop_flair','t1ce_flair_only']
GRID = [.9,.8,.7,.6,.5]
def emit(tag, value): print(tag, json.dumps(value, sort_keys=True, default=str))
def load(i,name): return json.loads((ROOT/RUNS[i-1]/name).read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def verified(p):
 assert digest(p)==p.with_name(p.name+'.sha256').read_text().split()[0], str(p)
 return True
def frame(i,name='predictions.parquet',split=None):
 p=ROOT/RUNS[i-1]/name; verified(p); f=pd.read_parquet(p)
 assert set(f.cohort)<= {'utsw_calibration','utsw_internal_test'}, str(p)
 if split: f=f[f.cohort=='utsw_'+split]
 assert not f.duplicated(['patient_id','cohort','modality_condition']).any()
 return f.sort_values('patient_id').reset_index(drop=True)
def temp(f):
 z=f.logit.to_numpy(float); y=f.label.to_numpy(int)
 r=minimize_scalar(lambda t:np.mean(np.logaddexp(0,z/np.exp(t))-y*z/np.exp(t)),bounds=(math.log(.05),math.log(20)),method='bounded',options={'xatol':1e-12})
 return float(np.exp(r.x))
def ece(p,y,b=10):
 q=np.minimum((p*b).astype(int),b-1)
 return sum(abs(float(np.sum(p[q==i]-y[q==i])))/len(y) for i in range(b))
def auc(p,y):
 a=p[y==1,None]; b=p[y==0][None,:]
 return float(np.mean((a>b)+.5*(a==b)))
def ap(p,y):
 o=np.argsort(-p,kind='stable'); p=p[o];y=y[o]; k=np.flatnonzero(np.r_[p[1:]!=p[:-1],True])+1
 tp=np.cumsum(y)[k-1];return float(np.sum(np.diff(np.r_[0,tp])*tp/k)/y.sum())
def curve(s,e):
 o=np.argsort(-np.asarray(s),kind='stable'); s=np.asarray(s)[o];e=np.asarray(e)[o]
 k=np.flatnonzero(np.r_[s[1:]!=s[:-1],True])+1; risks=np.cumsum(e)[k-1]/k
 return k,risks,e,o
def area(s,e):
 k,r,_,_=curve(s,e);return float(np.sum(np.diff(np.r_[0,k])*r)/len(e))
def interval(v): return np.quantile(v,[.025,.975])
def close(a,b,tol=1e-9):
 assert np.allclose(a,b,atol=tol,rtol=0), (a,b)
def quantile(p,y,a):
 from fractions import Fraction
 n=len(y); k=math.ceil((n+1)*(1-Fraction(str(a))))
 s=np.where(y==1,1-p,p)
 return float(np.sort(s)[k-1]) if k<=n else math.inf

def phase07():
 for i in [1,2]:
  f=frame(i);cal=f[f.cohort=='utsw_calibration'];test=f[f.cohort=='utsw_internal_test'];T=temp(cal);y=test.label.to_numpy(int);raw=test.p_hat.to_numpy(float);scaled=expit(test.logit.to_numpy(float)/T);cp=expit(cal.logit.to_numpy(float)/T);cy=cal.label.to_numpy(int);j=load(i,'internal_analysis.json'); verified(ROOT/RUNS[i-1]/'internal_analysis.json')
  vals={}
  for m,p in [('M1_raw',raw),('M2_scaled',scaled)]:
   b=j['views'][m];met=b.get('classification',b)
   vals[m]={'ece10':ece(p,y),'ece5':ece(p,y,5),'ece15':ece(p,y,15),'brier':float(np.mean((p-y)**2)),'stored_keys':list(b),'reliability_bins':len(met.get('reliability_bins',[]))}
  cov=[]
  for a in [.05,.1,.2]:
   q=quantile(cp,cy,a);covered=np.where(y==1,1-scaled,scaled)<=q
   item=j['conformal'][str(a)]
   cov.append({'alpha':a,'q':q,'coverage':float(covered.mean()),'delta_pp':100*(covered.mean()-(1-a)),'within_2pp':abs(covered.mean()-(1-a))<=.02,'frozen_coverage':item.get('empirical_coverage')})
  emit('calibration_R'+str(i),{'temperature':T,'frozen_temperature':j['provenance']['temperature'],'metrics':vals,'conformal':cov})
 for i in range(3,7):
  r=load(i,'record.json');f=frame(i)
  emit('ensemble_R'+str(i),{'status':r['status'],'seed':r['seed'],'git_dirty':r['git_dirty'],'checkpoint_hash_matches':digest(ROOT/RUNS[i-1]/'checkpoints/best.pt')==r['checkpoint_hash'],'rows':len(f),'splits':f.groupby('cohort').size().to_dict()})
 mc=frame(2,'mc_dropout.parquet');emit('mc_dropout',{'rows':len(mc),'columns':mc.columns.tolist(),'pass_counts':sorted(set(len(s) for s in mc.mc_dropout_samples))})
 # Distinct patient sets, checked without exposing patient identifiers.
 f=frame(2);ids={k:set(v.patient_id) for k,v in f.groupby('cohort')};emit('cal_test_disjoint',not bool(ids['utsw_calibration']&ids['utsw_internal_test']))
def show(tag, filename, start, end):
    lines=Path(filename).read_text().splitlines()
    emit(tag, [f"{filename}:{i+1}: {line}" for i,line in enumerate(lines) if start<=i+1<=end])
def decision(key):
    text=Path('docs/research/DECISION_LOG.md').read_text()
    sections=text.split('\n## ')
    emit(key,next(x for x in sections if x.startswith(key+' ')))


def full_phase07_tables():
 from fractions import Fraction
 for i in [1,2]:
  f=frame(i);cal=f[f.cohort=='utsw_calibration'];test=f[f.cohort=='utsw_internal_test'];y=test.label.to_numpy(int);cy=cal.label.to_numpy(int);T=temp(cal);p=expit(test.logit.to_numpy(float)/T);cp=expit(cal.logit.to_numpy(float)/T);raw=test.p_hat.to_numpy(float);j=load(i,'internal_analysis.json')
  scalars={}
  for name,prob in [('M1_raw',raw),('M2_scaled',p)]:
   pred=prob>=.5;met={'auroc':auc(prob,y),'auprc':ap(prob,y),'accuracy':float(np.mean(pred==y)),'sensitivity':float(np.mean(pred[y==1])),'specificity':float(np.mean(~pred[y==0]))}
   for key,value in met.items():close(value,j['views'][name]['classification'][key])
   scores=np.maximum(prob,1-prob);k,r,e,o=curve(scores,(pred!=y).astype(int));diff=r[:,None]-r[None,:];tri=np.triu_indices(len(r),1)
   met.update({'aurc_mean':area(scores,(pred!=y).astype(int)),'aurc_trapezoid':float(np.sum(np.diff(k/len(y))*(r[1:]+r[:-1])/2)),'violations':int(np.sum(diff[tri]>1e-15)),'always_predict_error':float(np.mean(pred!=y)),'operating_points':{str(g):{'risk':float(r[np.searchsorted(k/len(y),g)]),'coverage':float(k[np.searchsorted(k/len(y),g)]/len(y)),'rejected_correct':float(np.mean(1-e[k[np.searchsorted(k/len(y),g)]:]))} for g in GRID}})
   close(met['aurc_mean'],j['views'][name]['selective']['aurc_mean_over_cutoffs']);scalars[name]=met
  sets=[];crcs=[]
  for a in [.05,.1,.2]:
   q=quantile(cp,cy,a);zero=p<=q;one=1-p<=q;single=zero^one;covered=np.where(y==1,one,zero);cf={'alpha':a,'coverage':float(covered.mean()),'abstention_rate':float((~single).mean()),'singleton_count':int(single.sum()),'empty_count':int((~zero & ~one).sum()),'full_count':int((zero & one).sum()),'singleton_true_label_fraction':float(covered[single].mean())}
   for key,value in cf.items():close(value,j['conformal'][str(a)][key])
   sets.append(cf);confidence=np.maximum(cp,1-cp);wrong=(cp>=.5)!=cy
   tau=next((float(t) for t in sorted(set(confidence)) if Fraction(int(np.sum(wrong & (confidence>=t)))+1,len(cy)+1)<=Fraction(str(a))),math.inf)
   accept=np.maximum(p,1-p)>=tau;wrongtest=(p>=.5)!=y;crc={'alpha':a,'tau':tau,'coverage':float(accept.mean()),'accepted_and_wrong_rate':float(np.mean(accept & wrongtest)),'risk_among_accepted':float(wrongtest[accept].mean())}
   for key,value in crc.items():close(value,j['crc'][str(a)][key],2e-7)
   crcs.append(crc)
  emit('full_document_tables_R'+str(i),{'classification_selective':scalars,'conformal':sets,'CRC':crcs})
 f=frame(2,'mc_dropout.parquet',split='internal_test');base=frame(2,split='internal_test');prob=base.p_hat.to_numpy(float);y=f.label.to_numpy(int);samples=np.asarray(f.mc_dropout_samples.tolist());mean=samples.mean(axis=1);scores=mean*np.log(mean)+(1-mean)*np.log(1-mean);k,r,_,_=curve(scores,((prob>=.5)!=y).astype(int));dd=r[:,None]-r[None,:]
 emit('full_document_M3',{'aurc_mean':area(scores,((prob>=.5)!=y).astype(int)),'aurc_trapezoid':float(np.sum(np.diff(k/len(y))*(r[1:]+r[:-1])/2)),'violations':int(np.sum(dd[np.triu_indices(len(r),1)]>1e-15)),'risk_grid':{str(g):float(r[np.searchsorted(k/len(y),g)]) for g in GRID},'mean_sample_SD':float(samples.std(axis=1).mean()),'p_hat_max_abs_difference':float(np.max(np.abs(f.p_hat.to_numpy(float)-base.p_hat.to_numpy(float))))})
full_phase07_tables()

phase07()
decision('D-002'); decision('D-058')
show('fit_source','src/glioma_selective/evaluation/internal_analysis.py',230,245)
show('quantile_source','src/glioma_selective/calibration/conformal.py',65,110)
show('separate_condition_fits','src/glioma_selective/evaluation/condition_analysis.py',250,290)
for name in ['internal_analysis','condition_analysis','phase09_analysis']:
    path=Path('tests/unit/test_'+name+'.py')
    emit('tests_'+name,[f'{path}:{n}: {v}' for n,v in enumerate(path.read_text().splitlines(),1) if v.startswith('def test_')])
for name in ['calibration/temperature.py','calibration/conformal.py','calibration/crc.py','uncertainty/mc_dropout.py','selective/abstention.py']:
    path=Path('src/glioma_selective')/name
    emit('module_'+name,[v for v in path.read_text().splitlines() if v.startswith(('def ','class ','_'))][:24])

```
