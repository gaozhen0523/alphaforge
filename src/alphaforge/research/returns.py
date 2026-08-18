#src/alphaforge/research/returns.py
"""Forward returns for factor research."""

from __future__ import annotations

import pandas as pd


def compute_forward_return(
    df: pd.DataFrame,
    horizon: int = 1,
    price_col: str = "close",
) -> pd.Series:
    """Return each symbol's price return over the next available observations."""

    if horizon < 1:
        raise ValueError("horizon must be positive")

    ordered = df.loc[:, ["date", "symbol", price_col]].copy()
    ordered["_position"] = range(len(df))
    ordered = ordered.sort_values(["symbol", "date"], kind="mergesort")

    future_price = ordered.groupby("symbol", sort=False)[price_col].shift(-horizon)
    values = future_price / ordered[price_col] - 1.0

    result = pd.Series(values.to_numpy(), index=ordered["_position"]).sort_index()
    result.index = df.index
    result.name = "forward_return"
    return result


def compute_decay_return(
    df: pd.DataFrame,
    lag: int = 0,
    price_col: str = "close",
) -> pd.Series:
    """Return the one-observation price move starting ``lag`` observations ahead.

    The result at a formation row ``t`` is
    ``price(t + lag + 1) / price(t + lag) - 1`` within the same symbol's
    available observations. The series remains aligned to the formation row.
    """

    if lag < 0:
        raise ValueError("lag must be non-negative")
    if lag == 0:
        result = compute_forward_return(df, horizon=1, price_col=price_col)
        return result.rename("decay_return")

    ordered = df.loc[:, ["date", "symbol", price_col]].copy()
    ordered["_position"] = range(len(df))
    ordered = ordered.sort_values(["symbol", "date"], kind="mergesort")

    grouped_price = ordered.groupby("symbol", sort=False)[price_col]
    interval_start = grouped_price.shift(-lag)
    interval_end = grouped_price.shift(-(lag + 1))
    values = interval_end / interval_start - 1.0

    result = pd.Series(values.to_numpy(), index=ordered["_position"]).sort_index()
    result.index = df.index
    result.name = "decay_return"
    return result
