#src/alphaforge/portfolio/construction.py
"""Cross-sectional signal and target-weight construction."""

from __future__ import annotations

import pandas as pd

from alphaforge.research import assign_quantiles


def _weekly_rebalance_dates(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    date_frame = pd.DataFrame({"date": dates})
    calendar_week = date_frame["date"].dt.to_period("W-SUN")
    return pd.DatetimeIndex(
        date_frame.groupby(calendar_week, sort=True)["date"].max()
    )


def build_long_only_top_quantile_portfolio(
    df: pd.DataFrame,
    factor_col: str,
    n_quantiles: int = 5,
) -> pd.DataFrame:
    """Build weekly long-only equal-weight targets from the top factor quantile.

    Each calendar week's last global trading date is a rebalance decision date.
    The decision uses factor values from that date without an execution shift.
    Targets are carried forward between decisions; rows before the first decision
    have zero signal and weight.
    """

    factor_data = df.loc[:, ["date", "symbol", factor_col]].rename(
        columns={factor_col: "factor"}
    )
    global_dates = pd.DatetimeIndex(factor_data["date"].unique()).sort_values()
    symbols = pd.Index(factor_data["symbol"].unique()).sort_values()

    panel_index = pd.MultiIndex.from_product(
        [global_dates, symbols],
        names=["date", "symbol"],
    )
    result = (
        factor_data.set_index(["date", "symbol"])["factor"]
        .reindex(panel_index)
        .rename("factor")
        .reset_index()
    )

    rebalance_dates = _weekly_rebalance_dates(global_dates)
    result["is_rebalance"] = result["date"].isin(rebalance_dates)
    result["signal"] = pd.NA
    result["target_weight"] = pd.NA

    decision_rows = result.loc[result["is_rebalance"], ["date", "factor"]]
    quantiles = assign_quantiles(
        decision_rows,
        "factor",
        n_quantiles=n_quantiles,
    )
    decision_signal = quantiles.eq(n_quantiles).fillna(False).astype("int8")
    selected_count = decision_signal.groupby(decision_rows["date"]).transform(
        "sum"
    )
    decision_weight = decision_signal.div(selected_count.where(selected_count.gt(0)))

    result.loc[result["is_rebalance"], "signal"] = decision_signal
    result.loc[result["is_rebalance"], "target_weight"] = (
        decision_weight.fillna(0.0)
    )
    result[["signal", "target_weight"]] = (
        result.groupby("symbol", sort=False)[["signal", "target_weight"]]
        .ffill()
        .fillna(0.0)
    )
    result["signal"] = result["signal"].astype("int8")
    result["target_weight"] = result["target_weight"].astype(float)
    return result
