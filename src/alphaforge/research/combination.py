#src/alphaforge/research/combination.py
"""Simple cross-sectional factor combinations."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from .ranking import cross_sectional_rank


def cross_sectional_zscore(
    df: pd.DataFrame,
    factor_col: str,
) -> pd.Series:
    """Return population z-scores independently within each date."""

    grouped = df.groupby("date", sort=False)[factor_col]
    mean = grouped.transform("mean")
    std = grouped.transform("std", ddof=0)
    result = (df[factor_col] - mean) / std.where(std.ne(0.0))
    return result.rename(f"{factor_col}_zscore")


def _validate_directions(factor_directions: Mapping[str, int]) -> None:
    if not factor_directions:
        raise ValueError("factor_directions must not be empty")
    if any(direction not in (-1, 1) for direction in factor_directions.values()):
        raise ValueError("factor directions must be +1 or -1")


def combine_factors_by_rank(
    df: pd.DataFrame,
    factor_directions: Mapping[str, int],
) -> pd.Series:
    """Average equally weighted, direction-aligned cross-sectional ranks.

    A row is valid only when every normalized factor is valid.
    """

    _validate_directions(factor_directions)
    oriented = {}
    for factor_col, direction in factor_directions.items():
        rank = cross_sectional_rank(df, factor_col)
        oriented[factor_col] = rank if direction == 1 else 1.0 - rank

    return pd.DataFrame(oriented).mean(axis=1, skipna=False).rename(
        "combined_rank"
    )


def combine_factors_by_zscore(
    df: pd.DataFrame,
    factor_directions: Mapping[str, int],
) -> pd.Series:
    """Average equally weighted, direction-aligned cross-sectional z-scores.

    A row is valid only when every normalized factor is valid.
    """

    _validate_directions(factor_directions)
    oriented = {
        factor_col: direction * cross_sectional_zscore(df, factor_col)
        for factor_col, direction in factor_directions.items()
    }
    return pd.DataFrame(oriented).mean(axis=1, skipna=False).rename(
        "combined_zscore"
    )
