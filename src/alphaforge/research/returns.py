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
