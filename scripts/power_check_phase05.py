#!/usr/bin/env python3
"""Phase 05 T05.1 power check: bootstrap CI widths for a UTSW internal test set.

Simulation only. No image data and no UCSF-PDGM/EGD labels are read. Class counts are
arguments so nothing is hard-coded; verify them against the post-QC manifests first.
"""

from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.stats import beta, norm, rankdata

COVERAGE_GRID = (0.9, 0.8, 0.7, 0.6, 0.5)
AUROC_GRID = (0.75, 0.80, 0.85, 0.90)


def simulate_test_set(
    rng: np.random.Generator, n_pos: int, n_neg: int, auroc: float, prevalence: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Equal-variance binormal scores with the exact posterior (calibrated)."""
    d = math.sqrt(2.0) * norm.ppf(auroc)
    y = np.concatenate([np.ones(n_pos, dtype=int), np.zeros(n_neg, dtype=int)])
    s = rng.normal(size=y.size) + d * y
    logit = math.log(prevalence / (1.0 - prevalence)) + d * s - d * d / 2.0
    p = 1.0 / (1.0 + np.exp(-logit))
    return y, s, p


def auroc_rows(y: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Mann-Whitney AUROC per row of a (B, n) resample; one-class rows give NaN."""
    ranks = rankdata(s, axis=1)
    n_pos = y.sum(axis=1)
    n_neg = y.shape[1] - n_pos
    u = (ranks * y).sum(axis=1) - n_pos * (n_pos + 1) / 2.0
    with np.errstate(invalid="ignore", divide="ignore"):
        out = u / (n_pos * n_neg)
    out[(n_pos == 0) | (n_neg == 0)] = np.nan
    return out


def selective_risk_rows(
    err: np.ndarray, conf: np.ndarray, coverages: tuple[float, ...]
) -> np.ndarray:
    """0-1 selective risk: error rate of the top round(phi*n) by confidence."""
    n = err.shape[1]
    order = np.argsort(-conf, axis=1)
    cum = np.cumsum(np.take_along_axis(err, order, axis=1), axis=1)
    out = np.empty((err.shape[0], len(coverages)))
    for j, phi in enumerate(coverages):
        k = max(1, round(phi * n))
        out[:, j] = cum[:, k - 1] / k
    return out


def half_width(values: np.ndarray) -> float:
    lo, hi = np.nanpercentile(values, [2.5, 97.5], axis=0)
    return float((hi - lo) / 2.0)


def one_config(
    rng: np.random.Generator,
    n_pos: int,
    n_neg: int,
    auroc: float,
    prevalence: float,
    reps: int,
    boot: int,
) -> dict[str, object]:
    n = n_pos + n_neg
    auc_hw: list[float] = []
    risk_hw: list[list[float]] = []
    risk_pt: list[list[float]] = []
    for _ in range(reps):
        y, s, p = simulate_test_set(rng, n_pos, n_neg, auroc, prevalence)
        err = ((p > 0.5).astype(int) != y).astype(float)
        conf = np.maximum(p, 1.0 - p)
        idx = rng.integers(0, n, size=(boot, n))
        auc_hw.append(half_width(auroc_rows(y[idx], s[idx])))
        rows = selective_risk_rows(err[idx], conf[idx], COVERAGE_GRID)
        risk_hw.append([half_width(rows[:, j]) for j in range(len(COVERAGE_GRID))])
        risk_pt.append(
            selective_risk_rows(err[None, :], conf[None, :], COVERAGE_GRID)[0].tolist()
        )
    return {
        "n_test": n,
        "auroc_true": auroc,
        "auroc_ci_half_width": float(np.mean(auc_hw)),
        "coverage_grid": list(COVERAGE_GRID),
        "n_accepted": [max(1, round(phi * n)) for phi in COVERAGE_GRID],
        "selective_risk_expected": np.mean(risk_pt, axis=0).tolist(),
        "selective_risk_ci_half_width": np.mean(risk_hw, axis=0).tolist(),
    }


def split_conformal_coverage(n_cal: int, alpha: float) -> dict[str, float]:
    """Coverage law given the calibration draw: Beta(n+1-l, l), l=floor((n+1)a)."""
    ell = math.floor((n_cal + 1) * Fraction(str(alpha)))
    a, b = n_cal + 1 - ell, ell
    lo, hi = beta.ppf([0.025, 0.975], a, b)
    return {
        "n_cal": n_cal,
        "alpha": alpha,
        "mean": float(beta.mean(a, b)),
        "sd": float(beta.std(a, b)),
        "p2_5": float(lo),
        "p97_5": float(hi),
    }


def binomial_half_width(n: int, p: float) -> float:
    return 1.96 * math.sqrt(p * (1.0 - p) / n)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-mutant", type=int, required=True)
    parser.add_argument("--n-wildtype", type=int, required=True)
    parser.add_argument("--reps", type=int, default=300)
    parser.add_argument("--boot", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    total = args.n_mutant + args.n_wildtype
    prevalence = args.n_mutant / total
    proportions = {
        "60/20/20": (0.6, 0.2, 0.2),
        "70/15/15": (0.7, 0.15, 0.15),
        "50/25/25": (0.5, 0.25, 0.25),
        "60/15/25": (0.6, 0.15, 0.25),
    }
    rng = np.random.default_rng(args.seed)
    result: dict[str, object] = {
        "seed": args.seed,
        "reps": args.reps,
        "boot": args.boot,
        "n_mutant": args.n_mutant,
        "n_wildtype": args.n_wildtype,
        "prevalence": prevalence,
        "splits": {},
    }
    splits: dict[str, object] = {}
    for name, (_, cal_frac, test_frac) in proportions.items():
        n_test = round(total * test_frac)
        n_cal = round(total * cal_frac)
        n_pos = round(n_test * prevalence)
        configs = [
            one_config(rng, n_pos, n_test - n_pos, a, prevalence, args.reps, args.boot)
            for a in AUROC_GRID
        ]
        splits[name] = {
            "n_train": total - n_test - n_cal,
            "n_cal": n_cal,
            "n_test": n_test,
            "test_mutants": n_pos,
            "configs": configs,
            "conformal_coverage": [
                split_conformal_coverage(n_cal, alpha) for alpha in (0.05, 0.10, 0.20)
            ],
        }
    result["splits"] = splits
    result["external_coverage_binomial_half_width_at_0.90"] = {
        str(n): binomial_half_width(n, 0.90) for n in (202, 300, 450, 500)
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
