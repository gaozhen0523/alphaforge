#tests/test_data_schema.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.data import (
    CANONICAL_OHLCV_COLUMNS,
    OHLCVValidationError,
    normalize_ohlcv,
    validate_ohlcv,
)


def raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": [" 600000.sh", "000001.sz", "000001.sz"],
            "date": ["2024-01-03", "2024-01-03", "2024-01-02"],
            "open": [10, 20, 19],
            "high": [11, 22, 21],
            "low": [9, 19, 18],
            "close": [10.5, 21, 20],
            "volume": [1000, 2000, 1500],
        }
    )


def test_valid_data_passes() -> None:
    frame = normalize_ohlcv(raw_frame())

    assert validate_ohlcv(frame) is None


def test_duplicate_date_symbol_is_rejected() -> None:
    frame = raw_frame().iloc[[0, 0]].copy()

    with pytest.raises(OHLCVValidationError, match="must be unique"):
        normalize_ohlcv(frame)


@pytest.mark.parametrize(
    ("column", "value"),
    [("open", 12.0), ("close", 8.0), ("high", 8.0)],
)
def test_invalid_ohlc_is_rejected(column: str, value: float) -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, column] = value

    with pytest.raises(OHLCVValidationError, match="OHLC"):
        normalize_ohlcv(frame)


def test_non_positive_price_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "open"] = 0.0

    with pytest.raises(OHLCVValidationError, match="must be positive"):
        normalize_ohlcv(frame)


def test_non_finite_ohlcv_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame["volume"] = np.inf

    with pytest.raises(OHLCVValidationError, match="must be finite"):
        normalize_ohlcv(frame)


def test_negative_volume_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "volume"] = -1

    with pytest.raises(OHLCVValidationError, match="non-negative"):
        normalize_ohlcv(frame)


def test_missing_required_column_is_rejected() -> None:
    with pytest.raises(OHLCVValidationError, match="missing columns"):
        normalize_ohlcv(raw_frame().drop(columns="volume"))


def test_unexpected_column_is_rejected() -> None:
    frame = raw_frame().assign(amount=1.0)

    with pytest.raises(OHLCVValidationError, match="unexpected columns"):
        normalize_ohlcv(frame)


def test_invalid_date_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "date"] = "not-a-date"

    with pytest.raises(OHLCVValidationError, match="unparseable"):
        normalize_ohlcv(frame)


def test_invalid_symbol_format_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "symbol"] = "600000"

    with pytest.raises(OHLCVValidationError, match="six digits"):
        normalize_ohlcv(frame)


def test_symbol_with_wrong_exchange_is_rejected() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "symbol"] = "600000.SZ"

    with pytest.raises(OHLCVValidationError, match="six digits"):
        normalize_ohlcv(frame)


def test_missing_values_are_rejected_instead_of_filled() -> None:
    frame = raw_frame().iloc[[0]].copy()
    frame.loc[:, "close"] = np.nan

    with pytest.raises(OHLCVValidationError, match="must not be missing"):
        normalize_ohlcv(frame)


def test_normalization_sets_order_values_and_dtypes() -> None:
    frame = normalize_ohlcv(raw_frame())

    assert tuple(frame.columns) == CANONICAL_OHLCV_COLUMNS
    assert list(zip(frame["date"], frame["symbol"], strict=True)) == [
        (pd.Timestamp("2024-01-02"), "000001.SZ"),
        (pd.Timestamp("2024-01-03"), "000001.SZ"),
        (pd.Timestamp("2024-01-03"), "600000.SH"),
    ]
    assert str(frame["date"].dtype) == "datetime64[ns]"
    assert isinstance(frame["symbol"].dtype, pd.StringDtype)
    assert all(
        str(frame[column].dtype) == "float64"
        for column in CANONICAL_OHLCV_COLUMNS[2:]
    )
    assert len(frame) == len(raw_frame())
    assert isinstance(frame.index, pd.RangeIndex)


def test_strict_validation_rejects_unsorted_frame() -> None:
    frame = normalize_ohlcv(raw_frame()).iloc[::-1].reset_index(drop=True)

    with pytest.raises(OHLCVValidationError, match="sorted"):
        validate_ohlcv(frame)
