# C-019 — Publication figure helpers: reliability diagram and risk-coverage plot

Assigned to ShantanuTripathi2745. Branch `contrib/ShantanuTripathi2745/figure-helpers`. Read-only for you; the Research
Lead edits this file.

## Why this exists

The paper's main figures are reliability diagrams (Phase 07) and risk-coverage curves (Phase 09). Every figure has to be
regenerable from frozen prediction artifacts, look the same across the paper, and be traceable to the numbers it
shows. Writing the plotting code once, now, with a fixed style, means Phase 07 and Phase 09 reuse it instead of each
session inventing its own. `src/glioma_selective/visualization/` is currently empty (`.gitkeep`).

## Files (nothing else may be touched)

- `src/glioma_selective/visualization/style.py` (new)
- `src/glioma_selective/visualization/reliability.py` (new)
- `src/glioma_selective/visualization/risk_coverage.py` (new)
- `src/glioma_selective/visualization/__init__.py` (edit: export the public functions only)
- `tests/unit/test_visualization_helpers.py` (new)

## Rules that come from the repository

- **These functions take plain numbers and plot them. They do no metric computation.** Do not compute ECE, risk,
  coverage or a confidence interval inside them; receive already-computed sequences. Do not import from
  `glioma_selective.evaluation`, `selective`, `calibration`, `statistics` or `uncertainty` (metric code must never
  depend on plotting code, and the reverse is kept out too so the two stay independent; `scripts/check_invariants.py`
  enforces the first direction for `evaluation/` only).
- Use `matplotlib.figure.Figure` directly, not `matplotlib.pyplot`, so there is no global state and no display is
  needed (the tests run headless on CI).
- The package must pass `mypy` (the project config is strict: full type hints on everything), `ruff`, and
  `radon` (cyclomatic complexity at most 10 per function). Run `pre-commit run --all-files`, `mypy`, and
  `pytest tests/unit -q` before pushing.
- No new dependency. numpy and matplotlib are already installed; do not add pandas or seaborn.
- No real data and no path under `data/` or `artifacts/`. Tests use tiny hand-written sequences and `tmp_path`.

## What to build

1. `style.py`
   - `PALETTE`: the Okabe-Ito colour-blind-safe palette as a tuple of hex strings, in a fixed documented order.
   - `SINGLE_COLUMN_INCHES = (3.4, 2.6)`, `DOUBLE_COLUMN_INCHES = (7.0, 3.2)`.
   - `apply_style(figure)`: sets font sizes (tick 8, label 9, title 9, legend 8), line widths, grid off, top and right
     spines off, on the figure passed in (do not change global rcParams).
   - `save_figure(figure, stem, data, formats=("png", "pdf"))`: writes `<stem>.png` (300 dpi) and `<stem>.pdf`, and a
     sidecar `<stem>.json` holding `data` (the exact numbers plotted, plus the function name and its arguments) with
     sorted keys and a fixed indent. Two calls with the same input must produce byte-identical `.json` and `.png`
     files; pass `metadata={"Software": None}` for the PNG and `metadata={"CreationDate": None, "ModDate": None}` for the PDF (the
     Research Lead checked that this gives identical bytes on two saves with matplotlib 3.11.2). Refuse (raise `FileExistsError`)
     to overwrite an existing file unless `overwrite=True`. Returns the list of paths written.
2. `reliability.py`: `plot_reliability_diagram(series, *, title=None) -> Figure`. `series` is a list of dicts, each
   with `label` and per-bin sequences `mean_confidence`, `observed`, `count` (a bin with `count == 0` has `None`
   values and is not drawn), so a raw and a temperature-scaled curve can share one diagram. Draws the identity
   diagonal, one marker-and-line series per entry (colours from `PALETTE` in order), a legend, and a small bar strip
   of the bin counts of the **first** series under the plot (a second axis). Axis labels "Mean predicted probability"
   and "Observed fraction", both axes fixed to [0, 1]. `ValueError` for an empty list, unequal sequence lengths within
   a series, and any value outside [0, 1].
3. `risk_coverage.py`: `plot_risk_coverage(curves, *, title=None) -> Figure`. `curves` is a list of dicts with `label`,
   `coverage`, `risk`, and optional `risk_lower`, `risk_upper` (a shaded band). Draws each curve as a step-free line
   with markers off, x axis "Coverage" fixed to [0, 1], y axis "Selective risk" starting at 0, a legend, and colours
   from `PALETTE` in order. If `risk_lower` is given `risk_upper` must be too (`ValueError` otherwise). `ValueError` also for
   coverage outside [0, 1], unequal lengths, and coverage that is not strictly increasing.

## Tests required (assert on data, never on pixels)

- The drawn line data equals the input (read it from `line.get_xdata()` and `get_ydata()`); the diagonal is
  present; axis limits and labels are as specified; empty bins are skipped without an error.
- The shaded band exists when bounds are given and is absent when they are not.
- Every `ValueError` case above.
- `save_figure`: files exist; the `.json` round-trips and contains the plotted numbers; calling twice with the same
  input gives byte-identical `.json` and `.png`; a second call without `overwrite=True` raises `FileExistsError`;
  nothing is written outside `tmp_path`.
- Importing the modules does not create a display, open a window or change `matplotlib.rcParams`.
- One test that fails if `matplotlib.pyplot` is imported by these modules (check `sys.modules` in a subprocess).

## Milestones

The dates are deadlines, not start dates; starting this weekend is fine. Finish your earlier rows first (ascending ID order).

1. (by Wed 2026-09-23, open a **draft** pull request) `style.py` and `save_figure` with tests.
2. (by Thu 2026-09-24) `plot_reliability_diagram` with tests.
3. (by Fri 2026-09-25, mark ready) `plot_risk_coverage`, the `__init__` exports, all gates, and the PR text with the three
   sample images (generated from made-up numbers in `tmp_path`, attached to the pull request as images, never committed).

## Not allowed

Style decisions beyond the list above (colours other than the palette, fonts, extra chart types): the Research Lead
will review the sample images and decide. If something here is ambiguous, list it under "Open questions" in the pull
request and implement it exactly as written. Do not touch `paper/`, `configs/`, `scripts/`, or any file not listed.
