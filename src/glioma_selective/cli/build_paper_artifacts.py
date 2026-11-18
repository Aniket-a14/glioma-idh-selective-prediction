"""Generate Phase 13 figures, tables and registry rows from verified frozen files.

Run with PYTHONPATH=src and the repository Python environment::

    python -m glioma_selective.cli.build_paper_artifacts --run-id R2

Default output is build/paper_artifacts/, never paper/. This command does not
fit temperatures, recompute intervals, apply BH, or adjudicate claims. Optional
M6 cells are read beside the R2 analysis and checked against --m6-run-id.
External analysis files must be supplied explicitly as COHORT=PATH and pass the
existing Gate E firewall before any access. Only the documented frozen Phase 09
schema is accepted; unknown schemas fail instead of guessing future keys.

Required manifests are read through paths.manifests_dir(). Every source,
including manifests and predictions, must have a matching .sha256 sidecar.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from glioma_selective.evaluation import firewall
from glioma_selective.utils import paths
from glioma_selective.visualization.abstention import abstention_figure
from glioma_selective.visualization.coverage import coverage_figure
from glioma_selective.visualization.reliability import reliability_figure
from glioma_selective.visualization.risk_coverage import (
    DIGEST_PREFIX_LENGTH,
    cohort_flow_figure,
    figure_style,
    risk_coverage_figure,
    save_figure,
)
from glioma_selective.visualization.tables import (
    Table,
    cohort_tables,
    coverage_table,
    headline_table,
    selective_tables,
    write_table,
)

DEFAULT_OUTPUT = Path("build/paper_artifacts")
REGISTRY_HEADER = "| Element | Content | Generated from | Regenerate command | Status |"
REGISTRY_SEPARATOR = "|---|---|---|---|---|"


@dataclass(frozen=True)
class FrozenInput:
    """One verified byte stream and its digest, retained for registry provenance."""

    path: Path
    payload: bytes
    digest: str

    @classmethod
    def read(cls, path: Path) -> FrozenInput:
        payload = path.read_bytes()
        sidecar = path.with_name(path.name + ".sha256")
        try:
            expected = sidecar.read_text(encoding="ascii").split()[0]
        except (OSError, UnicodeError, IndexError) as error:
            raise ValueError(
                f"missing or invalid SHA-256 sidecar: {path.name}"
            ) from error
        actual = hashlib.sha256(payload).hexdigest()
        if expected.lower() != actual:
            raise ValueError(f"SHA-256 mismatch: {path.name}")
        return cls(path, payload, actual)

    def document(self, schema: str | None = None) -> dict[str, Any]:
        value = json.loads(self.payload)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {self.path.name}")
        if schema is not None and value["schema"] != schema:
            raise ValueError(f"unsupported schema: {self.path.name}")
        return value

    def registry_source(self) -> str:
        return f"{self.path.name} sha256:{self.digest[:DIGEST_PREFIX_LENGTH]}"


def load_external_analysis(cohort: str, analysis_path: Path) -> FrozenInput:
    """No external analysis is opened or discovered implicitly, even with flag 1."""
    firewall.assert_external_eval_authorized(cohort)
    return FrozenInput.read(analysis_path)


def _run_directory(run_id: str) -> Path:
    if not run_id or Path(run_id).name != run_id or run_id in (".", ".."):
        raise ValueError("run ID must be a single directory name")
    if any(name in run_id.casefold() for name in firewall.EXTERNAL_COHORTS):
        raise ValueError("external runs require an explicit external analysis path")
    return paths.experiments_dir() / run_id


def _provenance(document: dict[str, Any], run_id: str) -> None:
    if document["provenance"]["run_id"] != run_id:
        raise ValueError("analysis run_id does not match the requested run")


def _merge_m6(document: dict[str, Any], extra: dict[str, Any], m6_run_id: str) -> None:
    if extra["provenance"]["m6_run_id"] != m6_run_id:
        raise ValueError("M6 run_id does not match --m6-run-id")
    if sorted(extra["conditions"]) != sorted(document["conditions"]):
        raise ValueError("M6 condition set differs from the main analysis")
    for condition, cell in extra["conditions"].items():
        if document["conditions"][condition]["M6"].get("absent") is not True:
            raise ValueError("M6 overlay would replace a present frozen cell")
        document["conditions"][condition]["M6"] = cell


def _prediction_frames(
    directory: Path, document: dict[str, Any], run_id: str
) -> tuple[dict[str, Any], list[FrozenInput]]:
    inputs = [FrozenInput.read(directory / "predictions.parquet")]
    frames = {}
    for condition in sorted(document["conditions"]):
        source = (
            inputs[0]
            if condition == "full"
            else FrozenInput.read(directory / "conditions" / f"{condition}.parquet")
        )
        if condition != "full":
            inputs.append(source)
        frame = pd.read_parquet(io.BytesIO(source.payload))
        if not frame["cohort"].isin(("utsw_calibration", "utsw_internal_test")).all():
            raise ValueError(
                "internal reliability input contains a non-internal cohort"
            )
        if not (frame["run_id"] == run_id).all():
            raise ValueError("prediction run_id does not match the requested run")
        if not (
            frame["checkpoint_hash"] == document["provenance"]["checkpoint_hash"]
        ).all():
            raise ValueError(
                "prediction checkpoint hash differs from the frozen analysis"
            )
        if not (frame["modality_condition"] == condition).all():
            raise ValueError("prediction file contains another modality condition")
        frames[condition] = frame
    return frames, inputs


def _registry_row(
    element: str, files: tuple[Path, ...], sources: list[FrozenInput], command: str
) -> str:
    content = ", ".join(f"`{path.as_posix()}`" for path in files)
    provenance = "; ".join(source.registry_source() for source in sources)
    # Escape Markdown table separators in user-supplied output paths/commands.
    cells = (element, content, provenance, f"`{command}`", "GENERATED")
    return (
        "| "
        + " | ".join(cell.replace("|", "&#124;").replace("\n", " ") for cell in cells)
        + " |"
    )


def build_paper_artifacts(
    run_id: str,
    *,
    m6_run_id: str | None = None,
    out_dir: Path = DEFAULT_OUTPUT,
    external_analyses: tuple[tuple[str, Path], ...] = (),
) -> Path:
    """Build internal artifacts and explicitly authorized external analysis panels.

    Raises on missing keys or sidecars, unknown schemas, provenance mismatch, or
    SI-14 violations. Claims are copied to CLAIMS.json without re-evaluation.
    """
    repository = Path(__file__).resolve().parents[3]
    if out_dir.resolve().is_relative_to((repository / "paper").resolve()):
        raise ValueError("paper/ is human-owned; choose another output directory")
    # Check external authorization before even opening the internal inputs.
    externals = [
        (cohort, load_external_analysis(cohort, path))
        for cohort, path in external_analyses
    ]
    if len({cohort for cohort, _ in externals}) != len(externals):
        raise ValueError("duplicate external cohort")
    directory = _run_directory(run_id)
    phase09_source = FrozenInput.read(directory / "phase09_analysis.json")
    phase10_source = FrozenInput.read(directory / "phase10_analysis.json")
    phase09 = copy.deepcopy(phase09_source.document("phase09_analysis.v1"))
    phase10 = phase10_source.document("phase10_analysis.v1")
    _provenance(phase09, run_id)
    _provenance(phase10, run_id)
    if sorted(phase09["conditions"]) != sorted(phase09["provenance"]["conditions"]):
        raise ValueError("condition panels differ from frozen provenance")
    if sorted(phase09["conformal"]) != sorted(phase09["conditions"]):
        raise ValueError("conformal condition panels differ from selective results")
    if (
        phase09["provenance"]["checkpoint_hash"]
        != phase10["provenance"]["checkpoint_hash"]
    ):
        raise ValueError("Phase 09 and Phase 10 checkpoint hashes differ")
    selective_sources = [phase09_source]
    if m6_run_id is not None:
        _run_directory(m6_run_id)  # Validate the ID; do not open R1 predictions.
        m6_source = FrozenInput.read(directory / "phase09_m6_analysis.json")
        m6 = m6_source.document("phase09_m6_analysis.v1")
        _provenance(m6, run_id)
        _merge_m6(phase09, m6, m6_run_id)
        selective_sources.append(m6_source)
    cohort_source = FrozenInput.read(
        paths.manifests_dir() / "cohort_manifest_post_qc.json"
    )
    exclusion_source = FrozenInput.read(
        paths.manifests_dir() / "exclusion_manifest_post_qc.json"
    )
    cohort, exclusions = cohort_source.document(), exclusion_source.document()
    frames, predictions = _prediction_frames(directory, phase09, run_id)
    command_parts = [
        sys.executable,
        "-m",
        "glioma_selective.cli.build_paper_artifacts",
        "--run-id",
        run_id,
    ]
    if m6_run_id is not None:
        command_parts.extend(("--m6-run-id", m6_run_id))
    command_parts.extend(("--out-dir", str(out_dir)))
    for name, source in externals:
        command_parts.extend(("--external-analysis", f"{name}={source.path}"))
    command = "PYTHONPATH=src " + shlex.join(command_parts)
    registry = [REGISTRY_HEADER, REGISTRY_SEPARATOR]
    one, two = cohort_tables(cohort, exclusions)
    three, six = selective_tables(phase09, "utsw")
    tables = [
        one,
        two,
        three,
        coverage_table(phase09, "utsw"),
        headline_table(phase10, "utsw"),
        six,
    ]
    sources = [
        [cohort_source],
        [exclusion_source],
        selective_sources,
        [phase09_source],
        [phase10_source],
        selective_sources,
    ]
    claims = {"utsw": phase09["claims"]}
    external_documents = []
    for name, source in externals:
        doc = source.document("phase09_analysis.v1")
        external_documents.append((name, source, doc))
        claims[name] = doc["claims"]
        ext_three, ext_six = selective_tables(doc, name)
        for index, extra in (
            (2, ext_three),
            (3, coverage_table(doc, name)),
            (5, ext_six),
        ):
            table = tables[index]
            tables[index] = Table(table.caption, table.columns, table.rows + extra.rows)
            sources[index] = [*sources[index], source]
    with figure_style():
        figures = [
            cohort_flow_figure(cohort, exclusions),
            risk_coverage_figure(phase09),
            coverage_figure(phase09),
            reliability_figure(
                frames, phase09["provenance"]["full_temperature"], "utsw_internal_test"
            ),
            abstention_figure(phase09),
        ]
        figure_sources = [
            [cohort_source, exclusion_source],
            selective_sources,
            [phase09_source],
            [phase09_source, *predictions],
            selective_sources,
        ]
        extra_figures = [
            (name, source, number, factory(doc))
            for name, source, doc in external_documents
            for number, factory in (
                (2, risk_coverage_figure),
                (3, coverage_figure),
                (5, abstention_figure),
            )
        ]
        out_dir.mkdir(parents=True, exist_ok=True)
        files: tuple[Path, ...]
        for number, (table, inputs) in enumerate(
            zip(tables, sources, strict=True), start=1
        ):
            files = write_table(table, out_dir / f"table_{number}")
            registry.append(_registry_row(f"Table {number}", files, inputs, command))
        for number, ((fig, caption), inputs) in enumerate(
            zip(figures, figure_sources, strict=True), start=1
        ):
            files = save_figure(fig, caption, out_dir / f"fig_{number}")
            registry.append(_registry_row(f"Fig {number}", files, inputs, command))
        for name, source, number, (fig, caption) in extra_figures:
            files = save_figure(
                fig, f"{name}: {caption}", out_dir / f"fig_{number}_{name}"
            )
            registry.append(
                _registry_row(f"Fig {number} ({name})", files, [source], command)
            )
    (out_dir / "CLAIMS.json").write_text(
        json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "REGISTRY_ROWS.md").write_text(
        "\n".join(registry) + "\n", encoding="utf-8"
    )
    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--m6-run-id")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--external-analysis", action="append", default=[], metavar="COHORT=PATH"
    )
    args = parser.parse_args(argv)
    external = []
    for value in args.external_analysis:
        name, separator, path = value.partition("=")
        if not separator or not path:
            parser.error("--external-analysis requires COHORT=PATH")
        external.append((name, Path(path)))
    try:
        build_paper_artifacts(
            args.run_id,
            m6_run_id=args.m6_run_id,
            out_dir=args.out_dir,
            external_analyses=tuple(external),
        )
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"build_paper_artifacts: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
