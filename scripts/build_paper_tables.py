"""Write paper/generated/tbl_*.tex: manuscript tables built from the frozen files.

Each file holds one ``tabular`` body (booktabs); captions and widths live in
``paper/main.tex``. Nothing is typed by hand: every cell is read from the frozen
Phase 09/10 analyses (internal and external), the M6 file, the probe file, the
Phase 13 final analysis and the verified cohort-flow CSVs. No statistic is
recomputed.

    PYTHONPATH=src:. python scripts/build_paper_tables.py \
        --experiments /Volumes/Research_2/artifacts/experiments \
        --cohort-flow build/paper_artifacts_ext_a --out paper/generated
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

RUN = "01M46999FB083AX4WW0067YM13"
EXT1 = "external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_20261118"
CONDITIONS = [
    ("full", "Full"),
    ("drop_t1", "$-$T1 (sim.)"),
    ("drop_t1ce", "$-$T1ce (sim.)"),
    ("drop_t2", "$-$T2 (sim.)"),
    ("drop_flair", "$-$FLAIR (sim.)"),
    ("t1ce_flair_only", "T1ce+FLAIR (sim.)"),
]
COVERAGES = ["0.5", "0.6", "0.7", "0.8", "0.9"]
ALPHAS = ["0.05", "0.1", "0.2"]
MECHANISMS = ["M1", "M2", "M3", "M4", "M5"]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def f3(value: float) -> str:
    return f"{value:.3f}"


def interval(point: float, lower: float, upper: float) -> str:
    return f"{f3(point)} [{f3(lower)}, {f3(upper)}]"


def tabular(align: str, header: list[str], rows: list[list[str]]) -> str:
    lines = [
        f"\\begin{{tabular}}{{{align}}}",
        "\\toprule",
        " & ".join(header) + " \\\\",
    ]
    lines.append("\\midrule")
    for row in rows:
        lines.append(" & ".join(row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def tex_escape(text: str) -> str:
    return text.replace("_", "\\_").replace("%", "\\%")


def aurc_table(d09: dict[str, Any], m6: dict[str, Any] | None) -> str:
    rows = []
    for key, label in CONDITIONS:
        cell = d09["conditions"][key]
        row = [
            label,
            f3(cell["M2"]["always_predict_risk"]),
            f3(cell["M2"]["oracle_aurc"]),
        ]
        for mech in MECHANISMS:
            row.append(f3(cell[mech]["aurc_mean_over_cutoffs"]))
        if "aurc_mean_over_cutoffs" in cell.get("M6", {}):
            row.append(f3(cell["M6"]["aurc_mean_over_cutoffs"]))
        elif m6 is not None:
            row.append(f3(m6["conditions"][key]["aurc_mean_over_cutoffs"]))
        rows.append(row)
    return tabular(
        "lrrrrrrrr",
        ["Condition", "Always", "Oracle", "M1", "M2", "M3", "M4", "M5", "M6"],
        rows,
    )


def risk_table(d09: dict[str, Any]) -> str:
    rows = []
    for key, label in CONDITIONS:
        cell = d09["conditions"][key]["M2"]["selective_risk_at_coverage"]
        row = [label]
        for level in COVERAGES:
            entry = cell[level]
            bounds = entry["risk_95_interval"]
            row.append(interval(entry["risk"], bounds["lower"], bounds["upper"]))
        rows.append(row)
    return tabular("lccccc", ["Condition", *COVERAGES], rows)


def delta_table(d09: dict[str, Any]) -> str:
    rows = []
    for key, label in CONDITIONS:
        cell = d09["conditions"][key]["M2"]["selective_risk_at_coverage"]
        row = [label]
        for level in COVERAGES:
            point = cell[level]["D_phi"]["point"]
            upper = cell[level]["D_phi"]["upper"]
            row.append(f"{point:+.3f} ({upper:+.3f})")
        rows.append(row)
    return tabular("lccccc", ["Condition", *COVERAGES], rows)


def conformal_table(d09: dict[str, Any]) -> str:
    rows = []
    for key, label in CONDITIONS:
        for alpha in ALPHAS:
            carried = d09["conformal"][key]["carried_over"][alpha]
            refit = d09["conformal"][key]["refit"][alpha]
            dev = carried["coverage_deviation_bootstrap"]
            rows.append(
                [
                    label if alpha == ALPHAS[0] else "",
                    alpha,
                    f3(carried["empirical_coverage"]),
                    f3(dev["half_width"]),
                    dev["deviation_label_band_0.07"],
                    f3(carried["abstention_rate"]),
                    str(carried["empty_count"]),
                    f3(refit["empirical_coverage"]),
                    f3(refit["coverage_deviation_bootstrap"]["half_width"]),
                ]
            )
    return tabular(
        "llrrlrrrr",
        [
            "Condition",
            "$\\alpha$",
            "Cov.",
            "Half",
            "Label",
            "Abst.",
            "Empty",
            "Refit cov.",
            "Refit half",
        ],
        rows,
    )


def monotone_table(d09: dict[str, Any]) -> str:
    rows = []
    for key, label in CONDITIONS:
        cell = d09["conditions"][key]["M2"]
        diffs = cell["adjacent_grid_risk_differences"]
        points = [f"{item['point']:+.3f}" for item in diffs]
        worst_lower = max(item["lower"] for item in diffs)
        mono = cell["monotonicity"]
        rows.append(
            [
                label,
                *points,
                f"{worst_lower:+.3f}",
                str(mono["violations"]),
            ]
        )
    return tabular(
        "lcccccc",
        [
            "Condition",
            "0.5--0.6",
            "0.6--0.7",
            "0.7--0.8",
            "0.8--0.9",
            "Max lower",
            "Viol.",
        ],
        rows,
    )


def enrichment_table(d09: dict[str, Any]) -> str:
    rows = []
    for key, label in CONDITIONS:
        enrich = d09["conditions"][key]["M2"]["enrichment"]
        row = [label]
        for level in COVERAGES:
            entry = enrich[level]
            adjusted = _fraction(entry["adjusted_p_value"])
            row.append(f"{entry['observed_difference']:+.3f} ({adjusted:.3f})")
        rows.append(row)
    return tabular("lccccc", ["Condition", *COVERAGES], rows)


def _fraction(text: str | float) -> float:
    if isinstance(text, str) and "/" in text:
        numerator, denominator = text.split("/")
        return int(numerator) / int(denominator)
    return float(text)


def family_table(
    final: dict[str, Any], i10: dict[str, Any], e10: dict[str, Any]
) -> str:
    comparison = {row["id"]: row["comparison"] for row in i10["bh_family"]}
    estimates = {f"utsw:{k}": v for k, v in i10["confirmatory"].items()}
    estimates |= {f"ucsf_pdgm:{k}": v for k, v in e10["confirmatory"].items()}
    rows = []
    for member in final["family"]["members"]:
        ident = member["id"]
        est = estimates[ident]
        rows.append(
            [
                tex_escape(ident.replace("ucsf_pdgm", "UCSF").replace("utsw", "UTSW")),
                tex_escape(comparison[ident]),
                f"{est['point']:+.4f}",
                f"[{est['lower']:+.4f}, {est['upper']:+.4f}]",
                f"{member['raw_p_value']:.4f}",
                f"{member['bh_adjusted_p_value_float']:.4f}",
                "yes" if member["reject_q_0.05"] else "no",
            ]
        )
    return tabular(
        "llrrrrl",
        [
            "ID",
            "Comparison",
            "Estimate",
            "95\\% interval",
            "Raw $p$",
            "BH adj. $p$",
            "Rej.",
        ],
        rows,
    )


def segmentation_table(i10: dict[str, Any]) -> str:
    rows = []
    names = {"R2": "R2 (primary)", "R7": "R7 (global pooling)", "R8": "R8 (two-stage)"}
    for run in ("R2", "R7", "R8"):
        info = i10["runs"][run]
        dice = info["segmentation_dice"]
        channels = info["hd95"]["per_channel"]
        rows.append(
            [
                names[run],
                f3(dice["mean"]),
                f3(dice["per_channel"]["enhancing"]),
                f3(dice["per_channel"]["necrotic_core"]),
                f3(dice["per_channel"]["oedema"]),
                f"{channels['enhancing']['primary']['median']:.1f}",
                f"{channels['necrotic_core']['primary']['median']:.1f}",
                f"{channels['oedema']['primary']['median']:.1f}",
            ]
        )
    return tabular(
        "lrrrrrrr",
        [
            "Run",
            "Dice",
            "Enh.",
            "Core",
            "Oedema",
            "HD95 enh.",
            "HD95 core",
            "HD95 oed.",
        ],
        rows,
    )


def probe_table(probe: dict[str, Any]) -> str:
    test = probe["internal_test"]
    rows = []
    for label, point, boot, comparator in (
        (
            "All labelled patients",
            test["probe"],
            test["probe_bootstrap"],
            test["comparator_idh_probability"],
        ),
        (
            "IDH-mutant only",
            test["idh_mutant_only"]["probe"],
            test["idh_mutant_only"]["probe_bootstrap"],
            test["idh_mutant_only"]["comparator_idh_probability"],
        ),
    ):
        low, high = boot["auroc_95_interval"]
        rows.append(
            [
                label,
                str(point["n"]),
                str(point["n_codeleted"]),
                interval(point["auroc"], low, high),
                f3(point["auprc"]),
                f3(comparator["auroc"]),
            ]
        )
    return tabular(
        "lrrccc",
        ["Subset", "$n$", "Codel.", "Probe AUROC [95\\%]", "AUPRC", "IDH-prob. AUROC"],
        rows,
    )


def cohort_flow_table(directory: Path) -> str:
    """One table: retained and excluded counts per cohort, then each reason."""
    with (directory / "table_1.csv").open() as handle:
        counts = list(csv.DictReader(handle))
    with (directory / "table_2.csv").open() as handle:
        reasons = list(csv.DictReader(handle))

    def cohort_name(raw: str) -> str:
        return raw.replace("ucsf_pdgm", "UCSF-PDGM").replace("utsw", "UTSW-Glioma")

    names = {
        "no_imaging_available": "no imaging available",
        "overlap:brats2021": "also in BraTS 2021",
        "label:idh_unavailable": "no IDH label",
        "qc:skullstrip-over": "failed skull-strip check",
    }

    def reason_text(raw: str) -> str:
        return tex_escape(names.get(raw, raw.replace(":", " ").replace("_", " ")))

    rows: list[list[str]] = []
    for row in counts:
        rows.append(
            [
                f"\\textbf{{{cohort_name(row['cohort'])}}}",
                row["retained_patient_count"],
                row["excluded_patient_count"],
            ]
        )
        for reason in reasons:
            if reason["cohort"] == row["cohort"]:
                rows.append(
                    [f"\\quad {reason_text(reason['reason'])}", "", reason["count"]]
                )
    return tabular("lrr", ["Cohort / exclusion reason", "Retained", "Excluded"], rows)


def build(experiments: Path, flow: Path) -> dict[str, str]:
    i09 = _load(experiments / RUN / "phase09_analysis.json")
    i10 = _load(experiments / RUN / "phase10_analysis.json")
    m6 = _load(experiments / RUN / "phase09_m6_analysis.json")
    e09 = _load(experiments / EXT1 / "phase09_external_analysis.json")
    e10 = _load(experiments / EXT1 / "phase10_external_analysis.json")
    final = _load(experiments / "phase13" / "phase13_final_analysis.json")
    probe = _load(experiments / RUN / "probe_1p19q" / "probe_1p19q.json")
    return {
        "tbl_cohort_flow": cohort_flow_table(flow),
        "tbl_aurc_int": aurc_table(i09, m6),
        "tbl_aurc_ext": aurc_table(e09, None),
        "tbl_risk_int": risk_table(i09),
        "tbl_risk_ext": risk_table(e09),
        "tbl_delta_int": delta_table(i09),
        "tbl_delta_ext": delta_table(e09),
        "tbl_conformal_int": conformal_table(i09),
        "tbl_conformal_ext": conformal_table(e09),
        "tbl_monotone_int": monotone_table(i09),
        "tbl_monotone_ext": monotone_table(e09),
        "tbl_enrich_int": enrichment_table(i09),
        "tbl_enrich_ext": enrichment_table(e09),
        "tbl_family": family_table(final, i10, e10),
        "tbl_seg": segmentation_table(i10),
        "tbl_probe": probe_table(probe),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", type=Path, required=True)
    parser.add_argument("--cohort-flow", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, body in build(args.experiments, args.cohort_flow).items():
        (args.out / f"{name}.tex").write_text(body)
        print(args.out / f"{name}.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
