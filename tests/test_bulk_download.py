from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from alphaforge.data import (
    CANONICAL_OHLCV_COLUMNS,
    OHLCVValidationError,
    download_daily_ohlcv,
    normalize_ohlcv,
    validate_ohlcv,
    write_canonical_parquet,
)


def one_bar(symbol: str, date: str, close: float) -> pd.DataFrame:
    return normalize_ohlcv(
        pd.DataFrame(
            {
                "date": [date],
                "symbol": [symbol],
                "open": [close - 0.2],
                "high": [close + 0.5],
                "low": [close - 0.5],
                "close": [close],
                "volume": [1_000],
            }
        )
    )


def test_multi_symbol_download_is_sequential_and_canonical() -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fetch(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        assert (start_date, end_date) == ("20240101", "20240131")
        calls.append(symbol)
        close = 10.0 if symbol == "000001.SZ" else 20.0
        return one_bar(symbol, "2024-01-02", close)

    result = download_daily_ohlcv(
        ["000001.SZ", "600000.SH"],
        "20240101",
        "20240131",
        fetcher=fetch,
        sleep=sleeps.append,
    )

    assert calls == ["000001.SZ", "600000.SH"]
    assert sleeps == [2.0]
    assert result.failures == ()
    assert result.succeeded_symbols == ("000001.SZ", "600000.SH")
    assert result.data["symbol"].tolist() == ["000001.SZ", "600000.SH"]
    assert validate_ohlcv(result.data) is None


def test_failure_is_recorded_and_later_symbols_continue() -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fetch(symbol: str, _start: str, _end: str) -> pd.DataFrame:
        calls.append(symbol)
        if symbol == "600000.SH":
            raise RuntimeError("upstream unavailable")
        return one_bar(symbol, "2024-01-02", 10.0)

    result = download_daily_ohlcv(
        ["000001.SZ", "600000.SH", "000002.SZ"],
        "20240101",
        "20240131",
        delay_seconds=0.25,
        fetcher=fetch,
        sleep=sleeps.append,
    )

    assert calls == ["000001.SZ", "600000.SH", "000002.SZ"]
    assert sleeps == [0.25, 0.25]
    assert result.data["symbol"].tolist() == ["000001.SZ", "000002.SZ"]
    assert len(result.failures) == 1
    assert result.failures[0].symbol == "600000.SH"
    assert result.failures[0].error_type == "RuntimeError"
    assert result.failures[0].reason == "upstream unavailable"


def test_parquet_round_trip_preserves_canonical_schema_and_dtypes(
    tmp_path: Path,
) -> None:
    frame = normalize_ohlcv(
        pd.concat(
            [
                one_bar("600000.SH", "2024-01-03", 20.0),
                one_bar("000001.SZ", "2024-01-02", 10.0),
            ],
            ignore_index=True,
        )
    )
    path = tmp_path / "processed" / "ohlcv_hfq.parquet"

    read_back = write_canonical_parquet(frame, path)

    assert path.is_file()
    assert tuple(read_back.columns) == CANONICAL_OHLCV_COLUMNS
    assert str(read_back["date"].dtype) == "datetime64[ns]"
    assert isinstance(read_back["symbol"].dtype, pd.StringDtype)
    assert all(
        str(read_back[column].dtype) == "float64"
        for column in CANONICAL_OHLCV_COLUMNS[2:]
    )
    pd.testing.assert_frame_equal(read_back, frame)


def test_cross_frame_duplicate_rows_are_rejected() -> None:
    frame = one_bar("000001.SZ", "2024-01-02", 10.0)

    with pytest.raises(OHLCVValidationError, match="must be unique"):
        normalize_ohlcv(pd.concat([frame, frame], ignore_index=True))


def test_zero_delay_does_not_call_sleep() -> None:
    sleeps: list[float] = []

    result = download_daily_ohlcv(
        ["000001.SZ", "600000.SH"],
        "20240101",
        "20240131",
        delay_seconds=0,
        fetcher=lambda symbol, _start, _end: one_bar(
            symbol, "2024-01-02", 10.0
        ),
        sleep=sleeps.append,
    )

    assert not result.failures
    assert sleeps == []
