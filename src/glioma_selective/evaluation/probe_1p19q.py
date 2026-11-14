"""RQ4: exploratory 1p/19q frozen-encoder probe (D-007 option (c), PREREG. section 11).

A small linear head is fitted on the pooled bottleneck features of the trained IDH model
(R2, frozen: no weight of the IDH network moves), so the primary endpoint cannot be
harmed. Everything below is fixed in advance and none of it is tuned:

- features: the tumour-aware pooled bottleneck vector of the full four-sequence input,
  no augmentation, eval mode;
- standardization: mean and standard deviation from the UTSW train split only;
- probe: L2 logistic regression, ``C = 1``, class-balanced weights, unpenalized bias
  (the objective ``0.5 ||b||^2 + C sum_i w_i BCE_i`` with ``w_i = n / (2 n_class)``);
- fitted on the UTSW train patients that carry a 1p/19q label, scored on the UTSW
  internal test patients that carry one;
- reported with patient-level percentile bootstrap intervals and the Hanley-McNeil
  half-width, with the 1p/19q class counts beside every number, and with no inferential
  claim. A null result is expected at about 12 co-deleted test patients and is not
  evidence of absence (D-007).

Codeletion in diffuse glioma occurs almost only with an IDH mutation, so a probe can
score well by re-reading IDH status. The report therefore also gives the AUROC of the
IDH-mutant probability itself as a comparator, and the probe AUROC inside the IDH-mutant
test patients, where that shortcut is unavailable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray

from glioma_selective.evaluation.phase06_report import average_precision
from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)
from glioma_selective.training.determinism import deterministic_mode
from glioma_selective.training.metrics import binary_auroc

__all__ = [
    "ProbeFit",
    "analyze_probe",
    "class_counts",
    "extract_features",
    "fit_logistic_probe",
    "hanley_mcneil_half_width",
    "probe_scores",
]

C_REGULARIZATION = 1.0
BOOTSTRAP_ITERATIONS = 2000
BOOTSTRAP_SEED = 0


@dataclass(frozen=True)
class ProbeFit:
    """Standardization statistics and the fitted logistic weights."""

    mean: NDArray[np.float64]
    scale: NDArray[np.float64]
    weights: NDArray[np.float64]
    bias: float
    objective: float
    converged: bool


def extract_features(
    model: torch.nn.Module,
    dataset: Sequence[Mapping[str, Any]] | Any,
    *,
    device: torch.device | str,
    batch_size: int = 1,
) -> dict[str, Any]:
    """Pooled bottleneck features and IDH logit of a frozen model, in dataset order."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    model.to(device)
    model.eval()
    ids: list[str] = []
    features: list[NDArray[np.float64]] = []
    logits: list[float] = []
    idh_labels: list[int] = []
    with deterministic_mode(), torch.no_grad():
        for offset in range(0, len(dataset), batch_size):
            samples = [
                dataset[index]
                for index in range(offset, min(offset + batch_size, len(dataset)))
            ]
            image = torch.stack([sample["image"] for sample in samples]).to(device)
            pooled, _ = model.pooled_features(image)  # type: ignore[operator]
            logit = model.head(pooled)  # type: ignore[operator]
            features.append(pooled.detach().cpu().to(torch.float64).numpy())
            logits.extend(float(v) for v in logit.detach().cpu().tolist())
            ids.extend(str(sample["patient_id"]) for sample in samples)
            idh_labels.extend(int(sample["label"].item()) for sample in samples)
    return {
        "patient_ids": ids,
        "features": np.concatenate(features, axis=0),
        "idh_logit": np.asarray(logits, dtype=np.float64),
        "idh_label": np.asarray(idh_labels, dtype=np.int64),
    }


def _check_matrix(features: NDArray[Any], labels: NDArray[Any]) -> None:
    if features.ndim != 2 or labels.ndim != 1 or len(features) != len(labels):
        raise ValueError("features must be [N, C] and labels [N] with equal N")
    if not np.isfinite(features).all():
        raise ValueError("features must be finite")
    if set(np.unique(labels).tolist()) != {0, 1}:
        raise ValueError("labels must contain both classes 0 and 1")


def fit_logistic_probe(
    features: NDArray[np.floating[Any]],
    labels: NDArray[np.integer[Any]],
    *,
    c: float = C_REGULARIZATION,
    max_iter: int = 500,
) -> ProbeFit:
    """Class-balanced L2 logistic regression on train-split-standardized features."""
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    _check_matrix(x, y)
    if c <= 0:
        raise ValueError("c must be positive")
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale = np.where(scale > 0, scale, 1.0)
    z = torch.from_numpy((x - mean) / scale)
    target = torch.from_numpy(y.astype(np.float64))
    n = len(y)
    n_pos = int(y.sum())
    weight = torch.where(
        target == 1,
        torch.tensor(n / (2 * n_pos), dtype=torch.float64),
        torch.tensor(n / (2 * (n - n_pos)), dtype=torch.float64),
    )
    beta = torch.zeros(z.shape[1], dtype=torch.float64, requires_grad=True)
    bias = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    optimizer = torch.optim.LBFGS(
        [beta, bias],
        lr=1.0,
        max_iter=max_iter,
        tolerance_grad=1e-10,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )

    def objective() -> torch.Tensor:
        logits = z @ beta + bias
        loss = torch.nn.functional.binary_cross_entropy_with_logits(
            logits, target, weight=weight, reduction="sum"
        )
        return 0.5 * (beta**2).sum() + c * loss

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        value = objective()
        value.backward()
        return value

    optimizer.step(closure)
    optimizer.zero_grad()
    final = objective()
    final.backward()
    assert beta.grad is not None and bias.grad is not None
    gradient = torch.cat([beta.grad.flatten(), bias.grad.flatten()])
    return ProbeFit(
        mean=mean,
        scale=scale,
        weights=beta.detach().numpy().copy(),
        bias=float(bias.item()),
        objective=float(final.item()),
        converged=bool(gradient.abs().max().item() < 1e-5),
    )


def probe_scores(
    fit: ProbeFit, features: NDArray[np.floating[Any]]
) -> NDArray[np.float64]:
    """Linear scores (logits) for new features, standardized with train statistics."""
    x = np.asarray(features, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != len(fit.weights):
        raise ValueError("features must be [N, C] with the fitted width")
    return ((x - fit.mean) / fit.scale) @ fit.weights + fit.bias


def hanley_mcneil_half_width(auc: float, n_pos: int, n_neg: int) -> float:
    """95% half-width of the AUROC under the Hanley-McNeil (1982) variance."""
    if n_pos < 1 or n_neg < 1:
        raise ValueError("both classes are needed")
    q1 = auc / (2 - auc)
    q2 = 2 * auc * auc / (1 + auc)
    variance = (
        auc * (1 - auc)
        + (n_pos - 1) * (q1 - auc * auc)
        + (n_neg - 1) * (q2 - auc * auc)
    ) / (n_pos * n_neg)
    return float(1.96 * np.sqrt(max(variance, 0.0)))


def _metrics(scores: NDArray[np.float64], labels: NDArray[np.int64]) -> dict[str, Any]:
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return {"n": len(labels), "n_codeleted": n_pos, "auroc": None, "auprc": None}
    auc = float(binary_auroc(scores, labels))
    return {
        "n": len(labels),
        "n_codeleted": n_pos,
        "auroc": auc,
        "auprc": float(average_precision(scores, labels)),
        "auroc_hanley_mcneil_half_width": hanley_mcneil_half_width(auc, n_pos, n_neg),
    }


def _bootstrap(
    scores: NDArray[np.float64],
    labels: NDArray[np.int64],
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    indices = bootstrap_indices(len(labels), iterations, seed)
    auroc: list[float] = []
    auprc: list[float] = []
    skipped = 0
    for row in indices:
        sample_labels = labels[row]
        if sample_labels.min() == sample_labels.max():
            skipped += 1  # a resample without both classes has no AUROC
            continue
        auroc.append(float(binary_auroc(scores[row], sample_labels)))
        auprc.append(float(average_precision(scores[row], sample_labels)))
    out: dict[str, Any] = {"iterations": iterations, "skipped_single_class": skipped}
    if auroc:
        out["auroc_95_interval"] = list(percentile_interval(np.asarray(auroc)))
        out["auprc_95_interval"] = list(percentile_interval(np.asarray(auprc)))
    return out


def analyze_probe(
    train_features: NDArray[np.floating[Any]],
    train_labels: NDArray[np.integer[Any]],
    test_features: NDArray[np.floating[Any]],
    test_labels: NDArray[np.integer[Any]],
    test_idh_logit: NDArray[np.floating[Any]],
    test_idh_label: NDArray[np.integer[Any]],
    *,
    iterations: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> Mapping[str, Any]:
    """Fit on the train split, score the internal test split, and report descriptively.

    Labels are 1 for co-deleted and 0 for non-co-deleted. ``test_idh_logit`` is the IDH
    model's own logit for each test patient and ``test_idh_label`` the IDH label (1 for
    mutant), used for the comparator and for the IDH-mutant subgroup.
    """
    fit = fit_logistic_probe(train_features, train_labels)
    scores = probe_scores(fit, test_features)
    y = np.asarray(test_labels, dtype=np.int64)
    idh = np.asarray(test_idh_label, dtype=np.int64)
    idh_logit = np.asarray(test_idh_logit, dtype=np.float64)
    mutant = idh == 1
    return {
        "label": (
            "exploratory (RQ4, D-007); no inferential claim; "
            "a null result is not evidence of absence"
        ),
        "probe": {
            "model": (
                "L2 logistic regression, C = 1, class-balanced, "
                "train-split standardization"
            ),
            "n_features": int(len(fit.weights)),
            "converged": fit.converged,
            "objective": fit.objective,
        },
        "train": {
            "n": int(len(train_labels)),
            "n_codeleted": int(np.sum(train_labels)),
        },
        "internal_test": {
            "probe": _metrics(scores, y),
            "probe_bootstrap": _bootstrap(scores, y, iterations, seed),
            "comparator_idh_probability": _metrics(idh_logit, y),
            "comparator_idh_bootstrap": _bootstrap(idh_logit, y, iterations, seed),
            "idh_mutant_only": {
                "probe": _metrics(scores[mutant], y[mutant]),
                "comparator_idh_probability": _metrics(idh_logit[mutant], y[mutant]),
                "probe_bootstrap": _bootstrap(
                    scores[mutant], y[mutant], iterations, seed
                ),
            },
        },
        "settings": {"iterations": iterations, "seed": seed, "c": C_REGULARIZATION},
    }


def class_counts(labels: Sequence[int]) -> dict[str, int]:
    """Counts of co-deleted (1) and non-co-deleted (0) patients."""
    array = np.asarray(labels, dtype=np.int64)
    return {
        "codeleted": int(array.sum()),
        "non_codeleted": int(len(array) - array.sum()),
    }
