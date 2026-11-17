# ruff: noqa: E501
"""Independent recomputation of the Phase 10 internal headline numbers (Person C pack).

Reads only frozen prediction files and ``phase10_analysis.json`` (as the thing to
check). Imports nothing from ``glioma_selective``: every metric is written out here
from the definitions in ``docs/research/protocols/PHASE09_METRIC_CONTRACTS.md`` and
``PHASE10_STATS_CONTRACTS.md``. Needs numpy and pandas (with pyarrow). CPU only; about
one minute. Internal UTSW data only; never point it at an external cohort.

    python scripts/person_c_recompute.py --results-root PATH/TO/experiments
    python scripts/person_c_recompute.py --results-root PATH --reference phase10_analysis.json

Exit status 0 when every number agrees within tolerance, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ITERATIONS = 2000
SEED = 0
TOL = 1e-9  # points, interval limits (same index matrix), calibration numbers
TOL_T = 1e-6  # calibration numbers: float32 storage noise (~1e-8) and the reference's bisection
# stopping at 1e-8 in 1/T, which leaves its T off by up to ~1e-6
Z975 = 1.959963984540054  # 97.5th percentile of the standard normal
COVERAGES = (0.5, 0.6, 0.7, 0.8, 0.9)
CONDITIONS = ("drop_t1", "drop_t1ce", "drop_t2", "drop_flair", "t1ce_flair_only")


# ----------------------------------------------------------------- loading


def _verified_parquet(path: Path) -> pd.DataFrame:
    sidecar = path.with_name(path.name + ".sha256")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if sidecar.read_text().split()[0] != digest:
        raise SystemExit(f"hash mismatch, refusing to use {path}")
    return pd.read_parquet(path)


def _split(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    rows = frame[frame["cohort"] == cohort].sort_values("patient_id")
    if rows["patient_id"].duplicated().any():
        raise SystemExit("duplicate patient ids")
    return rows.reset_index(drop=True)


class Run:
    """One run's frozen predictions for one condition: calibration and test rows."""

    def __init__(self, frame: pd.DataFrame):
        cal = _split(frame, "utsw_calibration")
        test = _split(frame, "utsw_internal_test")
        self.cal_logit = cal["logit"].to_numpy(float)
        self.cal_label = cal["label"].to_numpy(int)
        self.ids = test["patient_id"].tolist()
        self.logit = test["logit"].to_numpy(float)
        self.p = test["p_hat"].to_numpy(float)
        self.label = test["label"].to_numpy(int)
        self.mc = np.asarray(test["mc_dropout_samples"].tolist(), dtype=float)

    @property
    def error(self) -> np.ndarray:
        """0/1 error of the raw probability at threshold 0.5."""
        return ((self.p >= 0.5) != (self.label == 1)).astype(float)


# ----------------------------------------------------------------- metrics


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def fit_temperature(logit: np.ndarray, label: np.ndarray) -> float:
    """Minimise mean binary cross-entropy of sigmoid(logit / T) over T in [0.05, 20]."""
    lo, hi = 1 / 20.0, 1 / 0.05  # search in w = 1 / T

    def grad(w: float) -> float:
        return float(np.mean(logit * (sigmoid(w * logit) - label)))

    if grad(lo) >= 0:
        return 20.0
    if grad(hi) <= 0:
        return 0.05
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if grad(mid) > 0 else (mid, hi)
    return 1.0 / ((lo + hi) / 2)


def auroc(score: np.ndarray, label: np.ndarray) -> float:
    pos, neg = score[label == 1], score[label == 0]
    diff = pos[:, None] - neg[None, :]
    return float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / diff.size)


def average_precision(score: np.ndarray, label: np.ndarray) -> float:
    """Non-interpolated AP; tied scores form one threshold."""
    order = np.argsort(-score, kind="stable")
    s, y = score[order], label[order]
    tp = np.cumsum(y)
    ends = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    recall = tp[ends] / y.sum()
    precision = tp[ends] / (ends + 1)
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def rc_points(score: np.ndarray, loss: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(patients accepted, risk) at the end of each tie block, score descending."""
    order = np.argsort(-score, kind="stable")
    s, ell = score[order], loss[order]
    ends = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    return ends + 1, np.cumsum(ell)[ends] / (ends + 1)


def aurc(score: np.ndarray, loss: np.ndarray) -> float:
    """Mean over cutoffs k = 1..n of the risk at k; a cutoff inside a tie block takes the block's end."""
    counts, risks = rc_points(score, loss)
    n = len(score)
    per_cutoff = risks[np.searchsorted(counts, np.arange(1, n + 1), side="left")]
    return float(per_cutoff.mean())


def selective_risk(
    score: np.ndarray, loss: np.ndarray, target: float
) -> tuple[float, float]:
    """First risk-coverage point with coverage >= target (exact comparison)."""
    counts, risks = rc_points(score, loss)
    n = len(score)
    need = Fraction(repr(target))
    for count, risk in zip(counts, risks, strict=True):
        if Fraction(int(count), n) >= need:
            return count / n, float(risk)
    raise AssertionError("unreachable: last point has coverage 1")


def brier(p: np.ndarray, label: np.ndarray) -> float:
    return float(np.mean((p - label) ** 2))


def _bins(p: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """floor(n_bins * p) from the decimal spelling, exact; p = 1 goes in the last bin."""
    out = []
    for value in p:
        scaled = Fraction(repr(float(value))) * n_bins
        out.append(min(scaled.numerator // scaled.denominator, n_bins - 1))
    return np.asarray(out)


def ece(p: np.ndarray, label: np.ndarray, bins: np.ndarray) -> float:
    total = 0.0
    for b in range(10):
        members = bins == b
        if members.any():
            total += members.mean() * abs(label[members].mean() - p[members].mean())
    return float(total)


def entropy_score(mc: np.ndarray) -> np.ndarray:
    """M3: minus the entropy (nats) of the mean MC-dropout probability."""
    q = mc.mean(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -(
            np.where(q > 0, q * np.log(q), 0)
            + np.where(q < 1, (1 - q) * np.log(1 - q), 0)
        )
    return -h


def hanley_mcneil(auc: float, m: int, n: int) -> tuple[float, float]:
    q1, q2 = auc / (2 - auc), 2 * auc * auc / (1 + auc)
    var = (auc * (1 - auc) + (m - 1) * (q1 - auc**2) + (n - 1) * (q2 - auc**2)) / (
        m * n
    )
    half = Z975 * math.sqrt(max(var, 0.0))
    return auc - half, auc + half


def delong_p(a: np.ndarray, b: np.ndarray, label: np.ndarray) -> tuple[float, float]:
    """Paired DeLong test: (AUC_a - AUC_b, two-sided p)."""
    pos, neg = label == 1, label == 0
    m, n = int(pos.sum()), int(neg.sum())

    def psi(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        d = x[:, None] - y[None, :]
        return (d > 0) + 0.5 * (d == 0)

    v10, v01, auc = [], [], []
    for s in (a, b):
        mat = psi(s[pos], s[neg])
        v10.append(mat.mean(axis=1))
        v01.append(mat.mean(axis=0))
        auc.append(mat.mean())
    s10 = np.cov(np.vstack(v10), ddof=1)
    s01 = np.cov(np.vstack(v01), ddof=1)
    var = (s10[0, 0] + s10[1, 1] - 2 * s10[0, 1]) / m + (
        s01[0, 0] + s01[1, 1] - 2 * s01[0, 1]
    ) / n
    diff = auc[0] - auc[1]
    if var == 0:
        return diff, 1.0 if diff == 0 else 0.0
    return diff, math.erfc(abs(diff / math.sqrt(var)) / math.sqrt(2))


# --------------------------------------------------------------- bootstrap


def interval(values: np.ndarray) -> tuple[float, float]:
    lo, hi = np.percentile(values, [2.5, 97.5])
    return float(lo), float(hi)


def paired_p(draws: np.ndarray) -> Fraction:
    """min(1, 2 (1 + min(#d<=0, #d>=0)) / (B + 1)), exact."""
    le, ge = int((draws <= 0).sum()), int((draws >= 0).sum())
    return min(Fraction(1), Fraction(2 * (1 + min(le, ge)), len(draws) + 1))


def boot(
    stat: Callable[[np.ndarray], float],
    idx: np.ndarray,
    valid: np.ndarray | None = None,
) -> np.ndarray:
    rows = idx if valid is None else idx[valid]
    return np.asarray([stat(row) for row in rows])


# ------------------------------------------------------------------ checks


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, float, float, float, bool]] = []

    def add(self, name: str, mine: float, ref: float, tol: float = TOL) -> None:
        ok = abs(mine - ref) <= tol
        self.rows.append((name, mine, ref, abs(mine - ref), ok))

    def add_p(self, name: str, mine: Fraction | float, ref: str | float) -> None:
        if isinstance(mine, Fraction):
            ok = mine == Fraction(str(ref))
            self.rows.append(
                (name, float(mine), float(Fraction(str(ref))), 0.0 if ok else 1.0, ok)
            )
        else:
            self.add(name, mine, float(ref), 1e-9)

    def print(self) -> int:
        failed = [r for r in self.rows if not r[4]]
        for name, mine, ref, diff, ok in self.rows:
            print(
                f"{'ok  ' if ok else 'FAIL'} {name:58s} mine={mine:<22.12g} ref={ref:<22.12g} |d|={diff:.2e}"
            )
        print(f"\n{len(self.rows) - len(failed)} of {len(self.rows)} numbers agree")
        return 1 if failed else 0


def _rb(
    report: Report,
    name: str,
    block: dict[str, Any],
    mine: float,
    lo: float,
    hi: float,
    tol: float = TOL,
) -> None:
    report.add(name + " point", mine, block["point"], tol)
    report.add(name + " lower", lo, block["bootstrap_95_interval"]["lower"], tol)
    report.add(name + " upper", hi, block["bootstrap_95_interval"]["upper"], tol)


def check_run(
    name: str,
    run: Run,
    ref: dict[str, Any],
    idx: np.ndarray,
    valid: np.ndarray,
    report: Report,
) -> np.ndarray:
    """Per-run block (AUROC, AUPRC, AURC, selective risk, ECE, Brier). Returns the M5 score."""
    label = run.label
    temperature = fit_temperature(run.cal_logit, run.cal_label)
    report.add(f"{name} temperature", temperature, ref["temperature"], TOL_T)
    q = sigmoid(run.logit / temperature)
    m5 = np.maximum(q, 1 - q)

    point = auroc(run.p, label)
    lo, hi = interval(boot(lambda r: auroc(run.p[r], label[r]), idx, valid))
    _rb(report, f"{name} AUROC", ref["auroc"], point, lo, hi)
    hm = hanley_mcneil(point, int(label.sum()), int((1 - label).sum()))
    report.add(
        f"{name} AUROC Hanley-McNeil lower",
        hm[0],
        ref["auroc"]["hanley_mcneil_95_interval"]["lower"],
    )
    report.add(
        f"{name} AUROC Hanley-McNeil upper",
        hm[1],
        ref["auroc"]["hanley_mcneil_95_interval"]["upper"],
    )

    point = average_precision(run.p, label)
    lo, hi = interval(boot(lambda r: average_precision(run.p[r], label[r]), idx, valid))
    _rb(report, f"{name} AUPRC", ref["auprc"], point, lo, hi)

    err = run.error
    point = aurc(m5, err)
    lo, hi = interval(boot(lambda r: aurc(m5[r], err[r]), idx))
    _rb(report, f"{name} AURC (M5)", ref["aurc_mean_over_cutoffs"], point, lo, hi)

    for target in COVERAGES:
        block = ref["selective_risk_at_coverage"][str(target)]
        attained, risk = selective_risk(m5, err, target)
        report.add(
            f"{name} sel. risk @{target} attained coverage",
            attained,
            block["attained_coverage"],
        )
        lo, hi = interval(
            boot(lambda r, t=target: selective_risk(m5[r], err[r], t)[1], idx)
        )
        _rb(report, f"{name} sel. risk @{target}", block, risk, lo, hi)

    for key, p in (("M1", run.p), ("M2", q)):
        bins = _bins(p)
        for metric, fn in (
            ("ece", lambda r, p=p, bins=bins: ece(p[r], label[r], bins[r])),
            ("brier", lambda r, p=p: brier(p[r], label[r])),
        ):
            point = fn(np.arange(len(label)))
            lo, hi = interval(boot(fn, idx))
            _rb(
                report,
                f"{name} {metric.upper()} {key}",
                ref["calibration"][key][metric],
                point,
                lo,
                hi,
                TOL_T,
            )
    return m5


def check_confirmatory(
    ref: dict[str, Any],
    r2: Run,
    conds: dict[str, Run],
    members: list[Run],
    r7: Run,
    r8: Run,
    idx: np.ndarray,
    report: Report,
) -> None:
    label = r2.label
    t_full = fit_temperature(r2.cal_logit, r2.cal_label)

    def m5_of(run: Run) -> np.ndarray:
        q = sigmoid(run.logit / t_full)
        return np.maximum(q, 1 - q)

    full_m5 = m5_of(r2)
    full_err = r2.error
    m3 = entropy_score(conds["full"].mc)
    member_p = np.column_stack([r2.p] + [m.p for m in members])
    m4 = -member_p.var(axis=1)  # population variance
    m4_err = ((member_p.mean(axis=1) >= 0.5) != (label == 1)).astype(float)

    def diff(
        name: str,
        a: Callable[[np.ndarray], float],
        b: Callable[[np.ndarray], float],
        tol: float = TOL,
    ) -> None:
        block = ref["confirmatory"][name]
        point = a(np.arange(len(label))) - b(np.arange(len(label)))
        draws = np.asarray([a(r) - b(r) for r in idx])
        lo, hi = interval(draws)
        report.add(f"{name} point", point, block["point"], tol)
        report.add(f"{name} lower", lo, block["lower"], tol)
        report.add(f"{name} upper", hi, block["upper"], tol)
        report.add_p(f"{name} p", paired_p(draws), block["p_value"])

    a_m5 = lambda r: aurc(full_m5[r], full_err[r])  # noqa: E731
    diff("A1", a_m5, lambda r: aurc(m3[r], full_err[r]))
    diff("A2", a_m5, lambda r: aurc(m4[r], m4_err[r]))
    diff("A3", lambda r: aurc(m3[r], full_err[r]), lambda r: aurc(m4[r], m4_err[r]))
    for i, c in enumerate(CONDITIONS, start=1):
        cm5, cerr = m5_of(conds[c]), conds[c].error
        diff(f"B{i}", lambda r, cm5=cm5, cerr=cerr: aurc(cm5[r], cerr[r]), a_m5)

    q = sigmoid(r2.logit / t_full)
    bins1, bins2 = _bins(r2.p), _bins(q)
    diff(
        "D1",
        lambda r: ece(r2.p[r], label[r], bins1[r]),
        lambda r: ece(q[r], label[r], bins2[r]),
        TOL_T,
    )
    diff(
        "D2", lambda r: brier(r2.p[r], label[r]), lambda r: brier(q[r], label[r]), TOL_T
    )

    # E1, E3: DeLong p for the AUROC difference (raw logits), bootstrap interval beside it.
    valid = _valid(label, idx)
    for name, other in (("E1", r7), ("E3", r8)):
        block = ref["confirmatory"][name]
        d, p = delong_p(other.logit, r2.logit, label)
        draws = np.asarray(
            [
                auroc(other.logit[r], label[r]) - auroc(r2.logit[r], label[r])
                for r in idx[valid]
            ]
        )
        lo, hi = interval(draws)
        report.add(f"{name} point", d, block["point"])
        report.add(f"{name} lower", lo, block["lower"])
        report.add(f"{name} upper", hi, block["upper"])
        report.add_p(f"{name} DeLong p", p, block["p_value"])
    for name, other in (("E2", r7), ("E4", r8)):
        om5 = m5_of_own(other)
        diff(name, lambda r, om5=om5, o=other: aurc(om5[r], o.error[r]), a_m5)


def m5_of_own(run: Run) -> np.ndarray:
    """M5 score of a run with that run's own temperature."""
    q = sigmoid(run.logit / fit_temperature(run.cal_logit, run.cal_label))
    return np.maximum(q, 1 - q)


def _valid(label: np.ndarray, idx: np.ndarray) -> np.ndarray:
    positives = label[idx].sum(axis=1)
    return (positives > 0) & (positives < label.size)


# -------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        required=True,
        help="directory holding <run_id>/ folders",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="phase10_analysis.json (default: inside the primary run folder)",
    )
    args = parser.parse_args(argv)

    ref_path = args.reference
    if ref_path is None:
        candidates = sorted(args.results_root.glob("*/phase10_analysis.json"))
        candidates = [c for c in candidates if "preliminary" not in c.name]
        if len(candidates) != 1:
            raise SystemExit("pass --reference")
        ref_path = candidates[0]
    sidecar = ref_path.with_name(ref_path.name + ".sha256")
    if (
        sidecar.exists()
        and sidecar.read_text().split()[0]
        != hashlib.sha256(ref_path.read_bytes()).hexdigest()
    ):
        raise SystemExit("reference file does not match its sha256 sidecar")
    ref = json.loads(ref_path.read_text())
    seed, iterations = ref["provenance"]["seed"], ref["provenance"]["iterations"]
    if (seed, iterations) != (SEED, ITERATIONS):
        print(
            f"note: reference used seed {seed}, iterations {iterations}",
            file=sys.stderr,
        )
    root = args.results_root
    r2_id = ref["provenance"]["run_id"]
    member_ids = [
        i for i in ref["provenance"]["ensemble_checkpoint_hashes"] if i != r2_id
    ]

    def predictions(run_id: str) -> Run:
        return Run(_verified_parquet(root / run_id / "predictions.parquet"))

    def condition(run_id: str, name: str) -> Run:
        return Run(_verified_parquet(root / run_id / "conditions" / f"{name}.parquet"))

    r2 = predictions(r2_id)
    r7, r8 = (
        predictions(ref["runs"]["R7"]["run_id"]),
        predictions(ref["runs"]["R8"]["run_id"]),
    )
    for other in (r7, r8):
        if other.ids != r2.ids or not np.array_equal(other.label, r2.label):
            raise SystemExit("patients or labels differ between runs")
    members = [condition(i, "full") for i in member_ids]
    conds = {c: condition(r2_id, c) for c in ("full", *CONDITIONS)}
    n = len(r2.ids)
    print(
        f"{n} internal-test patients, {int(r2.label.sum())} IDH-mutant; reference {ref_path.name}\n"
    )

    idx = np.random.default_rng(seed).integers(
        0, n, size=(iterations, n), dtype=np.int64
    )
    valid = _valid(r2.label, idx)
    report = Report()
    for name, run in (("R2", r2), ("R7", r7), ("R8", r8)):
        check_run(name, run, ref["runs"][name], idx, valid, report)
    check_confirmatory(ref, r2, conds, members, r7, r8, idx, report)
    return report.print()


if __name__ == "__main__":
    raise SystemExit(main())
