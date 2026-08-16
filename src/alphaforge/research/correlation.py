"""Cross-sectional factor correlation analysis."""

from __future__ import annotations

import pandas as pd


def compute_factor_correlation(
    df: pd.DataFrame,
    factor_cols: list[str],
    min_obs: int = 5,
) -> pd.DataFrame:
    """Return the equal-weight mean of daily Spearman factor correlations."""

    if min_obs < 2:
        raise ValueError("min_obs must be at least 2")

    daily_correlations = [
        group.loc[:, factor_cols].corr(
            method="spearman",
            min_periods=min_obs,
        )
        for _, group in df.groupby("date", sort=False)
    ]
    result = (
        pd.concat(daily_correlations)
        .groupby(level=0, sort=False)
        .mean()
    )
    return result.reindex(index=factor_cols, columns=factor_cols)
