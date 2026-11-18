"""Write paper/generated/numbers.tex: every number in the manuscript text, as macros.

Phase 14 rule: no hand-transcribed numbers. The manuscript calls ``\\Name`` and this
script fills it from the frozen aggregate files (Phase 09/10 internal and external
analyses, the Phase 13 final analysis) and, for the mutant counts only, the label
column of two frozen prediction files (counts, no patient rows). It never refits or
recomputes a statistic, and reads no dataset label file.

    PYTHONPATH=src:. python scripts/build_paper_numbers.py \
        --experiments /Volumes/Research_2/artifacts/experiments \
        --out paper/generated/numbers.tex
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

RUN = "01M46999FB083AX4WW0067YM13"
EXT1 = "external_frozen/ucsf_pdgm/ucsf_pdgm_gate_e_20261118"
CONDITIONS = {
    "Full": "full",
    "DropTone": "drop_t1",
    "DropTonece": "drop_t1ce",
    "DropTtwo": "drop_t2",
    "DropFlair": "drop_flair",
    "CeFlair": "t1ce_flair_only",
}
COVERAGES = {"05": "0.5", "06": "0.6", "07": "0.7", "08": "0.8", "09": "0.9"}
ALPHAS = {"Alphafive": "0.05", "Alphaten": "0.1", "Alphatwenty": "0.2"}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _get(document: Any, dotted: str) -> Any:
    for key in dotted.split("."):
        document = document[key]
    return document


def _fmt(value: Any, digits: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return str(value)
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def _positives(path: Path, cohort: str | None) -> tuple[int, int]:
    frame = pd.read_parquet(path)
    if cohort is not None:
        frame = frame[frame["cohort"] == cohort]
    return int(frame["label"].sum()), len(frame)


def build(experiments: Path) -> dict[str, str]:
    i09 = _load(experiments / RUN / "phase09_analysis.json")
    i10 = _load(experiments / RUN / "phase10_analysis.json")
    e09 = _load(experiments / EXT1 / "phase09_external_analysis.json")
    e10 = _load(experiments / EXT1 / "phase10_external_analysis.json")
    final = _load(experiments / "phase13" / "phase13_final_analysis.json")
    m6 = _load(experiments / RUN / "phase09_m6_analysis.json")
    probe = _load(experiments / RUN / "probe_1p19q" / "probe_1p19q.json")
    out: dict[str, str] = {}

    pos_i, n_i = _positives(
        experiments / RUN / "conditions" / "full.parquet", "utsw_internal_test"
    )
    pos_e, n_e = _positives(experiments / EXT1 / "primary_seed0" / "full.parquet", None)
    out |= {
        "NInt": str(n_i),
        "NIntPos": str(pos_i),
        "NExt": str(n_e),
        "NExtPos": str(pos_e),
        "PrevInt": _fmt(pos_i / n_i, 3),
        "PrevExt": _fmt(pos_e / n_e, 3),
        "Temperature": _fmt(i09["provenance"]["full_temperature"], 3),
        "BootDraws": str(i09["results_summary"]["iterations"]),
        "PermDraws": str(i09["results_summary"]["permutations"]),
        "FamilySize": str(final["family"]["size"]),
        "FamilyRejected": str(final["family"]["n_rejected"]),
    }
    for prefix, d09, d10 in (("Int", i09, i10), ("Ext", e09, e10)):
        for run in ("R2", "R7", "R8"):
            r = d10["runs"][run]
            tag = f"{prefix}{run}"
            out[f"{tag}Auroc"] = _fmt(r["auroc"]["point"], 3)
            out[f"{tag}Aurc"] = _fmt(r["aurc_mean_over_cutoffs"]["point"], 3)
            out[f"{tag}Ece"] = _fmt(r["calibration"]["M2"]["ece"]["point"], 3)
            out[f"{tag}Brier"] = _fmt(r["calibration"]["M2"]["brier"]["point"], 3)
        r2 = d10["runs"]["R2"]
        lo, hi = r2["auroc"]["hanley_mcneil_95_interval"].values()
        out[f"{prefix}AurocLo"] = _fmt(lo, 3)
        out[f"{prefix}AurocHi"] = _fmt(hi, 3)
        for kind, key in (("M1", "M1"), ("M2", "M2")):
            cal = r2["calibration"][key]
            out[f"{prefix}Ece{kind}"] = _fmt(cal["ece"]["point"], 3)
            out[f"{prefix}Ece{kind}Lo"] = _fmt(
                cal["ece"]["bootstrap_95_interval"]["lower"], 3
            )
            out[f"{prefix}Ece{kind}Hi"] = _fmt(
                cal["ece"]["bootstrap_95_interval"]["upper"], 3
            )
            out[f"{prefix}Brier{kind}"] = _fmt(cal["brier"]["point"], 3)
        out[f"{prefix}AurcLo"] = _fmt(
            r2["aurc_mean_over_cutoffs"]["bootstrap_95_interval"]["lower"], 3
        )
        out[f"{prefix}AurcHi"] = _fmt(
            r2["aurc_mean_over_cutoffs"]["bootstrap_95_interval"]["upper"], 3
        )
        for tag, level in COVERAGES.items():
            out[f"{prefix}Risk{tag}"] = _fmt(
                r2["selective_risk_at_coverage"][level]["point"], 3
            )
        for name, cond in CONDITIONS.items():
            cell = d09["conditions"][cond]["M2"]
            out[f"{prefix}Always{name}"] = _fmt(cell["always_predict_risk"], 3)
            out[f"{prefix}Aurc{name}"] = _fmt(cell["aurc_mean_over_cutoffs"], 3)
        out[f"{prefix}Oracle"] = _fmt(d09["conditions"]["full"]["M2"]["oracle_aurc"], 3)
        for label, key in (
            ("Alphafive", "0.05"),
            ("Alphaten", "0.1"),
            ("Alphatwenty", "0.2"),
        ):
            cell = d09["conformal"]["full"]["carried_over"][key]
            out[f"{prefix}Cov{label}"] = _fmt(cell["empirical_coverage"], 3)
            out[f"{prefix}Abst{label}"] = _fmt(cell["abstention_rate"], 3)
            out[f"{prefix}Empty{label}"] = str(cell["empty_count"])
            out[f"{prefix}Half{label}"] = _fmt(
                cell["coverage_deviation_bootstrap"]["half_width"], 3
            )
        for name, cond in CONDITIONS.items():
            cell = d09["conformal"][cond]["carried_over"]["0.05"]
            out[f"{prefix}HalfAlphafive{name}"] = _fmt(
                cell["coverage_deviation_bootstrap"]["half_width"], 3
            )
    for index, tag in enumerate(COVERAGES):
        point = e09["claims"]["C3"]["full"]["numbers"]["points"][index]
        upper = e09["claims"]["C3"]["full"]["numbers"]["upper_95_limits"][index]
        out[f"CThreeDelta{tag}"] = _fmt(point, 3)
        out[f"CThreeUpper{tag}"] = _fmt(upper, 3)
        out[f"COneDelta{tag}"] = _fmt(
            i09["claims"]["C1"]["full"]["numbers"]["points"][index], 3
        )
    for claim, entry in final["claims"].items():
        out[f"Status{claim}Int"] = entry["internal"]
        out[f"Status{claim}Ext"] = (
            entry["external"] if entry["external"] else "not applicable"
        )
    out["StatusCThreeWorst"] = final["claims"]["C3"]["external_worst_over_conditions"]
    members = {row["id"]: row for row in final["family"]["members"]}
    for ident, row in members.items():
        key = ident.replace("utsw:", "FamU").replace("ucsf_pdgm:", "FamX")
        out[f"{key}Adj"] = _fmt(row["bh_adjusted_p_value_float"], 3)
    ablation = e10["confirmatory"]
    out["ExtEOneDiff"] = _fmt(ablation["E1"]["point"], 3)
    out["ExtETwoDiff"] = _fmt(ablation["E2"]["point"], 3)
    out["ExtEThreeDiff"] = _fmt(ablation["E3"]["point"], 3)
    out["ExtEFourDiff"] = _fmt(ablation["E4"]["point"], 3)
    out["ExtDTwoDiff"] = _fmt(e10["confirmatory"]["D2"]["point"], 4)
    out["ExtDTwoAbs"] = _fmt(abs(e10["confirmatory"]["D2"]["point"]), 4)
    out["ExtCOneDiff"] = _fmt(e10["confirmatory"]["C1"]["point"], 3)
    out["ExtCOneLo"] = _fmt(e10["confirmatory"]["C1"]["lower"], 3)
    out["ExtCOneHi"] = _fmt(e10["confirmatory"]["C1"]["upper"], 3)

    for prefix, d09 in (("Int", i09), ("Ext", e09)):
        for name, cond in CONDITIONS.items():
            cell = d09["conditions"][cond]
            for mech in ("M1", "M2", "M3", "M4", "M5"):
                out[f"{prefix}Aurc{mech}{name}"] = _fmt(
                    cell[mech]["aurc_mean_over_cutoffs"], 3
                )
            six = cell.get("M6", {})
            if "aurc_mean_over_cutoffs" not in six:
                six = m6["conditions"][cond]
            out[f"{prefix}AurcMSix{name}"] = _fmt(six["aurc_mean_over_cutoffs"], 3)
        for label, key in ALPHAS.items():
            carried = d09["conformal"]["full"]["carried_over"][key]
            refit = d09["conformal"]["full"]["refit"][key]
            out[f"{prefix}CalCov{label}"] = _fmt(
                carried["calibration_empirical_coverage"], 3
            )
            out[f"{prefix}Quant{label}"] = _fmt(carried["quantile"], 3)
            out[f"{prefix}RefitCov{label}"] = _fmt(refit["empirical_coverage"], 3)
            out[f"{prefix}SingleTrue{label}"] = _fmt(
                carried["singleton_true_label_fraction"], 3
            )
            out[f"{prefix}Full{label}"] = str(carried["full_count"])
    for run in ("R2", "R7", "R8"):
        info = i10["runs"][run]
        out[f"Dice{run}"] = _fmt(info["segmentation_dice"]["mean"], 3)
        for channel, tag in (
            ("enhancing", "Enh"),
            ("necrotic_core", "Core"),
            ("oedema", "Oed"),
        ):
            out[f"Dice{tag}{run}"] = _fmt(
                info["segmentation_dice"]["per_channel"][channel], 3
            )
            summary = info["hd95"]["per_channel"][channel]["primary"]
            out[f"Hd{tag}{run}"] = _fmt(summary["median"], 1)
            out[f"HdN{tag}{run}"] = str(summary["n_evaluable"])
    test = probe["internal_test"]
    out["ProbeTrainN"] = str(probe["train"]["n"])
    out["ProbeTrainCodel"] = str(probe["train"]["n_codeleted"])
    out["ProbeN"] = str(test["probe"]["n"])
    out["ProbeCodel"] = str(test["probe"]["n_codeleted"])
    out["ProbeAuroc"] = _fmt(test["probe"]["auroc"], 3)
    out["ProbeAurocLo"] = _fmt(test["probe_bootstrap"]["auroc_95_interval"][0], 3)
    out["ProbeAurocHi"] = _fmt(test["probe_bootstrap"]["auroc_95_interval"][1], 3)
    out["ProbeIdhAuroc"] = _fmt(test["comparator_idh_probability"]["auroc"], 3)
    mutant = test["idh_mutant_only"]
    out["ProbeMutN"] = str(mutant["probe"]["n"])
    out["ProbeMutAuroc"] = _fmt(mutant["probe"]["auroc"], 3)
    out["ProbeMutAurocLo"] = _fmt(mutant["probe_bootstrap"]["auroc_95_interval"][0], 3)
    out["ProbeMutAurocHi"] = _fmt(mutant["probe_bootstrap"]["auroc_95_interval"][1], 3)
    out["ProbeMutIdhAuroc"] = _fmt(mutant["comparator_idh_probability"]["auroc"], 3)
    return out


DIGITS = dict(
    zip(
        "0123456789",
        "Zero One Two Three Four Five Six Seven Eight Nine".split(),
        strict=True,
    )
)


def _macro(name: str) -> str:
    """TeX control-sequence names are letters only: spell digits out (R2 -> RTwo)."""
    return "".join(DIGITS.get(char, char) for char in name)


def render(values: dict[str, str]) -> str:
    lines = ["% Generated by scripts/build_paper_numbers.py. Do not edit by hand."]
    for name in sorted(values, key=_macro):
        lines.append(f"\\newcommand{{\\num{_macro(name)}}}{{{values[name]}}}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(build(args.experiments)))
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
