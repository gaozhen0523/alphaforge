#tests/test_factors.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.data import normalize_ohlcv
from alphaforge.factors import momentum, reversal, volatility


def factor_frame() -> pd.DataFrame:
    rows = []
    closes = {
        "000001.SZ": [100.0, 110.0, 99.0, 118.8],
        "600000.SH": [50.0, 100.0, 50.0, 100.0],
    }
    for symbol, prices in closes.items():
        for date, close in zip(pd.date_range("2024-01-02", periods=4), prices):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": 1_000.0,
                }
            )

    frame = normalize_ohlcv(pd.DataFrame(rows))
    frame.index = pd.Index([8, 3, 12, 5, 21, 13, 34, 2], name="row_id")
    return frame


def values_for(result: pd.Series, frame: pd.DataFrame, symbol: str) -> pd.Series:
    return result.loc[frame["symbol"].eq(symbol)]


def test_momentum_known_values_and_warm_up_nan() -> None:
    frame = factor_frame()

    result = values_for(momentum(frame, window=2), frame, "000001.SZ")

    np.testing.assert_allclose(result.iloc[2:], [-0.01, 0.08])
    assert result.iloc[:2].isna().all()


def test_reversal_is_negative_trailing_return() -> None:
    frame = factor_frame()

    result = values_for(reversal(frame, window=1), frame, "000001.SZ")

    np.testing.assert_allclose(result.iloc[1:], [-0.10, 0.10, -0.20])


def test_volatility_is_rolling_std_of_one_day_returns() -> None:
    frame = factor_frame()

    result = values_for(volatility(frame, window=2), frame, "000001.SZ")

    expected = pd.Series([0.10, -0.10, 0.20]).rolling(2).std()
    assert result.iloc[:2].isna().all()
    np.testing.assert_allclose(result.iloc[2:], expected.iloc[1:])


def test_calculations_are_isolated_by_symbol() -> None:
    frame = factor_frame()

    result = values_for(momentum(frame, window=1), frame, "600000.SH")

    np.testing.assert_allclose(result.iloc[1:], [1.0, -0.5, 1.0])
    assert result.iloc[0:].isna().sum() == 1


def test_output_index_matches_input_index() -> None:
    frame = factor_frame()

    for result in (momentum(frame), reversal(frame), volatility(frame)):
        assert result.index.equals(frame.index)


def test_shuffled_rows_are_calculated_chronologically_and_restored() -> None:
    frame = factor_frame()
    expected = momentum(frame, window=2)
    shuffled = frame.iloc[[6, 1, 4, 0, 7, 3, 5, 2]]

    result = momentum(shuffled, window=2)

    pd.testing.assert_series_equal(result, expected.loc[shuffled.index])


@pytest.mark.parametrize("window", [0, -1])
def test_non_positive_window_is_rejected(window: int) -> None:
    frame = factor_frame()

    for factor in (momentum, reversal, volatility):
        with pytest.raises(ValueError, match="window must be positive"):
            factor(frame, window=window)
