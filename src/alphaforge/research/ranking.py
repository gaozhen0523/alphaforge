#src/alphaforge/research/ranking.py
"""Cross-sectional factor ranking."""

from __future__ import annotations

import pandas as pd


def cross_sectional_rank(
    df: pd.DataFrame,
    factor_col: str,
) -> pd.Series:
    """Return percentile ranks of a factor independently within each date."""

    return df.groupby("date", sort=False)[factor_col].rank(pct=True)
