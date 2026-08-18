#src/alphaforge/data/quality.py
"""Lightweight diagnostics for an observed canonical OHLCV panel."""

from __future__ import annotations

import pandas as pd

from .schema import _invalid_observation_mask, _require_columns


def summarize_ohlcv_quality(frame: pd.DataFrame) -> dict[str, int | float]:
    """Summarize coverage and row-level quality without changing ``frame``.

    Coverage uses the Cartesian product of all observed global dates and all
    observed symbols. Missing rows between a symbol's first and last observed
    global dates are internal; all other missing rows are boundary missing.
    These categories describe location only and do not infer economic causes.

    ``duplicate_pairs`` counts unique keys that occur more than once.
    ``invalid_observations`` counts rows with at least one numeric or OHLC
    violation; duplicate keys are reported separately. The function requires
    canonical columns but deliberately does not run hard validation first.
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    _require_columns(frame)

    keys = frame.loc[:, ["date", "symbol"]]
    unique_keys = keys.drop_duplicates()
    rows = len(frame)
    symbols = unique_keys["symbol"].nunique()
    global_dates = unique_keys["date"].nunique()
    expected_panel_rows = symbols * global_dates
    observed_unique_rows = len(unique_keys)
    missing_observations = expected_panel_rows - observed_unique_rows
    duplicate_pairs = int(keys.value_counts(sort=False).gt(1).sum())

    internal_missing_observations = 0
    if observed_unique_rows:
        ordered_dates = pd.Index(unique_keys["date"].unique()).sort_values()
        date_position = pd.Series(range(len(ordered_dates)), index=ordered_dates)
        positioned = unique_keys.assign(
            _date_position=unique_keys["date"].map(date_position)
        )
        spans = positioned.groupby("symbol", observed=True)["_date_position"].agg(
            ["min", "max", "count"]
        )
        internal_missing_observations = int(
            (spans["max"] - spans["min"] + 1 - spans["count"]).sum()
        )

    boundary_missing_observations = (
        missing_observations - internal_missing_observations
    )
    coverage_ratio = (
        observed_unique_rows / expected_panel_rows
        if expected_panel_rows
        else float("nan")
    )

    return {
        "rows": rows,
        "symbols": symbols,
        "global_dates": global_dates,
        "expected_panel_rows": expected_panel_rows,
        "observed_unique_rows": observed_unique_rows,
        "missing_observations": missing_observations,
        "coverage_ratio": coverage_ratio,
        "duplicate_pairs": duplicate_pairs,
        "invalid_observations": int(_invalid_observation_mask(frame).sum()),
        "internal_missing_observations": internal_missing_observations,
        "boundary_missing_observations": boundary_missing_observations,
    }
