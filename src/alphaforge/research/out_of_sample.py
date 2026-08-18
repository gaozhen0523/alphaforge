#src/alphaforge/research/out_of_sample.py
"""Chronological out-of-sample factor research."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from alphaforge.periods import OOS_PERIODS, assign_oos_period

from .ic import compute_daily_ic, summarize_ic
from .quantiles import (
    assign_quantiles,
    compute_quantile_returns,
    summarize_quantile_returns,
)
from .returns import compute_forward_return

def compute_period_forward_return(
    df: pd.DataFrame,
    horizon: int = 1,
    price_col: str = "close",
) -> pd.Series:
    """Compute forward returns without crossing a research-period boundary."""

    period = assign_oos_period(df["date"])
    result = pd.Series(np.nan, index=df.index, name="forward_return")
    for period_name, _, _ in OOS_PERIODS:
        in_period = period.eq(period_name)
        period_data = df.loc[in_period]
        result.loc[in_period] = compute_forward_return(
            period_data,
            horizon=horizon,
            price_col=price_col,
        )
    return result


def run_out_of_sample_research(
    df: pd.DataFrame,
    factor_cols: Sequence[str],
    horizon: int = 1,
    n_quantiles: int = 5,
    price_col: str = "close",
    min_obs: int = 5,
) -> pd.DataFrame:
    """Compare frozen factor definitions across the fixed IS/OOS periods.

    Factor values are expected to have been computed on full chronological
    history. Forward-return labels are then computed within each period so a
    research label never consumes a price from the following period.
    """

    period = assign_oos_period(df["date"])
    forward_return = compute_period_forward_return(
        df,
        horizon=horizon,
        price_col=price_col,
    )
    rows = []
    for factor_col in factor_cols:
        for period_name, _, _ in OOS_PERIODS:
            in_period = period.eq(period_name)
            research_frame = df.loc[in_period, ["date", factor_col]].copy()
            research_frame["forward_return"] = forward_return.loc[in_period]

            daily_ic = compute_daily_ic(
                research_frame,
                factor_col,
                min_obs=min_obs,
            )
            ic_summary = summarize_ic(daily_ic)
            research_frame["quantile"] = assign_quantiles(
                research_frame,
                factor_col,
                n_quantiles=n_quantiles,
            )
            quantile_returns = compute_quantile_returns(
                research_frame,
                n_quantiles=n_quantiles,
            )
            quantile_summary = summarize_quantile_returns(quantile_returns)

            q1_mean = quantile_summary["q1_mean"]
            q5_mean = quantile_summary[f"q{n_quantiles}_mean"]
            rows.append(
                {
                    "factor": factor_col,
                    "period": period_name,
                    "valid_ic_days": int(ic_summary["n_obs"]),
                    "mean_ic": ic_summary["mean_ic"],
                    "icir": ic_summary["icir"],
                    "q1_mean": q1_mean,
                    "q5_mean": q5_mean,
                    "q5_minus_q1": q5_mean - q1_mean,
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "factor",
            "period",
            "valid_ic_days",
            "mean_ic",
            "icir",
            "q1_mean",
            "q5_mean",
            "q5_minus_q1",
        ],
    )
