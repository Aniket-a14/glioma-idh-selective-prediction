#!/usr/bin/env python3
"""Independent Phase 10 recomputation from the four permitted prose contracts.

Only NumPy and pandas/pyarrow are third-party runtime dependencies. The compute
command cannot read the reference JSON; compare requires an already-written
results file and never evaluates a scientific statistic. Outputs are exclusive
creation to preserve the pre-comparison record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

RUNS = {
    "R2": "01M46999FB083AX4WW0067YM13",
    "R3": "01M4FPECM9DKAR7F6B7VFRQNC5",
    "R4": "01M60CYFD2AYA8DCPBTDSJS4DM",
    "R5": "01M66E2KR6ZV2YPBTNPF5FD53T",
    "R6": "01M776GTZC70FTB1ABD2DDMYHH",
    "R7": "01M7C0KRNY5M2SNH59PH97XZ8K",
    "R8": "01M7JZYEBFCJF8WY0W1WJ3RZX7",
}
CONDITIONS = [
    "full",
    "drop_t1",
    "drop_t1ce",
    "drop_t2",
    "drop_flair",
    "t1ce_flair_only",
]
GRID = [0.5, 0.6, 0.7, 0.8, 0.9]


def verified_bytes(path: Path, hashes: dict) -> bytes:
    """Fail closed on a missing/malformed/mismatching SHA-256 sidecar."""
    payload = path.read_bytes()
    expected = Path(str(path) + ".sha256").read_text().split()[0]
    actual = hashlib.sha256(payload).hexdigest()
    if len(expected) != 64 or actual != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")
    hashes[str(path)] = actual
    return payload


def write_json(path: Path, value: dict) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def sigmoid(z: np.ndarray) -> np.ndarray:
    return np.exp(-np.logaddexp(0.0, -z))


def temperature(z: np.ndarray, y: np.ndarray) -> float:
    """Minimize calibration BCE in inverse temperature u in [1/20, 1/.05].

    BCE(u) = mean(logaddexp(0, u*z) - y*u*z) is convex in u.
    Its derivative is mean(z * (sigmoid(u*z) - y)).
    """
    lower, upper = 1 / 20, 1 / 0.05

    def derivative(u):
        return np.mean(z * (sigmoid(u * z) - y))

    if derivative(lower) >= 0:
        return 1 / lower
    if derivative(upper) <= 0:
        return 1 / upper
    for _ in range(100):
        middle = (lower + upper) / 2
        if derivative(middle) < 0:
            lower = middle
        else:
            upper = middle
    return 1 / ((lower + upper) / 2)


def roc_auc(p: np.ndarray, y: np.ndarray) -> float:
    """Probability that a random positive outranks a negative, half for ties."""
    positive, negative = p[y == 1], p[y == 0]
    return float(
        np.mean((positive[:, None] > negative) + 0.5 * (positive[:, None] == negative))
    )


def average_precision(p: np.ndarray, y: np.ndarray) -> float:
    """Step PR integral: sum of recall increments times block-end precision."""
    order = np.argsort(-p, kind="stable")
    scores, labels = p[order], y[order]
    ends = np.r_[np.flatnonzero(scores[:-1] != scores[1:]) + 1, len(y)]
    tp = np.cumsum(labels)[ends - 1]
    return float(np.sum(np.diff(np.r_[0, tp]) * tp / ends) / np.sum(y))


def selective(scores: np.ndarray, losses: np.ndarray) -> dict:
    """Every tie block enters together; its end risk fills all its cutoffs."""
    order = np.argsort(-scores, kind="stable")
    s, loss = scores[order], losses[order]
    ends = np.r_[np.flatnonzero(s[:-1] != s[1:]) + 1, len(s)]
    counts = np.diff(np.r_[0, ends])
    errors = np.cumsum(loss, dtype=np.int64)[ends - 1]
    risks = errors / ends
    # Exact rational block sum, rounded only once, per Phase 09 convention.
    area = sum(
        (
            Fraction(int(w * e), int(k))
            for w, e, k in zip(counts, errors, ends, strict=True)
        ),
        Fraction(),
    ) / len(s)
    result = {"aurc": float(area)}
    for target in GRID:
        # Integer cross-products avoid the float ceil(124 * target) trap.
        t = Fraction(str(target))
        position = next(
            i
            for i, k in enumerate(ends)
            if int(k) * t.denominator >= len(s) * t.numerator
        )
        result[f"risk_{target}"] = float(risks[position])
        result[f"coverage_{target}"] = float(ends[position] / len(s))
    return result


def ece(p: np.ndarray, y: np.ndarray) -> float:
    """Positive-class ECE: sum_b |sum_{i in b}(p_i-y_i)| / n."""
    bins = np.minimum(np.searchsorted(np.linspace(0, 1, 11), p, side="right") - 1, 9)
    return float(np.abs(np.bincount(bins, weights=p - y, minlength=10)).sum() / len(y))


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def interval(values: np.ndarray) -> tuple[float, float]:
    lower, upper = np.quantile(values, [0.025, 0.975], method="linear")
    return float(lower), float(upper)


def bootstrap_p(values: np.ndarray) -> str:
    # Fraction(repr(d)) has exactly the same sign and zero status as finite d.
    # Fraction is retained for the final probability, with no rounded p-values.
    le, ge = int(np.count_nonzero(values <= 0)), int(np.count_nonzero(values >= 0))
    return str(min(Fraction(1), Fraction(2 * (1 + min(le, ge)), len(values) + 1)))


def hanley_mcneil(auc: float, y: np.ndarray) -> tuple[float, float]:
    m, n = int(y.sum()), int(len(y) - y.sum())
    q1, q2 = auc / (2 - auc), 2 * auc * auc / (1 + auc)
    variance = (
        auc * (1 - auc) + (m - 1) * (q1 - auc * auc) + (n - 1) * (q2 - auc * auc)
    ) / (m * n)
    half = 1.959964 * math.sqrt(variance)
    return max(0.0, auc - half), min(1.0, auc + half)


def delong_p(a: np.ndarray, b: np.ndarray, y: np.ndarray) -> float:
    """Paired placement covariance, directly following S1, no library code."""
    placements_positive, placements_negative, aucs = [], [], []
    for s in (a, b):
        positive, negative = s[y == 1], s[y == 0]
        psi = (positive[:, None] > negative) + 0.5 * (positive[:, None] == negative)
        placements_positive.append(psi.mean(axis=1))
        placements_negative.append(psi.mean(axis=0))
        aucs.append(float(psi.mean()))
    m, n = int(y.sum()), int(len(y) - y.sum())
    if min(m, n) < 2:
        raise ValueError("DeLong requires at least two patients of each class")
    # Var(X-Y) equals Var(X)+Var(Y)-2Cov(X,Y); evaluate the
    # placement differences directly to avoid subtractive cancellation.
    variance = (
        np.var(np.subtract(*placements_positive), ddof=1) / m
        + np.var(np.subtract(*placements_negative), ddof=1) / n
    )
    difference = aucs[0] - aucs[1]
    if variance == 0:
        return 1.0 if difference == 0 else 0.0
    return math.erfc(abs(difference) / math.sqrt(2 * variance))


def self_test() -> None:
    """Hand-derived checks written independently, without project fixtures."""
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.8, 0.1])
    assert roc_auc(p, y) == 0.875
    assert abs(average_precision(p, y) - 5 / 6) < 1e-15
    s = selective(np.array([3, 2, 2, 1]), np.array([0, 1, 0, 1]))
    assert s["aurc"] == float(Fraction(7, 24))
    assert s["coverage_0.5"] == 0.75 and s["risk_0.5"] == 1 / 3
    assert (
        abs(ece(np.array([0.1, 0.2, 0.9, 1.0]), np.array([0, 1, 1, 1])) - 0.25) < 1e-15
    )
    assert brier(np.array([0.0, 0.5, 1.0]), np.array([0, 1, 1])) == 1 / 12
    assert bootstrap_p(np.array([-1.0, 0, 1.0])) == "1"
    assert bootstrap_p(np.array([1.0, 2, 3])) == "1/2"
    assert delong_p(p, p, y) == 1
    assert delong_p(y.astype(float), 1 - y.astype(float), y) == 0
    z = np.array([-1.0, -1.0, 1.0, 1.0])
    assert temperature(z, np.array([0, 0, 1, 1])) == 0.05
    assert temperature(z, np.array([1, 1, 0, 0])) == 20
    assert interval(np.array([0.0, 1.0])) == (0.025, 0.975)
    labels = np.array([1, 1, 0, 0])
    a, b = np.array([0.9, 0.4, 0.5, 0.1]), np.array([0.8, 0.7, 0.6, 0.2])
    assert abs(delong_p(a, b, labels) - math.erfc(0.5)) < 1e-15
    assert delong_p(a, b, labels) == delong_p(b, a, labels)
    assert average_precision(np.ones(4), labels) == 0.5
    assert (
        abs(temperature(np.ones(4), np.array([1, 1, 1, 0])) - 1 / math.log(3)) < 1e-14
    )


def compute(root: Path, output: Path, row_order: str) -> None:
    self_test()
    hashes, tables = {}, {}
    # Explicitly exclude macOS AppleDouble ._* metadata, not real parquet data.
    paths = sorted(p for p in root.rglob("*.parquet") if not p.name.startswith("._"))
    for path in paths:
        verified_bytes(path, hashes)
        df = pd.read_parquet(path, engine="pyarrow")
        if set(df.cohort) != {"utsw_calibration", "utsw_internal_test"}:
            raise ValueError(f"Unexpected cohort in {path}")
        tables[str(path.relative_to(root))] = df

    ids, labels = {}, {}

    def split(relative, cohort):
        df = tables[relative]
        part = df.loc[df.cohort == cohort].copy()
        if row_order == "patient_id":
            part = part.sort_values("patient_id")
        if (
            len(part) != 124
            or not part.patient_id.is_unique
            or int(part.label.sum()) != 35
        ):
            raise ValueError(f"Unexpected patient counts in {relative}, {cohort}")
        if not set(part.label).issubset({0, 1}):
            raise ValueError("Nonbinary labels")
        if not np.isfinite(part[["p_hat", "logit"]].to_numpy()).all():
            raise ValueError("Nonfinite predictions")
        if not part.p_hat.between(0, 1).all():
            raise ValueError("Probability outside [0, 1]")
        if cohort in ids:
            if (
                part.patient_id.tolist() != ids[cohort]
                or part.label.tolist() != labels[cohort]
            ):
                raise ValueError(f"Patient order or labels differ in {relative}")
        else:
            ids[cohort], labels[cohort] = part.patient_id.tolist(), part.label.tolist()
        return part

    draws = np.random.default_rng(0).integers(0, 124, size=(2000, 124))
    numbers, samples, run_data = {}, {}, {}

    def store(name, point, values):
        low, high = interval(values)
        numbers[name + ".point"] = float(point)
        numbers[name + ".lower"] = low
        numbers[name + ".upper"] = high
        samples[name] = np.asarray(values)

    y = None
    valid_draws = None
    for run in ("R2", "R7", "R8"):
        suffix = "conditions/full.parquet" if run == "R2" else "predictions.parquet"
        path = f"{RUNS[run]}/{suffix}"
        cal, test = split(path, "utsw_calibration"), split(path, "utsw_internal_test")
        z, y, p = (
            test.logit.to_numpy(dtype=float),
            test.label.to_numpy(dtype=int),
            test.p_hat.to_numpy(dtype=float),
        )
        t = temperature(cal.logit.to_numpy(dtype=float), cal.label.to_numpy(dtype=int))
        scaled = sigmoid(z / t)
        scores, losses = np.maximum(scaled, 1 - scaled), ((p > 0.5) != y).astype(int)
        run_data[run] = (z, p, scaled, scores, losses)
        numbers[f"{run}.temperature"] = t
        stats = {
            "auroc": [],
            "auprc": [],
            "M1.ece": [],
            "M2.ece": [],
            "M1.brier": [],
            "M2.brier": [],
        }
        stats.update({key: [] for key in selective(scores, losses)})
        valid_draws = []
        for row in draws:
            ys = y[row]
            valid = 0 < ys.sum() < len(ys)
            valid_draws.append(valid)
            if valid:
                stats["auroc"].append(roc_auc(p[row], ys))
                stats["auprc"].append(average_precision(p[row], ys))
            for key, value in selective(scores[row], losses[row]).items():
                stats[key].append(value)
            for mechanism, probs in [("M1", p), ("M2", scaled)]:
                stats[mechanism + ".ece"].append(ece(probs[row], ys))
                stats[mechanism + ".brier"].append(brier(probs[row], ys))
        store(run + ".auroc", roc_auc(p, y), np.array(stats["auroc"]))
        store(run + ".auprc", average_precision(p, y), np.array(stats["auprc"]))
        low, high = hanley_mcneil(roc_auc(p, y), y)
        numbers[run + ".auroc.hm_lower"], numbers[run + ".auroc.hm_upper"] = low, high
        for key, value in selective(scores, losses).items():
            if key.startswith("coverage_"):
                numbers[run + "." + key] = value
            else:
                store(run + "." + key, value, np.array(stats[key]))
        for mechanism, probs in [("M1", p), ("M2", scaled)]:
            for metric, function in [("ece", ece), ("brier", brier)]:
                key = mechanism + "." + metric
                store(run + "." + key, function(probs, y), np.array(stats[key]))

    def aurc_series(scores, loss):
        return selective(scores, loss)["aurc"], np.array(
            [selective(scores[row], loss[row])["aurc"] for row in draws]
        )

    def comparison(member, point, values, p_value=None):
        store(member, point, values)
        numbers[member + ".p_value"] = (
            bootstrap_p(values) if p_value is None else p_value
        )

    test = split(f"{RUNS['R2']}/conditions/full.parquet", "utsw_internal_test")
    mc_mean = np.array(
        [np.mean(np.asarray(v, dtype=float)) for v in test.mc_dropout_samples]
    )
    # x log x = 0 at endpoints, avoiding undefined 0*log(0).
    entropy_score = np.zeros(len(mc_mean))
    interior = (mc_mean > 0) & (mc_mean < 1)
    q = mc_mean[interior]
    entropy_score[interior] = q * np.log(q) + (1 - q) * np.log1p(-q)
    member_probs = []
    for run in ("R2", "R3", "R4", "R5", "R6"):
        part = split(f"{RUNS[run]}/conditions/full.parquet", "utsw_internal_test")
        member_probs.append(part.p_hat.to_numpy(dtype=float))
    ensemble = np.column_stack(member_probs)
    ensemble_score, ensemble_mean = -np.var(ensemble, axis=1), ensemble.mean(axis=1)
    m3_point, m3 = aurc_series(entropy_score, ((mc_mean > 0.5) != y).astype(int))
    m4_point, m4 = aurc_series(ensemble_score, ((ensemble_mean > 0.5) != y).astype(int))
    m5_point, m5 = numbers["R2.aurc.point"], samples["R2.aurc"]
    comparison("A1", m5_point - m3_point, m5 - m3)
    comparison("A2", m5_point - m4_point, m5 - m4)
    comparison("A3", m3_point - m4_point, m3 - m4)
    for i, condition in enumerate(CONDITIONS[1:], start=1):
        part = split(
            f"{RUNS['R2']}/conditions/{condition}.parquet", "utsw_internal_test"
        )
        probs = part.p_hat.to_numpy(dtype=float)
        scaled = sigmoid(part.logit.to_numpy(dtype=float) / numbers["R2.temperature"])
        point, values = aurc_series(
            np.maximum(scaled, 1 - scaled), ((probs > 0.5) != y).astype(int)
        )
        comparison(f"B{i}", point - m5_point, values - m5)
    for member, metric in [("D1", "ece"), ("D2", "brier")]:
        a, b = f"R2.M1.{metric}", f"R2.M2.{metric}"
        comparison(
            member,
            numbers[a + ".point"] - numbers[b + ".point"],
            samples[a] - samples[b],
        )
    for run, auc_member, aurc_member in [("R7", "E1", "E2"), ("R8", "E3", "E4")]:
        # Per-run AUROC uses stored raw probabilities; DeLong uses raw logits.
        za, zb = run_data[run][0], run_data["R2"][0]
        auc_values = np.array(
            [
                roc_auc(za[row], y[row]) - roc_auc(zb[row], y[row])
                for row, valid in zip(draws, valid_draws, strict=True)
                if valid
            ]
        )
        comparison(
            auc_member, roc_auc(za, y) - roc_auc(zb, y), auc_values, delong_p(za, zb, y)
        )
        comparison(
            aurc_member,
            numbers[run + ".aurc.point"] - m5_point,
            samples[run + ".aurc"] - m5,
        )
    if len(numbers) != 188:
        raise AssertionError(f"Expected 188 numbers, got {len(numbers)}")
    write_json(
        output,
        {
            "schema": "person_c_independent_codex.v1",
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "row_order": row_order,
            "n": 124,
            "n_positive": 35,
            "bootstrap_iterations": 2000,
            "bootstrap_matrix_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
            "valid_draws": int(sum(valid_draws)),
            "skipped_single_class_draws": int(2000 - sum(valid_draws)),
            "input_sha256": hashes,
            "numbers": numbers,
            "implementation_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "reading": {
                "R2_source": "conditions/full.parquet",
                "row_order": row_order,
                "AUPRC": "noninterpolated average precision; ties grouped",
                "M3_M4_losses": "classify MC/ensemble mean with p > 0.5",
                "temperature": "float64 inverse-T derivative bisection, 100 steps",
                "percentiles": "NumPy linear interpolation",
                "Hanley_McNeil": (
                    "Q1=A/(2-A), Q2=2*A*A/(1+A), clipped to [0,1], z=1.959964"
                ),
            },
        },
    )
    print(f"Wrote {len(numbers)} independent numbers to {output}; reference NOT read")


def compare(results: Path, reference: Path, output: Path) -> None:
    """Compare 188 saved scalars; no metric computation or reference-code read."""
    mine = json.loads(results.read_text())
    hashes = {}
    ref = json.loads(verified_bytes(reference, hashes))
    expected = {}

    def unpack(prefix, value):
        expected[prefix + ".point"] = value["point"]
        for side in ("lower", "upper"):
            expected[prefix + "." + side] = value["bootstrap_95_interval"][side]

    for run, data in ref["runs"].items():
        expected[run + ".temperature"] = data["temperature"]
        for name, key in [
            ("auroc", "auroc"),
            ("auprc", "auprc"),
            ("aurc", "aurc_mean_over_cutoffs"),
        ]:
            unpack(run + "." + name, data[key])
        for side in ("lower", "upper"):
            expected[run + ".auroc.hm_" + side] = data["auroc"][
                "hanley_mcneil_95_interval"
            ][side]
        for grid, value in data["selective_risk_at_coverage"].items():
            unpack(run + ".risk_" + grid, value)
            expected[run + ".coverage_" + grid] = value["attained_coverage"]
        for mechanism, value in data["calibration"].items():
            for metric in ("ece", "brier"):
                unpack(run + "." + mechanism + "." + metric, value[metric])
    for member, value in ref["confirmatory"].items():
        for field in ("point", "lower", "upper", "p_value"):
            expected[member + "." + field] = value[field]
    if set(expected) != set(mine["numbers"]) or len(expected) != 188:
        raise ValueError("Comparison key sets must match all 188 numbers")
    rows = []
    for key, value in mine["numbers"].items():
        reference_value = expected[key]
        calibration = any(t in key for t in ("temperature", ".ece.", ".brier."))
        tolerance = 1e-6 if calibration or key.startswith(("D1.", "D2.")) else 1e-9
        if isinstance(value, str):
            difference = Fraction(value) - Fraction(reference_value)
            agrees = difference == 0
            difference, rule = str(difference), "exact fraction"
        else:
            difference = value - reference_value
            agrees, rule = abs(difference) <= tolerance, tolerance
        row = dict(
            number=key,
            mine=value,
            reference=reference_value,
            difference=difference,
            tolerance=rule,
            agrees=agrees,
        )
        rows.append(row)
        if not agrees:
            print("FAIL", key, value, reference_value, difference)
    agreeing = sum(row["agrees"] for row in rows)
    write_json(
        output,
        {
            "results_sha256": hashlib.sha256(results.read_bytes()).hexdigest(),
            "reference_sha256": hashes[str(reference)],
            "agreeing": agreeing,
            "total": len(rows),
            "comparison": rows,
        },
    )
    print(f"Agreement: {agreeing}/{len(rows)}; comparison saved to {output}")
    if agreeing != len(rows):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--row-order", choices=["patient_id", "file"], default="patient_id"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--compare-results", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--comparison-output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Independent hand-derived checks passed")
    elif args.compare_results is not None:
        if args.reference is None or args.comparison_output is None:
            parser.error("Comparison requires --reference and --comparison-output")
        compare(args.compare_results, args.reference, args.comparison_output)
    else:
        if args.reference is not None:
            parser.error("Compute mode must not receive a reference")
        if args.results_root is None or args.output is None:
            parser.error("--results-root and --output are required")
        compute(args.results_root, args.output, args.row_order)


if __name__ == "__main__":
    main()
