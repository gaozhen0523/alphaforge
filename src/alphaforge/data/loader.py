#src/alphaforge/data/loader.py
"""Thin loader for canonical daily OHLCV Parquet datasets."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

import pandas as pd

from .schema import CANONICAL_OHLCV_COLUMNS, validate_ohlcv
from .symbols import validate_canonical_symbol

DateFilter = str | date | pd.Timestamp


def _parse_filter_date(value: DateFilter | None, label: str) -> pd.Timestamp | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, date, pd.Timestamp)):
        raise TypeError(f"{label} must be a date-like value or None")
    try:
        parsed = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not a valid date") from exc
    if pd.isna(parsed):
        raise ValueError(f"{label} is not a valid date")
    if parsed.tzinfo is not None:
        raise ValueError(f"{label} must be timezone-naive")
    return parsed.normalize()


def _validate_requested_symbols(
    symbols: Iterable[str] | None,
) -> tuple[str, ...] | None:
    if symbols is None:
        return None
    if isinstance(symbols, (str, bytes)):
        raise TypeError("symbols must be an iterable of canonical symbols or None")

    try:
        requested = tuple(symbols)
    except TypeError as exc:
        raise TypeError(
            "symbols must be an iterable of canonical symbols or None"
        ) from exc

    for symbol in requested:
        if not isinstance(symbol, str):
            raise TypeError("each requested symbol must be a string")
        if symbol != symbol.strip().upper():
            raise ValueError(f"invalid canonical symbol: {symbol!r}")
        try:
            validate_canonical_symbol(symbol)
        except ValueError as exc:
            raise ValueError(f"invalid canonical symbol: {symbol!r}") from exc

    if len(requested) != len(set(requested)):
        raise ValueError("requested symbols must be unique")
    return requested


class MarketDataLoader:
    """Read and filter one canonical OHLCV Parquet dataset.

    Date boundaries are inclusive and interpreted as calendar dates. Requested
    symbols must use exact AlphaForge canonical form and must exist somewhere in
    the dataset. A valid query with no observations returns a validated canonical
    empty DataFrame. Loading and filtering never creates or fills observations.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(
        self,
        start_date: DateFilter | None = None,
        end_date: DateFilter | None = None,
        symbols: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        """Load canonical rows matching inclusive date and symbol filters."""

        start = _parse_filter_date(start_date, "start_date")
        end = _parse_filter_date(end_date, "end_date")
        if start is not None and end is not None and start > end:
            raise ValueError("start_date must be on or before end_date")
        requested_symbols = _validate_requested_symbols(symbols)

        if not self.path.is_file():
            raise FileNotFoundError(
                f"canonical market-data Parquet does not exist: {self.path}"
            )

        frame = pd.read_parquet(self.path)
        validate_ohlcv(frame)

        if requested_symbols is not None:
            available_symbols = set(frame["symbol"].tolist())
            missing_symbols = sorted(set(requested_symbols) - available_symbols)
            if missing_symbols:
                raise ValueError(
                    "requested symbols are not present in the dataset: "
                    f"{missing_symbols}"
                )

        filtered = frame
        if start is not None:
            filtered = filtered.loc[filtered["date"] >= start]
        if end is not None:
            filtered = filtered.loc[filtered["date"] <= end]
        if requested_symbols is not None:
            filtered = filtered.loc[filtered["symbol"].isin(requested_symbols)]

        result = (
            filtered.loc[:, list(CANONICAL_OHLCV_COLUMNS)]
            .sort_values(["date", "symbol"], kind="mergesort")
            .reset_index(drop=True)
        )
        validate_ohlcv(result)
        return result
