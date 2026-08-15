#src/alphaforge/data/schema.py
"""Canonical daily OHLCV schema and validation.

The contract deliberately validates observed rows only. It never creates calendar
rows or fills absent bars, because an absent row may represent a suspension or
other real market-data condition that must remain explicit downstream.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

import numpy as np
import pandas as pd

from .symbols import validate_canonical_symbol

CANONICAL_OHLCV_COLUMNS: Final[tuple[str, ...]] = (
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

CANONICAL_OHLCV_DTYPES = MappingProxyType(
    {
        "date": "datetime64[ns]",
        "symbol": "string",
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "float64",
    }
)

_PRICE_COLUMNS: Final[tuple[str, ...]] = ("open", "high", "low", "close")
_NUMERIC_COLUMNS: Final[tuple[str, ...]] = (*_PRICE_COLUMNS, "volume")


class OHLCVValidationError(ValueError):
    """Raised when a frame violates the canonical OHLCV contract."""


def _require_columns(frame: pd.DataFrame) -> None:
    columns = list(frame.columns)
    if len(columns) != len(set(columns)):
        raise OHLCVValidationError("column names must be unique")

    missing = [name for name in CANONICAL_OHLCV_COLUMNS if name not in columns]
    unexpected = [name for name in columns if name not in CANONICAL_OHLCV_COLUMNS]
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing columns: {missing}")
        if unexpected:
            details.append(f"unexpected columns: {unexpected}")
        raise OHLCVValidationError("; ".join(details))


def normalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a canonical copy of a daily OHLCV frame.

    Normalization reorders columns, parses dates, uppercases and trims symbols,
    casts numeric values to float64, and performs a stable ``date, symbol`` sort.
    It does not add rows or fill missing values. The returned frame is validated.
    """

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    _require_columns(frame)

    normalized = frame.loc[:, list(CANONICAL_OHLCV_COLUMNS)].copy()

    try:
        dates = pd.to_datetime(normalized["date"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise OHLCVValidationError("date contains unparseable values") from exc
    if isinstance(dates.dtype, pd.DatetimeTZDtype):
        raise OHLCVValidationError("date must be timezone-naive")
    normalized["date"] = dates.dt.normalize().astype("datetime64[ns]")

    normalized["symbol"] = (
        normalized["symbol"].astype("string").str.strip().str.upper()
    )

    for column in _NUMERIC_COLUMNS:
        try:
            normalized[column] = pd.to_numeric(
                normalized[column], errors="raise"
            ).astype("float64")
        except (TypeError, ValueError) as exc:
            raise OHLCVValidationError(f"{column} must be numeric") from exc

    normalized = normalized.sort_values(
        ["date", "symbol"], kind="mergesort", ignore_index=True
    )
    validate_ohlcv(normalized)
    return normalized


def validate_ohlcv(frame: pd.DataFrame) -> None:
    """Validate an already-normalized frame against the canonical contract."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    _require_columns(frame)

    if tuple(frame.columns) != CANONICAL_OHLCV_COLUMNS:
        raise OHLCVValidationError(
            f"columns must be ordered as {CANONICAL_OHLCV_COLUMNS}"
        )

    if str(frame["date"].dtype) != CANONICAL_OHLCV_DTYPES["date"]:
        raise OHLCVValidationError("date dtype must be datetime64[ns]")
    if not isinstance(frame["symbol"].dtype, pd.StringDtype):
        raise OHLCVValidationError("symbol dtype must be pandas string")
    for column in _NUMERIC_COLUMNS:
        if str(frame[column].dtype) != CANONICAL_OHLCV_DTYPES[column]:
            raise OHLCVValidationError(f"{column} dtype must be float64")

    if frame.loc[:, list(CANONICAL_OHLCV_COLUMNS)].isna().any().any():
        raise OHLCVValidationError("canonical OHLCV values must not be missing")

    try:
        for symbol in frame["symbol"].unique():
            validate_canonical_symbol(str(symbol))
    except (TypeError, ValueError) as exc:
        raise OHLCVValidationError(
            "symbol must use six digits plus the valid .SH, .SZ, or .BJ suffix"
        ) from exc
    if not frame["date"].equals(frame["date"].dt.normalize()):
        raise OHLCVValidationError("date values must be normalized to midnight")

    values = frame.loc[:, list(_NUMERIC_COLUMNS)].to_numpy()
    if not np.isfinite(values).all():
        raise OHLCVValidationError("OHLCV values must be finite")
    if not frame.loc[:, list(_PRICE_COLUMNS)].gt(0).all().all():
        raise OHLCVValidationError("OHLC prices must be positive")
    if not frame["volume"].ge(0).all():
        raise OHLCVValidationError("volume must be non-negative")

    if not (
        frame["low"].le(frame["open"])
        & frame["open"].le(frame["high"])
        & frame["low"].le(frame["close"])
        & frame["close"].le(frame["high"])
    ).all():
        raise OHLCVValidationError("OHLC values violate low/high bounds")

    if frame.duplicated(["date", "symbol"]).any():
        raise OHLCVValidationError("(date, symbol) rows must be unique")

    actual_keys = frame.loc[:, ["date", "symbol"]].reset_index(drop=True)
    sorted_keys = actual_keys.sort_values(
        ["date", "symbol"], kind="mergesort", ignore_index=True
    )
    if not actual_keys.equals(sorted_keys):
        raise OHLCVValidationError("rows must be sorted by date, then symbol")
