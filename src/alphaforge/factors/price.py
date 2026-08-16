#src/alphaforge/factors/price.py
"""Price-based factors for canonical long-form OHLCV data."""

from __future__ import annotations

import pandas as pd


def _validate_window(window: int) -> None:
    if window <= 0:
        raise ValueError("window must be positive")


def _ordered_close(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.loc[:, ["date", "symbol", "close"]].copy()
    ordered["_position"] = range(len(frame))
    return ordered.sort_values(["symbol", "date"], kind="mergesort")


def _restore_order(
    values: pd.Series,
    ordered: pd.DataFrame,
    frame: pd.DataFrame,
    name: str,
) -> pd.Series:
    result = pd.Series(values.to_numpy(), index=ordered["_position"]).sort_index()
    result.index = frame.index
    result.name = name
    return result


def _trailing_return(ordered: pd.DataFrame, window: int) -> pd.Series:
    return ordered.groupby("symbol", sort=False)["close"].transform(
        lambda close: close / close.shift(window) - 1.0
    )


def momentum(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Return each symbol's trailing close return through the current row."""

    _validate_window(window)
    ordered = _ordered_close(df)
    values = _trailing_return(ordered, window)
    return _restore_order(values, ordered, df, "momentum")


def reversal(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Return the negative trailing close return through the current row."""

    _validate_window(window)
    ordered = _ordered_close(df)
    values = -_trailing_return(ordered, window)
    return _restore_order(values, ordered, df, "reversal")


def volatility(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Return rolling sample volatility of each symbol's one-day returns."""

    _validate_window(window)
    ordered = _ordered_close(df)
    ordered["_return"] = _trailing_return(ordered, 1)
    values = ordered.groupby("symbol", sort=False)["_return"].transform(
        lambda returns: returns.rolling(window).std()
    )
    return _restore_order(values, ordered, df, "volatility")
