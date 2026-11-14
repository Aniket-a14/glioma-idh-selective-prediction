"""Claude's independent DeLong reference: the midrank (fast DeLong) algorithm.

Sun and Xu 2014.

Different organization from the contract text on purpose: placement values come from
midranks, not from the O(m n) pairwise sums.
"""

from __future__ import annotations

from math import erfc, sqrt

import numpy as np


def midrank(x: np.ndarray) -> np.ndarray:
    """Average ranks (1-based) with ties sharing their mean rank."""
    order = np.argsort(x, kind="mergesort")
    z = x[order]
    n = len(x)
    out = np.empty(n)
    i = 0
    while i < n:
        j = i
        while j < n and z[j] == z[i]:
            j += 1
        out[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    result = np.empty(n)
    result[order] = out
    return result


def delong_reference(a: object, b: object, labels: object) -> dict[str, float]:
    a, b, y = (np.asarray(v, dtype=float) for v in (a, b, labels))
    pos, neg = y == 1, y == 0
    m, n = int(pos.sum()), int(neg.sum())
    if m < 2 or n < 2:
        raise ValueError("need two of each class")
    aucs, v10, v01 = [], [], []
    for s in (a, b):
        tx, ty, tz = midrank(s[pos]), midrank(s[neg]), midrank(s)
        aucs.append(tz[pos].sum() / m / n - (m + 1) / 2 / n)
        v10.append((tz[pos] - tx) / n)
        v01.append(1 - (tz[neg] - ty) / m)
    v10 = np.array(v10)
    v01 = np.array(v01)
    s10 = np.cov(v10)  # unbiased, (m - 1)
    s01 = np.cov(v01)
    contrast = np.array([1.0, -1.0])
    var = float(contrast @ s10 @ contrast / m + contrast @ s01 @ contrast / n)
    diff = float(aucs[0] - aucs[1])
    if var <= 1e-18:
        z = 0.0 if abs(diff) < 1e-12 else float("inf") * (1 if diff > 0 else -1)
        p = 1.0 if abs(diff) < 1e-12 else 0.0
    else:
        z = diff / sqrt(var)
        p = erfc(abs(z) / sqrt(2))
    return {
        "auc_a": aucs[0],
        "auc_b": aucs[1],
        "difference": diff,
        "variance": var,
        "z": z,
        "p_value": p,
    }
