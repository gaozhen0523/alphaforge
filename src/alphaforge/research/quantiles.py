"""Cross-sectional factor quantile assignment."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .ranking import cross_sectional_rank


def assign_quantiles(
    df: pd.DataFrame,
    factor_col: str,
    n_quantiles: int = 5,
) -> pd.Series:
    """Assign factor percentile ranks to quantiles independently by date."""

    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2")

    ranks = cross_sectional_rank(df, factor_col)
    quantiles = np.ceil(ranks * n_quantiles).astype("Int64")
    quantiles.name = "quantile"
    return quantiles


def compute_quantile_returns(
    df: pd.DataFrame,
    return_col: str = "forward_return",
    quantile_col: str = "quantile",
    n_quantiles: int = 5,
) -> pd.DataFrame:
    """Return daily equal-weight mean forward returns by quantile."""

    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2")

    result = (
        df.groupby(["date", quantile_col], sort=True)[return_col]
        .mean()
        .unstack(quantile_col)
        .reindex(columns=range(1, n_quantiles + 1))
        .sort_index()
    )
    result.columns.name = "quantile"
    return result


def summarize_quantile_returns(
    quantile_returns: pd.DataFrame,
) -> pd.Series:
    """Summarize mean daily returns and the top-minus-bottom mean spread."""

    summary = quantile_returns.mean()
    summary.index = [f"q{quantile}_mean" for quantile in quantile_returns.columns]

    bottom_quantile = quantile_returns.columns.min()
    top_quantile = quantile_returns.columns.max()
    summary.loc["top_minus_bottom"] = (
        summary[f"q{top_quantile}_mean"]
        - summary[f"q{bottom_quantile}_mean"]
    )
    return summary
