"""Phase 13 tables: copy frozen values; never estimate metrics or adjudicate claims.

CSV preserves Python's round-trip numeric spelling. TeX precision is controlled
only by COLUMN_DIGITS and format_number. Missing required keys raise KeyError;
there are no imputed cells. Aggregate manifests supply counts, not demographics.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MECHANISMS = ("M1", "M2", "M3", "M4", "M5", "M6")
COVERAGE_KEYS = ("0.5", "0.6", "0.7", "0.8", "0.9")
ALPHA_KEYS = ("0.05", "0.1", "0.2")
CONFORMAL_VARIANTS = ("carried_over", "refit")
COVERAGE_BAND = 0.07  # Frozen C4 tolerance, not a measured result.
COLUMN_DIGITS = {
    "n": 0,
    "retained_patient_count": 0,
    "excluded_patient_count": 0,
    "count": 0,
    "n_rejected": 0,
    **dict.fromkeys(
        (
            "aurc",
            "aurc_lower",
            "aurc_upper",
            "oracle_aurc",
            "target_coverage",
            "attained_coverage",
            "coverage_lower",
            "coverage_upper",
            "risk",
            "risk_lower",
            "risk_upper",
            "rejected_but_correct_rate",
            "alpha",
            "empirical_coverage",
            "deviation_lower",
            "deviation_upper",
            "half_width",
            "tolerance_band",
            "auroc",
            "auroc_lower",
            "auroc_upper",
            "auprc",
            "auprc_lower",
            "auprc_upper",
            "ece",
            "ece_lower",
            "ece_upper",
            "brier",
            "brier_lower",
            "brier_upper",
            "coverage",
        ),
        3,
    ),
}
HIERARCHY = ("ece", "brier", "aurc", "coverage")


class MetricHierarchyError(ValueError):
    """SI-14: AUROC requires calibration, selective risk summary and coverage."""


@dataclass(frozen=True)
class Table:
    """Ordered columns and rows copied from frozen sources."""

    caption: str
    columns: tuple[str, ...]
    rows: list[dict[str, Any]]

    @property
    def headers(self) -> tuple[str, ...]:
        return tuple(
            "condition (simulated missingness)" if key == "condition" else key
            for key in self.columns
        )


def condition_label(condition: str) -> str:
    """Keep the frozen condition name and explicitly label simulated missingness."""
    if condition.startswith("drop_") or condition == "t1ce_flair_only":
        return f"{condition} (simulated)"
    return condition


def operating_points(cell: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Require all five frozen operating points, then retain every stored point."""
    operations: dict[str, dict[str, Any]] = cell["selective_risk_at_coverage"]
    for key in COVERAGE_KEYS:
        operations[key]  # A missing point is a stop, never a shorter grid.
    return sorted(operations.items(), key=lambda item: float(item[0]))


def conformal_alphas(
    variants: dict[str, Any], variant: str
) -> list[tuple[str, dict[str, Any]]]:
    """Require every alpha from the frozen Phase 09 writer, without defaults."""
    alphas: dict[str, dict[str, Any]] = variants[variant]
    for key in ALPHA_KEYS:
        alphas[key]
    return sorted(alphas.items(), key=lambda item: float(item[0]))


def format_number(value: Any, column: str) -> str:
    """The sole rounding function for TeX; CSV never calls it."""
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{value:.{COLUMN_DIGITS[column]}f}"
    return str(value)


def tex_escape(value: str) -> str:
    """Escape source text, including exclusion reasons, for booktabs cells."""
    escapes = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(escapes.get(char, char) for char in value)


def validate_hierarchy(table: Table) -> None:
    """Reject AUROC output when any companion metric is missing in any row."""
    if "auroc" not in table.columns:
        return
    if any(key not in table.columns for key in HIERARCHY):
        raise MetricHierarchyError("AUROC requires ECE, Brier, AURC and coverage")
    for row in table.rows:
        if row["auroc"] != "absent" and any(
            row.get(key) is None or row.get(key) == "absent" for key in HIERARCHY
        ):
            raise MetricHierarchyError("AUROC row lacks SI-14 companion metrics")


def write_table(table: Table, stem: Path) -> tuple[Path, Path]:
    """Write full-precision CSV and rounded booktabs TeX, in fixed column order."""
    validate_hierarchy(table)
    csv_path, tex_path = stem.with_suffix(".csv"), stem.with_suffix(".tex")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(table.headers)
        writer.writerows([row[key] for key in table.columns] for row in table.rows)
    lines = [
        r"\begin{table}",
        r"\caption{" + tex_escape(table.caption) + "}",
        r"\begin{tabular}{" + "l" * len(table.columns) + "}",
        r"\toprule",
        " & ".join(tex_escape(key) for key in table.headers) + r" \\",
        r"\midrule",
    ]
    for row in table.rows:
        lines.append(
            " & ".join(
                tex_escape(format_number(row[key], key)) for key in table.columns
            )
            + r" \\"
        )
    lines.extend((r"\bottomrule", r"\end{tabular}", r"\end{table}"))
    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, tex_path


def cohort_tables(cohort: dict[str, Any], exclusions: dict[str, Any]) -> list[Table]:
    """Tables 1 and 2 use stored aggregate counts only, never patient identifiers."""
    characteristics = [
        {
            "cohort": name,
            "retained_patient_count": cell["retained_patient_count"],
            "excluded_patient_count": cell["excluded_patient_count"],
        }
        for name, cell in sorted(cohort["cohorts"].items())
    ]
    reasons = [
        {"cohort": name, "reason": reason, "count": count}
        for name, cell in sorted(exclusions["cohorts"].items())
        for reason, count in sorted(cell["reason_counts"].items())
    ]
    return [
        Table(
            "Cohort characteristics: post-QC patient counts.",
            ("cohort", "retained_patient_count", "excluded_patient_count"),
            characteristics,
        ),
        Table(
            "Patient exclusions by reason; reason counts may overlap.",
            ("cohort", "reason", "count"),
            reasons,
        ),
    ]


def _absent_row(
    columns: tuple[str, ...], identity: dict[str, Any], reason: str
) -> dict[str, Any]:
    return {**dict.fromkeys(columns, "absent"), **identity, "reason": reason}


def selective_tables(document: dict[str, Any], cohort: str) -> tuple[Table, Table]:
    """Tables 3 and 6 include every frozen operating point and absent mechanism."""
    identity = ("cohort", "condition", "mechanism")
    risk_columns = (
        *identity,
        "aurc",
        "aurc_lower",
        "aurc_upper",
        "oracle_aurc",
        "target_coverage",
        "attained_coverage",
        "coverage_lower",
        "coverage_upper",
        "risk",
        "risk_lower",
        "risk_upper",
        "reason",
    )
    abstention_columns = (
        *identity,
        "target_coverage",
        "attained_coverage",
        "risk",
        "rejected_but_correct_rate",
        "n_rejected",
        "reason",
    )
    risks, abstentions = [], []
    for condition, cells in sorted(document["conditions"].items()):
        for mechanism in MECHANISMS:
            cell = cells[mechanism]
            base = {
                "cohort": cohort,
                "condition": condition_label(condition),
                "mechanism": mechanism,
            }
            if cell.get("absent") is True:
                risks.append(_absent_row(risk_columns, base, cell["reason"]))
                abstentions.append(
                    _absent_row(abstention_columns, base, cell["reason"])
                )
                continue
            for target, op in operating_points(cell):
                shared = {
                    **base,
                    "target_coverage": float(target),
                    "attained_coverage": op["attained_coverage"],
                    "risk": op["risk"],
                    "reason": "",
                }
                risks.append(
                    {
                        **shared,
                        "aurc": cell["aurc_mean_over_cutoffs"],
                        "aurc_lower": cell["aurc_bootstrap_95_interval"]["lower"],
                        "aurc_upper": cell["aurc_bootstrap_95_interval"]["upper"],
                        "oracle_aurc": cell["oracle_aurc"],
                        "coverage_lower": op["attained_coverage_95_interval"]["lower"],
                        "coverage_upper": op["attained_coverage_95_interval"]["upper"],
                        "risk_lower": op["risk_95_interval"]["lower"],
                        "risk_upper": op["risk_95_interval"]["upper"],
                    }
                )
                abstentions.append(
                    {
                        **shared,
                        "rejected_but_correct_rate": op["rejected_but_correct_rate"],
                        "n_rejected": op["n_rejected"],
                    }
                )
    return (
        Table(
            "AURC and selective risk under complete and simulated missing modalities.",
            risk_columns,
            risks,
        ),
        Table(
            "Abstention under complete and simulated missing modalities.",
            abstention_columns,
            abstentions,
        ),
    )


def coverage_table(document: dict[str, Any], cohort: str) -> Table:
    """Table 4 copies absolute-deviation intervals and their frozen classifications."""
    rows = []
    for condition, variants in sorted(document["conformal"].items()):
        for variant in CONFORMAL_VARIANTS:
            for alpha, cell in conformal_alphas(variants, variant):
                interval = cell["coverage_deviation_bootstrap"]
                rows.append(
                    {
                        "cohort": cohort,
                        "condition": condition_label(condition),
                        "variant": variant,
                        "alpha": float(alpha),
                        "empirical_coverage": cell["empirical_coverage"],
                        "deviation_lower": interval["lower"],
                        "deviation_upper": interval["upper"],
                        "half_width": interval["half_width"],
                        "tolerance_band": COVERAGE_BAND,
                        "deviation_label": interval["deviation_label_band_0.07"],
                    }
                )
    return Table(
        (
            "Absolute coverage deviation under complete and simulated missing "
            "modalities; "
            "stored intervals versus the frozen tolerance band."
        ),
        (
            "cohort",
            "condition",
            "variant",
            "alpha",
            "empirical_coverage",
            "deviation_lower",
            "deviation_upper",
            "half_width",
            "tolerance_band",
            "deviation_label",
        ),
        rows,
    )


def headline_table(document: dict[str, Any], cohort: str) -> Table:
    """Table 5: quote AUROC's stored selected interval and keep SI-14 together."""
    columns = (
        "cohort",
        "run",
        "probability",
        "n",
        "auroc",
        "auroc_lower",
        "auroc_upper",
        "auroc_interval",
        "auprc",
        "auprc_lower",
        "auprc_upper",
        "ece",
        "ece_lower",
        "ece_upper",
        "brier",
        "brier_lower",
        "brier_upper",
        "aurc",
        "aurc_lower",
        "aurc_upper",
        "selective_mechanism",
        "coverage",
        "reason",
    )
    rows = []
    for name, run in sorted(document["runs"].items()):
        if run["status"] == "absent":
            rows.append(
                _absent_row(columns, {"cohort": cohort, "run": name}, run["reason"])
            )
            continue
        if any(
            key not in run
            for key in ("calibration", "aurc_mean_over_cutoffs", "coverage")
        ):
            raise MetricHierarchyError("AUROC run lacks SI-14 companion metrics")
        for calibration in run["calibration"].values():
            if any(key not in calibration for key in ("ece", "brier")):
                raise MetricHierarchyError("AUROC run lacks ECE or Brier")
            row = {
                "cohort": cohort,
                "run": name,
                "probability": calibration["probability"],
                "n": run["n"],
                "coverage": run["coverage"],
                "selective_mechanism": run["selective_mechanism"],
                "reason": "",
            }
            for metric, source in (
                ("auroc", run["auroc"]),
                ("auprc", run["auprc"]),
                ("ece", calibration["ece"]),
                ("brier", calibration["brier"]),
                ("aurc", run["aurc_mean_over_cutoffs"]),
            ):
                key = source["quoted"] if metric == "auroc" else "bootstrap_95_interval"
                row.update(
                    {
                        metric: source["point"],
                        metric + "_lower": source[key]["lower"],
                        metric + "_upper": source[key]["upper"],
                    }
                )
                if metric == "auroc":
                    row["auroc_interval"] = key
            rows.append(row)
    table = Table(
        "Discrimination and calibration with stored intervals, AURC and coverage.",
        columns,
        rows,
    )
    validate_hierarchy(table)
    return table
