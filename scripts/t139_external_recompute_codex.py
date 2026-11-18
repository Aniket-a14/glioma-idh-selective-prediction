#!/usr/bin/env python3
"""T13.9 independent agent recomputation; compute never reads author results.

Third-party dependencies: numpy and pandas/pyarrow only. All outputs use exclusive
creation. D-001: degraded solo fallback, a second agent, not a second human.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Volumes/Research_2/artifacts/experiments")
EXTERNAL = ROOT / "external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_20261118"
ABLATION = ROOT / "external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_r7r8_20261118"
INTERNAL = ROOT / "01M46999FB083AX4WW0067YM13"
CONDITIONS = [
    "full",
    "drop_t1",
    "drop_t1ce",
    "drop_t2",
    "drop_flair",
    "t1ce_flair_only",
]
GRID = [0.5, 0.6, 0.7, 0.8, 0.9]
ALPHAS = [0.05, 0.1, 0.2]
B = 2000
P = 10000
RULES = {
    "C3": (
        "D-035: refuted if any D(phi) >= 0; supported if all upper 95% "
        "limits < 0; otherwise inconclusive at this n. Full primary; "
        "missing conditions secondary; worst across conditions also "
        "reported."
    ),
    "C4": (
        "D-004, D-045, D-050, D-058: supported iff every two-stage "
        "coverage-deviation interval half-width <= .07; otherwise refuted. "
        "Preserved iff interval inside +/- band; degraded iff wholly below "
        "-band or above +band; otherwise indeterminate. Also report .05 "
        "band. D-058 permits negative calibration findings, no refit."
    ),
    "C5": (
        "D-035, D-050: adjacent difference = risk at lower coverage minus "
        "risk at higher coverage. Refuted if any lower 95% limit > 0; "
        "supported if all point differences <= 0; otherwise inconclusive "
        "at this n. Bootstrap intervals, not permutation inference."
    ),
    "C6": (
        "D-035, D-050: rejected error rate minus overall error rate. "
        "Refuted if any observed difference <= 0; supported if every "
        "one-sided permutation p, BH-adjusted across five coverages, < "
        ".05; otherwise inconclusive at this n. Permutation "
        "p=(1+count)/(10000+1)."
    ),
    "loss": (
        "D-059: M1/M2/M3/M5 use deterministic R2 errors; M4 uses "
        "ensemble-mean errors. Threshold >= .5 per updated metric "
        "contract. M6 uses its own classifier."
    ),
    "family": (
        "D-052, D-060: 15 external members plus 14 UTSW members, one "
        "pooled BH pass at q=.05 in compare only. Block C independent "
        "cohorts; R7/R8 from supplementary frozen run."
    ),
}


def verified(path, hashes):
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = Path(str(path) + ".sha256")
    if sidecar.exists() and sidecar.read_text().split()[0] != digest:
        raise ValueError(f"SHA-256 mismatch: {path}")
    hashes[str(path)] = {"sha256": digest, "sidecar_verified": sidecar.exists()}
    return payload


def exclusive_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def sigmoid(z):
    return np.exp(-np.logaddexp(0.0, -z))


def temperature(z, y):
    lo, hi = 0.05, 20.0  # inverse temperature has the same numerical bounds

    def derivative(w):
        return np.mean(z * (sigmoid(w * z) - y))

    if derivative(lo) >= 0:
        return 20.0
    if derivative(hi) <= 0:
        return 0.05
    for _ in range(100):
        mid = (lo + hi) / 2
        if derivative(mid) < 0:
            lo = mid
        else:
            hi = mid
    return 2 / (lo + hi)


def auc(p, y):
    a, b = p[y == 1], p[y == 0]
    if not len(a) or not len(b):
        return np.nan
    return float(np.mean((a[:, None] > b) + 0.5 * (a[:, None] == b)))


def auprc(p, y):
    order = np.argsort(-p, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(p[order]) != 0) + 1, len(y)]
    tp = np.cumsum(y[order])[ends - 1]
    return float(np.sum(np.diff(np.r_[0, tp]) * tp / ends) / y.sum())


def ece(p, y):
    bins = np.array([min(int(Fraction(repr(float(v))) * 10), 9) for v in p])
    return float(np.abs(np.bincount(bins, weights=p - y, minlength=10)).sum() / len(y))


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def rc(scores, loss):
    order = np.argsort(-scores, kind="stable")
    s = scores[order]
    ends = np.r_[np.flatnonzero(np.diff(s) != 0) + 1, len(s)]
    errors = np.cumsum(loss[order], dtype=np.int64)[ends - 1]
    risks = errors / ends
    widths = np.diff(np.r_[0, ends])
    return ends, risks, widths


def selective(scores, loss):
    ends, risks, widths = rc(scores, loss)
    out = {
        "aurc_mean_over_cutoffs": float(np.dot(widths, risks) / len(loss)),
        "aurc_trapezoid": float(
            np.sum(np.diff(ends / len(loss)) * (risks[1:] + risks[:-1]) / 2)
        ),
    }
    for phi in GRID:
        f = Fraction(str(phi))
        i = np.flatnonzero(ends * f.denominator >= len(loss) * f.numerator)[0]
        out[f"risk_{phi}"] = float(risks[i])
        out[f"coverage_{phi}"] = float(ends[i] / len(loss))
    return out


def ci(v):
    v = np.asarray(v)
    v = v[np.isfinite(v)]
    if not len(v):
        raise ValueError("No valid bootstrap draws")
    lo, hi = np.quantile(v, [0.025, 0.975], method="linear")
    return {"lower": float(lo), "upper": float(hi)}


def boot_p(v):
    return str(
        min(
            Fraction(1),
            Fraction(
                2 * (1 + min(int(np.sum(v <= 0)), int(np.sum(v >= 0)))), len(v) + 1
            ),
        )
    )


def summary(point, values, p=False):
    out = {"point": float(point), **ci(values)}
    if p:
        out["p_value"] = boot_p(np.asarray(values))
    return out


def bh(pvalues):
    vals = [Fraction(str(p)) for p in pvalues]
    order = sorted(range(len(vals)), key=vals.__getitem__)
    adjusted = [Fraction(1)] * len(vals)
    running = Fraction(1)
    for rank in range(len(vals), 0, -1):
        i = order[rank - 1]
        running = min(running, vals[i] * len(vals) / rank)
        adjusted[i] = running
    return [str(v) for v in adjusted]


def hm(a, y):
    m, n = int(y.sum()), int(len(y) - y.sum())
    v = (
        a * (1 - a)
        + (m - 1) * (a / (2 - a) - a * a)
        + (n - 1) * (2 * a * a / (1 + a) - a * a)
    ) / (m * n)
    h = 1.959964 * math.sqrt(v)
    return {"lower": max(0.0, a - h), "upper": min(1.0, a + h)}


def delong(a, b, y):
    pos, neg, av = [], [], []
    for s in (a, b):
        x, z = s[y == 1], s[y == 0]
        v = (x[:, None] > z) + 0.5 * (x[:, None] == z)
        pos.append(v.mean(axis=1))
        neg.append(v.mean(axis=0))
        av.append(float(v.mean()))
    variance = float(
        np.var(pos[0] - pos[1], ddof=1) / len(pos[0])
        + np.var(neg[0] - neg[1], ddof=1) / len(neg[0])
    )
    d = av[0] - av[1]
    p = math.erfc(abs(d) / math.sqrt(2 * variance)) if variance else float(d == 0)
    return {"difference": d, "variance": variance, "p_value": p}


def nonconformity(p, y):
    return np.array(
        [
            float(1 - Fraction(repr(float(v)))) if label else float(v)
            for v, label in zip(p, y, strict=True)
        ]
    )


def quantile(scores, alpha):
    rank = math.ceil((len(scores) + 1) * (1 - Fraction(str(alpha))))
    return float(np.sort(scores)[rank - 1]) if rank <= len(scores) else math.inf


def sets(p, y, q):
    zero = p <= q
    one = nonconformity(p, np.ones(len(y), dtype=int)) <= q
    sizes = zero.astype(int) + one.astype(int)
    covered = np.where(y == 1, one, zero)
    return sizes, covered


def worst(statuses):
    return max(
        statuses,
        key={"supported": 0, "inconclusive at this n": 1, "refuted": 2}.__getitem__,
    )


def self_check():
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.8, 0.1])
    assert auc(p, y) == 0.875
    assert abs(auprc(p, y) - 5 / 6) < 1e-15
    v = selective(np.array([3, 2, 2, 1]), np.array([0, 1, 0, 1]))
    assert abs(v["aurc_mean_over_cutoffs"] - 7 / 24) < 1e-15
    assert v["coverage_0.5"] == 0.75 and v["risk_0.5"] == 1 / 3
    assert quantile(np.arange(9.0), 0.7) == 2.0
    assert boot_p(np.array([1.0, 2, 3])) == "1/2"
    assert bh(["1/100", "1/25", "1/5"]) == ["3/100", "3/50", "1/5"]
    assert delong(p, p, y)["p_value"] == 1.0
    assert temperature(np.ones(4), np.array([1, 1, 1, 0])) - 1 / math.log(3) < 1e-14


def compute(output):
    self_check()
    if output.exists():
        raise FileExistsError(output)
    hashes = {}
    ext_ids = None
    ext_labels = None

    def read(path, cohort):
        nonlocal ext_ids, ext_labels
        verified(path, hashes)
        frame = pd.read_parquet(path, engine="pyarrow")
        if cohort is not None:
            frame = frame.loc[frame.cohort == cohort]
        frame = frame.sort_values("patient_id").reset_index(drop=True)
        if not frame.patient_id.is_unique or not set(frame.label).issubset({0, 1}):
            raise ValueError("Invalid patient units/labels")
        if (
            not np.isfinite(frame[["p_hat", "logit"]].to_numpy()).all()
            or not frame.p_hat.between(0, 1).all()
        ):
            raise ValueError("Invalid probabilities/logits")
        if cohort == "ucsf_pdgm":
            if len(frame) != 202:
                raise ValueError("External cohort size")
            ids, labels = frame.patient_id.tolist(), frame.label.tolist()
            if ext_ids is None:
                ext_ids, ext_labels = ids, labels
            elif ids != ext_ids or labels != ext_labels:
                raise ValueError("Patient alignment/label disagreement")
        return frame

    cal = read(INTERNAL / "conditions/full.parquet", "utsw_calibration")
    baseline = read(INTERNAL / "predictions.parquet", "utsw_calibration")
    if not np.array_equal(cal.patient_id, baseline.patient_id) or not np.array_equal(
        cal.label, baseline.label
    ):
        raise ValueError("Full-input calibration patient units differ")
    t = temperature(cal.logit.to_numpy(float), cal.label.to_numpy(int))
    cal_scores = nonconformity(
        sigmoid(cal.logit.to_numpy(float) / t), cal.label.to_numpy(int)
    )
    qs = {str(a): quantile(cal_scores, a) for a in ALPHAS}
    # One paired matrix across every condition/mechanism on UCSF.
    draws = np.random.default_rng(0).integers(0, 202, size=(B, 202))
    # Two-stage pairs: independent successive RNG draws, shared across conditions.
    rng = np.random.default_rng(0)
    cal_draws = rng.integers(0, len(cal), size=(B, len(cal)))
    c4_draws = rng.integers(0, 202, size=(B, 202))
    q_draws = {
        str(a): np.sort(cal_scores[cal_draws], axis=1)[
            :, math.ceil((len(cal) + 1) * (1 - Fraction(str(a)))) - 1
        ]
        for a in ALPHAS
    }
    results, series, points, run_data = {}, {}, {}, {}
    for condition in CONDITIONS:
        frame = read(EXTERNAL / "primary_seed0" / f"{condition}.parquet", "ucsf_pdgm")
        p, z, y = (
            frame.p_hat.to_numpy(float),
            frame.logit.to_numpy(float),
            frame.label.to_numpy(int),
        )
        scaled = sigmoid(z / t)
        loss = ((p >= 0.5) != y).astype(int)
        mc = np.stack(frame.mc_dropout_samples).astype(float)
        if mc.shape != (202, 30):
            raise ValueError("MC passes not 30")
        q = mc.mean(axis=1)
        entropy = np.zeros(len(q))
        mask = (q > 0) & (q < 1)
        entropy[mask] = q[mask] * np.log(q[mask]) + (1 - q[mask]) * np.log1p(-q[mask])
        probs = [p]
        for seed in range(1, 5):
            other = read(
                EXTERNAL / f"ensemble_seed{seed}" / f"{condition}.parquet", "ucsf_pdgm"
            )
            probs.append(other.p_hat.to_numpy(float))
        ensemble = np.column_stack(probs)
        comparator = read(
            EXTERNAL / "m6_comparator_r1" / f"{condition}.parquet", "ucsf_pdgm"
        )
        pc = comparator.p_hat.to_numpy(float)
        scores = {
            "M1": np.maximum(p, 1 - p),
            "M2": np.maximum(scaled, 1 - scaled),
            "M3": entropy,
            "M4": -ensemble.var(axis=1),
            "M5": np.maximum(scaled, 1 - scaled),
            "M6": np.maximum(pc, 1 - pc),
        }
        losses = {m: loss for m in scores}
        losses["M4"] = ((ensemble.mean(axis=1) >= 0.5) != y).astype(int)
        losses["M6"] = ((pc >= 0.5) != y).astype(int)
        result = {
            "n": len(y),
            "n_positive": int(y.sum()),
            "n_errors": int(loss.sum()),
            "always_predict_risk": float(loss.mean()),
            "auroc": auc(p, y),
            "auprc": auprc(p, y),
            "calibration": {},
            "mechanisms": {},
            "conformal": {},
        }
        for m, v in [("M1", p), ("M2", scaled)]:
            result["calibration"][m] = {"ece": ece(v, y), "brier": brier(v, y)}
        per = {}
        for m in scores:
            point = selective(scores[m], losses[m])
            vals = {key: [] for key in point}
            for row in draws:
                for key, value in selective(scores[m][row], losses[m][row]).items():
                    vals[key].append(value)
            vals = {key: np.asarray(v) for key, v in vals.items()}
            per[m] = vals
            always = losses[m][draws].mean(axis=1)
            result["mechanisms"][m] = {
                key: (
                    value if key.startswith("coverage") else summary(value, vals[key])
                )
                for key, value in point.items()
            }
            result["mechanisms"][m]["always_predict_risk"] = float(losses[m].mean())
            result["mechanisms"][m]["n_errors"] = int(losses[m].sum())
            for phi in GRID:
                key = f"D_{phi}"
                result["mechanisms"][m][key] = summary(
                    point[f"risk_{phi}"] - losses[m].mean(),
                    vals[f"risk_{phi}"] - always,
                )
            points[condition, m] = point["aurc_mean_over_cutoffs"]
            series[condition, m] = vals["aurc_mean_over_cutoffs"]
        result["oracle_aurc"] = selective(-loss, loss)["aurc_mean_over_cutoffs"]
        result["c5_adjacent"] = {}
        c5p = []
        for low, high in zip(GRID[:-1], GRID[1:], strict=True):
            key = f"{low}-{high}"
            a = (
                result["mechanisms"]["M5"][f"risk_{low}"]["point"]
                - result["mechanisms"]["M5"][f"risk_{high}"]["point"]
            )
            v = per["M5"][f"risk_{low}"] - per["M5"][f"risk_{high}"]
            result["c5_adjacent"][key] = summary(a, v, True)
            c5p.append(boot_p(v))
        for cell, adj in zip(result["c5_adjacent"].values(), bh(c5p), strict=True):
            cell["p_adjusted"] = adj
        # Permute integer losses across the fixed confidence ranking; do not
        # permute scores or redraw the cohort. Same seed-0 schedule each condition.
        perm_rng = np.random.default_rng(0)
        permuted = np.array([perm_rng.permutation(loss) for _ in range(P)])
        result["c6_enrichment"] = {}
        c6p = []
        order = np.argsort(-scores["M5"], kind="stable")
        for phi in GRID:
            k = round(result["mechanisms"]["M5"][f"coverage_{phi}"] * len(y))
            rejected = order[k:]
            observed = int(loss[rejected].sum())
            count = int(np.sum(permuted[:, rejected].sum(axis=1) >= observed))
            pv = str(Fraction(1 + count, P + 1))
            c6p.append(pv)
            result["c6_enrichment"][str(phi)] = {
                "observed": float(loss[rejected].mean() - loss.mean()),
                "p_value": pv,
                "n_rejected": len(rejected),
                "rejected_but_correct_rate": float(1 - loss[rejected].mean()),
            }
        for cell, adj in zip(result["c6_enrichment"].values(), bh(c6p), strict=True):
            cell["p_adjusted"] = adj
        for a in ALPHAS:
            key = str(a)
            sizes, covered = sets(scaled, y, qs[key])
            deviations = []
            for i, row in enumerate(c4_draws):
                _, cov = sets(scaled[row], y[row], q_draws[key][i])
                deviations.append(cov.mean() - (1 - a))
            dev = summary(covered.mean() - (1 - a), deviations)
            dev["half_width"] = (dev["upper"] - dev["lower"]) / 2
            labels = {}
            for band in [0.07, 0.05]:
                labels[str(band)] = (
                    "preserved"
                    if dev["lower"] >= -band and dev["upper"] <= band
                    else "degraded"
                    if dev["upper"] < -band or dev["lower"] > band
                    else "indeterminate"
                )
            singleton = sizes == 1
            result["conformal"][key] = {
                "quantile": qs[key],
                "coverage": float(covered.mean()),
                "abstention_rate": float(np.mean(~singleton)),
                "empty_count": int(np.sum(sizes == 0)),
                "full_count": int(np.sum(sizes == 2)),
                "singleton_count": int(singleton.sum()),
                "singleton_true_label_fraction": float(covered[singleton].mean())
                if singleton.any()
                else None,
                "deviation": dev,
                "coverage_labels": labels,
            }
        d = [result["mechanisms"]["M5"][f"D_{phi}"] for phi in GRID]
        c5 = list(result["c5_adjacent"].values())
        c6 = list(result["c6_enrichment"].values())
        result["claims"] = {
            "C3": "refuted"
            if any(v["point"] >= 0 for v in d)
            else "supported"
            if all(v["upper"] < 0 for v in d)
            else "inconclusive at this n",
            "C4": "refuted"
            if any(
                v["deviation"]["half_width"] > 0.07
                for v in result["conformal"].values()
            )
            else "supported",
            "C5": "refuted"
            if any(v["lower"] > 0 for v in c5)
            else "supported"
            if all(v["point"] <= 0 for v in c5)
            else "inconclusive at this n",
            "C6": "refuted"
            if any(v["observed"] <= 0 for v in c6)
            else "supported"
            if all(Fraction(v["p_adjusted"]) < Fraction(1, 20) for v in c6)
            else "inconclusive at this n",
        }
        if condition == "full":
            av = np.array([auc(p[row], y[row]) for row in draws])
            result["auroc_bootstrap_95_interval"] = ci(av)
            result["auroc_hanley_mcneil_95_interval"] = hm(result["auroc"], y)
            result["auroc_valid_draws"] = int(np.isfinite(av).sum())
            run_data["R2"] = (p, z, y, scores["M5"], loss)
        results[condition] = result
        print(f"Computed {condition}: aggregate results only", flush=True)
    family = {}

    def difference(member, ca, ma, cb, mb):
        family[member] = summary(
            points[ca, ma] - points[cb, mb], series[ca, ma] - series[cb, mb], True
        )

    for member, ma, mb in [("A1", "M5", "M3"), ("A2", "M5", "M4"), ("A3", "M3", "M4")]:
        difference(member, "full", ma, "full", mb)
    for i, c in enumerate(CONDITIONS[1:], 1):
        difference(f"B{i}", c, "M5", "full", "M5")
    # Unpaired external/internal: two successive independent matrices from seed 0.
    internal = read(INTERNAL / "conditions/full.parquet", "utsw_internal_test")
    ip, iy = internal.p_hat.to_numpy(float), internal.label.to_numpy(int)
    isc = np.maximum(ip, 1 - ip)
    iloss = ((ip >= 0.5) != iy).astype(int)
    rng = np.random.default_rng(0)
    ed = rng.integers(0, 202, size=(B, 202))
    ids = rng.integers(0, len(iy), size=(B, len(iy)))
    internal_values = np.array(
        [selective(isc[r], iloss[r])["aurc_mean_over_cutoffs"] for r in ids]
    )
    assert np.array_equal(ed, draws)
    family["C1"] = summary(
        points["full", "M5"] - selective(isc, iloss)["aurc_mean_over_cutoffs"],
        series["full", "M5"] - internal_values,
        True,
    )
    p, z, y, score, loss = run_data["R2"]
    for member, fn in [("D1", ece), ("D2", brier)]:
        scaled = sigmoid(z / t)
        values = np.array([fn(p[r], y[r]) - fn(scaled[r], y[r]) for r in draws])
        family[member] = summary(fn(p, y) - fn(scaled, y), values, True)
    ablations = {}
    for run, role, auc_id, aurc_id in [
        ("R7", "ablation_r7_whole_brain", "E1", "E2"),
        ("R8", "ablation_r8_two_stage", "E3", "E4"),
    ]:
        f = read(ABLATION / role / "full.parquet", "ucsf_pdgm")
        ap, az = f.p_hat.to_numpy(float), f.logit.to_numpy(float)
        asc = np.maximum(ap, 1 - ap)
        aloss = ((ap >= 0.5) != y).astype(int)
        values = np.array(
            [selective(asc[r], aloss[r])["aurc_mean_over_cutoffs"] for r in draws]
        )
        point = selective(asc, aloss)["aurc_mean_over_cutoffs"]
        comparison = delong(az, z, y)
        auc_values = np.array([auc(az[r], y[r]) - auc(z[r], y[r]) for r in draws])
        family[auc_id] = {
            **summary(comparison["difference"], auc_values),
            "p_value": comparison["p_value"],
        }
        family[aurc_id] = summary(
            point - points["full", "M5"], values - series["full", "M5"], True
        )
        ablations[run] = {
            "n": len(y),
            "auroc": auc(ap, y),
            "auprc": auprc(ap, y),
            "aurc_mean_over_cutoffs": point,
            "ece": ece(ap, y),
            "brier": brier(ap, y),
            "coverage": 1.0,
            "delong_vs_R2": comparison,
            "aurc_vs_R2": family[aurc_id],
        }
    ablations["R2"] = {
        "n": len(y),
        "auroc": auc(p, y),
        "auprc": auprc(p, y),
        "aurc_mean_over_cutoffs": points["full", "M5"],
        "ece": ece(p, y),
        "brier": brier(p, y),
        "coverage": 1.0,
    }
    assert len(family) == 15
    result = {
        "schema": "t139_external_codex.v1",
        "executor": "D-001 degraded solo fallback: second agent, not second human",
        "input_sha256": hashes,
        "implementation_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "resampling": {
            "bootstrap_iterations": B,
            "permutations": P,
            "seed": 0,
            "row_order": "patient_id ascending",
            "paired": "default_rng(0).integers(0,202,(2000,202)), reused everywhere",
            "C4": (
                "default_rng(0), calibration matrix first then independent "
                "external matrix; fixed fitted temperature, refit quantiles only"
            ),
            "C6": (
                "default_rng(0), 10000 permutation(loss) vectors per condition, "
                "shared over grid; reset per condition"
            ),
            "unpaired_C": (
                "default_rng(0), external matrix first then independent UTSW matrix"
            ),
            "author_seed_index_match": (
                "Unknown until compare; only S4 internal seed scheme explicitly "
                "fixed in permitted contracts"
            ),
            "draw_matrix_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
        },
        "conventions": {
            "AUPRC": "noninterpolated average precision, ties grouped",
            "Hanley_McNeil_z": 1.959964,
            "M6_AURC": "confidence-ranked diagnostic; M6 is deployed always-predict",
            "float_computation": (
                "float64 sums; tie-block decisions exact; rational p-values and BH "
                "exact"
            ),
        },
        "rules": RULES,
        "temperature": t,
        "calibration_source": {
            "selected": "conditions/full.parquet",
            "reason": (
                "Full-input condition sweep; independently derived T and quantiles "
                "agree with freeze_spec within its temperature fitting tolerance. "
                "predictions.parquet has small numerical inference differences."
            ),
            "base_predictions_max_logit_difference": float(
                np.max(np.abs(cal.logit.to_numpy() - baseline.logit.to_numpy()))
            ),
            "base_predictions_temperature": temperature(
                baseline.logit.to_numpy(float), baseline.label.to_numpy(int)
            ),
        },
        "calibration_n": len(cal),
        "quantiles": qs,
        "calibration_coverage": {
            str(a): float(
                sets(
                    sigmoid(cal.logit.to_numpy(float) / t),
                    cal.label.to_numpy(int),
                    qs[str(a)],
                )[1].mean()
            )
            for a in ALPHAS
        },
        "conditions": results,
        "ablations": ablations,
        "external_family": family,
        "supplementary_external_only_bh": dict(
            zip(family, bh([v["p_value"] for v in family.values()]), strict=True)
        ),
        "pooled_BH": (
            "Deferred until compare: author UTSW raw p-values have not been "
            "read; external-only BH is supplementary, not the registered "
            "family."
        ),
        "overall_claims": {
            claim: worst([r["claims"][claim] for r in results.values()])
            for claim in ["C3", "C4", "C5", "C6"]
        },
    }
    exclusive_json(output, result)
    print(
        f"Wrote blinded aggregate results: {output}; author results not read",
        flush=True,
    )


def compare(mine_path, reference_dir, internal10, report):
    """Compare saved aggregates only; never replace or recompute mine's results."""
    if report.exists():
        raise FileExistsError(report)
    hashes = {}
    mine = json.loads(mine_path.read_text())
    r9 = json.loads(verified(reference_dir / "phase09_external_analysis.json", hashes))
    r10 = json.loads(verified(reference_dir / "phase10_external_analysis.json", hashes))
    i10 = json.loads(verified(internal10, hashes))
    expected, kinds = {}, {}

    def put(path, value, kind="point"):
        expected[tuple(path)] = value
        kinds[tuple(path)] = kind

    def interval(path, value):
        for side in ("lower", "upper"):
            put([*path, side], value[side], "interval")

    put(["temperature"], r9["provenance"]["full_temperature"])
    # UTSW n is in the pre-existing internal run's aggregate table.
    # Its test n is not substituted for calibration n; the latter is checked
    # against each conformal calibration coverage, not inferred from test size.
    for a in ALPHAS:
        key = str(a)
        cell = r9["conformal"]["full"]["carried_over"][key]
        put(["quantiles", key], cell["quantile"])
        put(["calibration_coverage", key], cell["calibration_empirical_coverage"])
    for condition in CONDITIONS:
        base = ["conditions", condition]
        ref = r9["conditions"][condition]
        for name in ("n", "n_errors", "always_predict_risk", "oracle_aurc"):
            put([*base, name], ref["M5"][name])
        for mechanism in ("M1", "M2", "M3", "M4", "M5", "M6"):
            path = [*base, "mechanisms", mechanism]
            cell = ref[mechanism]
            for name in ("n_errors", "always_predict_risk"):
                put([*path, name], cell[name])
            put(
                [*path, "aurc_mean_over_cutoffs", "point"],
                cell["aurc_mean_over_cutoffs"],
            )
            interval(
                [*path, "aurc_mean_over_cutoffs"], cell["aurc_bootstrap_95_interval"]
            )
            put([*path, "aurc_trapezoid", "point"], cell["aurc_trapezoid"])
            for phi in GRID:
                g = str(phi)
                value = cell["selective_risk_at_coverage"][g]
                put([*path, f"coverage_{phi}"], value["attained_coverage"])
                put([*path, f"risk_{phi}", "point"], value["risk"])
                interval([*path, f"risk_{phi}"], value["risk_95_interval"])
                for field in ("point", "lower", "upper"):
                    put(
                        [*path, f"D_{phi}", field],
                        value["D_phi"][field],
                        "interval" if field != "point" else "point",
                    )
        # The author's adjacent array follows its descending coverage grid.
        for i, (lo, hi) in enumerate(zip(GRID[:-1], GRID[1:], strict=True)):
            cell = ref["M5"]["adjacent_grid_risk_differences"][3 - i]
            for field in ("point", "lower", "upper"):
                put(
                    [*base, "c5_adjacent", f"{lo}-{hi}", field],
                    cell[field],
                    "interval" if field != "point" else "point",
                )
        for phi in GRID:
            g = str(phi)
            cell = ref["M5"]["enrichment"][g]
            path = [*base, "c6_enrichment", g]
            put([*path, "observed"], cell["observed_difference"])
            put([*path, "n_rejected"], cell["n_rejected"])
            put([*path, "p_value"], cell["p_value"], "exact")
            put([*path, "p_adjusted"], cell["adjusted_p_value"], "exact")
            put(
                [*path, "rejected_but_correct_rate"],
                ref["M5"]["selective_risk_at_coverage"][g]["rejected_but_correct_rate"],
            )
        for alpha in ALPHAS:
            a = str(alpha)
            cell = r9["conformal"][condition]["carried_over"][a]
            path = [*base, "conformal", a]
            for name, key in [
                ("coverage", "empirical_coverage"),
                ("abstention_rate", "abstention_rate"),
                ("empty_count", "empty_count"),
                ("full_count", "full_count"),
                ("singleton_count", "singleton_count"),
                ("singleton_true_label_fraction", "singleton_true_label_fraction"),
                ("quantile", "quantile"),
            ]:
                put([*path, name], cell[key])
            put([*path, "deviation", "point"], cell["empirical_coverage"] - (1 - alpha))
            interval([*path, "deviation"], cell["coverage_deviation_bootstrap"])
            put(
                [*path, "deviation", "half_width"],
                cell["coverage_deviation_bootstrap"]["half_width"],
                "interval",
            )
        if condition == "full":
            run = r10["runs"]["R2"]
            for name in ("auroc", "auprc"):
                put([*base, name], run[name]["point"])
            for mechanism in ("M1", "M2"):
                for metric in ("ece", "brier"):
                    put(
                        [*base, "calibration", mechanism, metric],
                        run["calibration"][mechanism][metric]["point"],
                    )
            interval(
                [*base, "auroc_bootstrap_95_interval"],
                run["auroc"]["bootstrap_95_interval"],
            )
            interval(
                [*base, "auroc_hanley_mcneil_95_interval"],
                run["auroc"]["hanley_mcneil_95_interval"],
            )
            put(
                [*base, "auroc_valid_draws"],
                run["auroc"]["bootstrap_95_interval"]["valid_draws"],
            )
    for run, cell in r10["runs"].items():
        base = ["ablations", run]
        for name in ("n", "coverage"):
            put([*base, name], cell[name])
        for name in ("auroc", "auprc", "aurc_mean_over_cutoffs"):
            put([*base, name], cell[name]["point"])
        for name in ("ece", "brier"):
            put([*base, name], cell["calibration"]["M1"][name]["point"])
        if run != "R2":
            auc_id, aurc_id = ("E1", "E2") if run == "R7" else ("E3", "E4")
            put(
                [*base, "delong_vs_R2", "difference"],
                r10["confirmatory"][auc_id]["point"],
            )
            put(
                [*base, "delong_vs_R2", "p_value"],
                r10["confirmatory"][auc_id]["p_value"],
            )
            for field in ("point", "lower", "upper", "p_value"):
                put(
                    [*base, "aurc_vs_R2", field],
                    r10["confirmatory"][aurc_id][field],
                    "interval"
                    if field in ("lower", "upper")
                    else "exact"
                    if field == "p_value"
                    else "point",
                )
    assert len(i10["confirmatory"]) == 14
    assert len(r10["confirmatory"]) == len(mine["external_family"]) == 15
    for member, cell in r10["confirmatory"].items():
        for field in ("point", "lower", "upper", "p_value"):
            put(
                ["external_family", member, field],
                cell[field],
                "interval"
                if field in ("lower", "upper")
                else "exact"
                if field == "p_value" and isinstance(cell[field], str)
                else "point",
            )

    def flatten(value, prefix=()):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from flatten(item, (*prefix, key))
        elif isinstance(value, int | float) or (
            isinstance(value, str) and ("/" in value or value == "1")
        ):
            yield prefix, value

    numerical = {}
    for key in (
        "temperature",
        "calibration_n",
        "quantiles",
        "calibration_coverage",
        "conditions",
        "ablations",
        "external_family",
    ):
        numerical.update(flatten(mine[key], (key,)))
    rows, missing = [], []
    for path, value in numerical.items():
        if path not in expected:
            missing.append((".".join(path), value))
            continue
        reference = expected[path]
        kind = kinds[path]
        if kind == "exact":
            difference = Fraction(str(value)) - Fraction(str(reference))
            ok = difference == 0
            display_diff = str(difference)
        else:
            difference = float(value) - float(reference)
            ok = abs(difference) <= (0.01 if kind == "interval" else 1e-9)
            display_diff = repr(difference)
        cause = ""
        if not ok:
            if "c6_enrichment" in path:
                cause = "C6_MC_OR_ENCODING"
            elif "conformal" in path:
                cause = "C4_MC"
            elif path == ("temperature",):
                cause = "TEMPERATURE_SOLVER"
            elif path[-1] == "oracle_aurc":
                cause = "OWN_ORACLE_TIES"
            elif path[:2] == ("external_family", "C1"):
                cause = "UNPAIRED_STREAMS"
            else:
                cause = "UNRESOLVED_STOP"
        rows.append((".".join(path), value, reference, display_diff, ok, kind, cause))
    # One registered 29-member family, pooled only now. Internal p-values are
    # borrowed explicitly, never presented as independently recomputed here.
    names = [f"utsw:{k}" for k in i10["confirmatory"]]
    internal_p = [v["p_value"] for v in i10["confirmatory"].values()]
    names += [f"ucsf_pdgm:{k}" for k in mine["external_family"]]
    mine_p = internal_p + [v["p_value"] for v in mine["external_family"].values()]
    ref_p = internal_p + [
        r10["confirmatory"][k]["p_value"] for k in mine["external_family"]
    ]
    mine_bh, ref_bh = bh(mine_p), bh(ref_p)
    assert len(names) == 29
    for name, value, reference in zip(names, mine_bh, ref_bh, strict=True):
        diff = Fraction(value) - Fraction(reference)
        rows.append(
            (
                f"pooled_BH.{name}",
                value,
                reference,
                str(diff),
                diff == 0,
                "exact",
                "POOLED_PROPAGATION" if diff else "",
            )
        )
    # Status strings are kept verbatim in the table; category equivalence is
    # explicit, since SAP's 'inconclusive at this n' is shortened in the author JSON.
    statuses = []

    def status(name, value, reference, cause=""):
        def canonical(s):
            return "inconclusive" if s == "inconclusive at this n" else s

        statuses.append(
            (name, value, reference, canonical(value) == canonical(reference), cause)
        )

    for condition in CONDITIONS:
        for claim in ("C3", "C4", "C5", "C6"):
            if claim == "C3":
                ref = (
                    r9["claims"][claim]["full"]
                    if condition == "full"
                    else r9["claims"][claim]["secondary_by_condition"][condition]
                )["status"]
            else:
                ref = r9["claims"][claim][condition]["status"]
            status(
                f"{condition}.{claim}",
                mine["conditions"][condition]["claims"][claim],
                ref,
            )
    for claim in ("C3", "C4", "C5", "C6"):
        ref = r9["claims"][claim]["status" if claim == "C3" else "worst_status"]
        status(
            f"overall.{claim}",
            mine["overall_claims"][claim],
            ref,
            "OWN_C3_AGGREGATION" if claim == "C3" else "",
        )
    status(
        "secondary_worst.C3",
        mine["overall_claims"]["C3"],
        r9["claims"]["C3"]["secondary_worst_status"],
    )
    for condition in CONDITIONS:
        for alpha in ALPHAS:
            for band in ("0.07", "0.05"):
                status(
                    f"{condition}.alpha_{alpha}.coverage_label_{band}",
                    mine["conditions"][condition]["conformal"][str(alpha)][
                        "coverage_labels"
                    ][band],
                    r9["conformal"][condition]["carried_over"][str(alpha)][
                        "coverage_deviation_bootstrap"
                    ][f"deviation_label_band_{band}"],
                )
    causes = {
        "TEMPERATURE_SOLVER": (
            "Independent inverse-temperature bisection gives 1.1247554289138795, "
            "frozen fit 1.1247554245437905 (difference 4.370089e-9). K5 allows "
            "1e-6 on T, but this task asks 1e-9 on point estimates; strict failure "
            "is retained. Calibration metrics/quantiles are compared separately."
        ),
        "UNPAIRED_STREAMS": (
            "Block C1 raw p is 8/29 versus 554/2001. Blinded code draws the UCSF "
            "matrix then UTSW matrix successively from default_rng(0). A separate "
            "diagnostic restarting default_rng(0) for each cohort reproduced the "
            "author lower=-0.07786734507784494, upper=0.02122924640373 and "
            "p=554/2001 exactly. Reusing the same seeded stream for both cohort "
            "matrices makes the matrices dependent, contrary to SAP section 4's "
            "independent-resamples instruction. This is an inferred author "
            "stream-construction bug, verified by aggregate reproduction, not "
            "source inspection. No compute change was made. Research Lead review "
            "is required; practical differences are small but exact p fails."
        ),
        "C4_MC": (
            "Four lower interval endpoints exceed .01. Mine uses seed 0 and "
            "successive complete calibration/test matrices, shared across cells. "
            "Reference declares seed=10000+100*condition_index+alpha_index. "
            "Diagnostic on full/alpha=.2 using seed 10002 and interleaving "
            "calibration and test draws reproduces reference endpoints exactly "
            "(-0.1960396039603961, 0.0861386138613861); sequential matrices give "
            "a different endpoint. Cause: Monte Carlo/index-schedule difference, "
            "not a quantile/coverage formula disagreement. Results left unchanged."
        ),
        "C6_MC_OR_ENCODING": (
            "Mine permutes the original patient-ordered loss vector at seed 0 "
            "once per condition and shares permutations across the grid. Author "
            "declares seed+coverage_index on its descending grid. Counts vary "
            "with seed and equivalent permutation layouts; matching seed alone "
            "did not reproduce the full permutation index scheme (12/30 counts "
            "matched in a diagnostic). Differences in integer exceedance counts "
            "are Monte Carlo noise; exact equality is still required and fails. "
            "Additionally author raw p is a rounded float, and its adjusted p "
            "is an exact fraction of that decimal rather than of the original "
            "integer-count rational. Even equal exceedance counts therefore "
            "fail exact-rational equality. Example full/0.5 BH: mine=5/30003, "
            "author=4999500049995001/30000000000000000000. This encoding difference "
            "has negligible numeric size but is retained as a strict discrepancy. "
            "No claim category changes. The author's full permutation index "
            "scheme remains unverified because its implementation was not read."
        ),
        "POOLED_PROPAGATION": (
            "Pooled BH differences propagate Block C1's raw-p difference or tiny "
            "DeLong floating-point differences. BH is exact Fraction arithmetic "
            "on the saved p-values; no p-value was replaced with the reference. "
            "The reference column is recalculated from author raw p-values, not "
            "a claim to have read phase13_final_analysis.json (never opened)."
        ),
        "OWN_C3_AGGREGATION": (
            "Own overall_claims.C3 incorrectly takes the worst over primary full "
            "and all secondary missing-modality conditions (inconclusive). "
            "Author keeps primary full C3=supported and secondary_worst_status="
            "inconclusive. Per-condition categories and the separately mapped "
            "secondary worst agree. This is an own aggregation/labeling bug, "
            "not a risk-estimation disagreement. Stopped; not patched after "
            "unblinding. Claim statuses therefore do not all match overall."
        ),
        "OWN_ORACLE_TIES": (
            "Own oracle uses selective(-loss, loss), which puts every erroneous "
            "case in one confidence tie block. Its AURC therefore equals (e/n)^2. "
            "The oracle must instead order all correct cases before all errors "
            "and evaluate each cutoff individually: sum(j/(n-e+j), j=1..e)/n. "
            "An exact Fraction hand-sum of that expression matches all six "
            "author oracle values exactly. This is an own oracle implementation "
            "bug; the other mechanism AURCs are unaffected. The saved compute "
            "code/results are preserved rather than patched after unblinding."
        ),
        "UNRESOLVED_STOP": "Unexpected disagreement: stop for Research Lead review.",
    }
    ok = sum(row[4] for row in rows)
    status_ok = sum(row[3] for row in statuses)
    used = {row[6] for row in rows if not row[4]}
    used.update(row[4] for row in statuses if not row[3])
    lines = [
        "# T13.9 independent external recomputation",
        "",
        "**BLOCKED — real disagreements found; scientific changes stopped.**",
        "D-001 degraded solo fallback: a second agent, not a second human.",
        "",
        f"Numbers compared: **{len(rows)}**; ok: **{ok}**; discrepancies: "
        f"**{len(rows) - ok}**. Additional saved numeric outputs without an allowed "
        f"reference: **{len(missing)}**, listed separately and excluded from the "
        "comparison denominator. They are not counted as agreement.",
        f"Status/coverage-label comparisons: {status_ok}/{len(statuses)} category "
        "matches. All 24 per-condition C3–C6 categories agree; overall primary "
        "C3 does not, due to OWN_C3_AGGREGATION. Raw inconclusive strings differ "
        "('inconclusive at this n' versus 'inconclusive'); table retains both.",
        "",
        "## Independence and scope",
        "",
        "Compute finished and exclusively created the results JSON before any "
        "author result was opened. Only permitted contracts, decision entries, "
        "freeze_spec and the earlier independent script were read; no prohibited "
        "analysis source, analyze script, person_c_recompute.py or phase13 result "
        "was opened. The allowed result files were first opened in the later "
        "comparison step. Compare adds mappings and a report only; it never "
        "alters the blinded JSON or scientific compute functions. Separate "
        "post-unblinding diagnostics above explain index schedules, not replace "
        "the blinded numbers. No patient IDs or patient rows are output.",
        "",
        "Blinded results SHA-256: "
        f"`{hashlib.sha256(mine_path.read_bytes()).hexdigest()}`.",
        f"Pre-comparison script SHA-256: `{mine['implementation_sha256']}` "
        "(comparison function was still a stub; final script adds compare only).",
        f"Parquet inputs: {len(mine['input_sha256'])}; all present sidecars "
        "verified; absent sidecars: "
        f"{sum(not v['sidecar_verified'] for v in mine['input_sha256'].values())}.",
        "No environment authorization flag was set; no /Volumes write, source, "
        "test, config, other document change, commit or merge was performed.",
        "",
        "## Discrepancy causes",
        "",
    ]
    for cause in sorted(used):
        count = sum(row[6] == cause and not row[4] for row in rows)
        lines.extend(
            [f"**{cause}** ({count} numeric discrepancies). " + causes[cause], ""]
        )
    lines += ["## Frozen rules applied", ""]
    lines += [f"- **{key}**: {value}" for key, value in mine["rules"].items()]
    lines += [
        "",
        "## Resampling and calibration provenance",
        "",
        "```json",
        json.dumps(mine["resampling"], indent=2),
        "```",
        "",
        "Author seed schedule (read only after compute):",
        "",
        "```json",
        json.dumps(r9["results_summary"]["seed_schedule"], indent=2),
        "```",
        "",
        "Paired seed-0 patient bootstrap matches the author empirically "
        "across paired family intervals and exact bootstrap p-values. "
        "C4, C6 and unpaired C index schemes did not match; intervals use "
        "the requested .01 absolute tolerance, point estimates 1e-9, "
        "rational p and BH strict equality. Finite DeLong p uses 1e-9. "
        "No tolerance is relaxed after seeing results.",
        "",
        "Calibration uses conditions/full.parquet; predictions.parquet "
        "was also verified. Its logits differ by at most "
        f"{mine['calibration_source']['base_predictions_max_logit_difference']}; "
        f"its fitted T={mine['calibration_source']['base_predictions_temperature']}. "
        "The condition-sweep calibration fit matches the written frozen "
        "specification within K5's 1e-6 solver tolerance. Neither uses "
        "external rows. Author R7/R8 M2 metrics require their own UTSW "
        "calibration files, which were not among the requested inputs; "
        "ablation ECE/Brier here are explicitly raw M1.",
        "",
        "## Every compared number",
        "",
        "| Number | Yours | Reference | Yours minus reference | Status | "
        "Tolerance / cause |",
        "|---|---:|---:|---:|---|---|",
    ]
    for name, value, ref, diff, agrees, kind, cause in rows:
        rule = "exact" if kind == "exact" else ".01" if kind == "interval" else "1e-9"
        lines.append(
            f"| {name} | {value} | {ref} | {diff} | "
            f"{'ok' if agrees else 'DISCREPANCY'} | {rule} {cause} |"
        )
    lines += [
        "",
        "## Claim statuses and coverage labels",
        "",
        "| Claim / label | Yours | Reference | Status / cause |",
        "|---|---|---|---|",
    ]
    for name, value, ref, agrees, cause in statuses:
        lines.append(
            f"| {name} | {value} | {ref} | "
            f"{'ok' if agrees else 'DISCREPANCY'} {cause} |"
        )
    lines += [
        "",
        "## Pooled registered family",
        "",
        "ONE family of 29 at q=.05: 14 UTSW raw p-values borrowed only now "
        "and 15 independently computed external p-values. The pooled_BH "
        "rows above compare this pass with the same pass on author raw "
        "external values. Author published final adjusted values were "
        "not supplied in an allowed comparison file, so agreement with "
        "that publication is not asserted. External-only BH in the JSON "
        "is supplementary and is not substituted for the pooled family.",
        "",
        "| Member | Raw p used | Pooled adjusted p | Reject < .05 |",
        "|---|---:|---:|---|",
    ]
    for name, raw, adj in zip(names, mine_p, mine_bh, strict=True):
        lines.append(f"| {name} | {raw} | {adj} | {Fraction(adj) <= Fraction(1, 20)} |")
    lines += [
        "",
        "## Saved numbers with no allowed reference field",
        "",
        "These are DISCREPANCY (reference coverage), not established "
        "numeric disagreement. The permitted Phase 09 external JSON "
        "does not include per-condition AUROC/AUPRC/ECE/Brier; Phase 10 "
        "contains full only. It also omits trapezoid intervals, C5 p-values "
        "and ablation DeLong variance. Additional optional output is "
        "retained; no reference value is invented. Calibration n is "
        "measured from parquet, not inferred from internal test n.",
        "",
        "| Number | Yours | Reference | Difference | Status |",
        "|---|---:|---|---|---|",
    ]
    for name, value in missing:
        lines.append(
            f"| {name} | {value} | absent in allowed files | n/a | "
            "DISCREPANCY (reference coverage) |"
        )
    lines += [
        "",
        "## Validation and next action",
        "",
        "Independent hand-derived self-checks ran at compute start. "
        "ruff check and ruff format were run on the final script. "
        "No commit was requested or made; Gate A/B were not claimed. "
        "This is a recomputation audit, not a scientific run or Gate C/D "
        "completion. The requested stopping rule applies.",
        "",
        "Research Lead: adjudicate Block C's independent resampling and "
        "the own C3 aggregation bug before accepting T13.9; authorize a "
        "fresh, separately named rerun if corrections are wanted. Preserve "
        "these blinded artifacts.",
        "",
    ]
    with report.open("x") as stream:
        stream.write("\n".join(lines))
    print(
        f"Numbers compared {len(rows)}; ok {ok}; discrepancies {len(rows) - ok}; "
        f"no reference {len(missing)}; status categories {status_ok}/{len(statuses)}"
    )
    if ok != len(rows) or status_ok != len(statuses) or missing:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    c = commands.add_parser("compute")
    c.add_argument("--out", type=Path, required=True)
    c = commands.add_parser("compare")
    c.add_argument("--mine", type=Path, required=True)
    c.add_argument("--reference-dir", type=Path, required=True)
    c.add_argument("--internal10", type=Path, required=True)
    c.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "compute":
        compute(args.out)
    else:
        compare(args.mine, args.reference_dir, args.internal10, args.report)


if __name__ == "__main__":
    main()
