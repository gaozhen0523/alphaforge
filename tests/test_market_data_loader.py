#tests/test_market_data_loader.py
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from alphaforge.data import (
    CANONICAL_OHLCV_COLUMNS,
    MarketDataLoader,
    normalize_ohlcv,
    validate_ohlcv,
    write_canonical_parquet,
)


def canonical_frame() -> pd.DataFrame:
    return normalize_ohlcv(
        pd.DataFrame(
            {
                "date": [
                    "2024-01-04",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-02",
                    "2024-01-04",
                ],
                "symbol": [
                    "600000.SH",
                    "000001.SZ",
                    "000001.SZ",
                    "600000.SH",
                    "000001.SZ",
                ],
                "open": [20.2, 10.0, 10.2, 20.0, 10.4],
                "high": [20.8, 10.6, 10.8, 20.6, 11.0],
                "low": [19.8, 9.8, 10.0, 19.6, 10.2],
                "close": [20.5, 10.3, 10.5, 20.2, 10.7],
                "volume": [2_200, 1_000, 1_100, 2_000, 1_200],
            }
        )
    )


@pytest.fixture
def market_data(tmp_path: Path) -> tuple[Path, pd.DataFrame]:
    path = tmp_path / "ohlcv_hfq.parquet"
    frame = canonical_frame()
    write_canonical_parquet(frame, path)
    return path, frame


def test_load_full_dataset(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, expected = market_data

    result = MarketDataLoader(path).load()

    pd.testing.assert_frame_equal(result, expected)


def test_date_range_filtering_is_inclusive(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(
        start_date="2024-01-02",
        end_date="2024-01-03",
    )

    assert result["date"].tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]


def test_symbol_filtering(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(symbols=["600000.SH"])

    assert result["symbol"].tolist() == ["600000.SH", "600000.SH"]


def test_combined_date_and_symbol_filtering(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(
        start_date="2024-01-03",
        end_date="2024-01-04",
        symbols=["600000.SH"],
    )

    assert result[["date", "symbol"]].to_dict(orient="records") == [
        {"date": pd.Timestamp("2024-01-04"), "symbol": "600000.SH"}
    ]


def test_equal_date_boundaries_include_that_date(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(
        start_date="2024-01-04",
        end_date="2024-01-04",
    )

    assert len(result) == 2
    assert result["date"].eq(pd.Timestamp("2024-01-04")).all()


def test_invalid_date_range_is_rejected(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    with pytest.raises(ValueError, match="start_date must be on or before"):
        MarketDataLoader(path).load(
            start_date="2024-01-04",
            end_date="2024-01-03",
        )


@pytest.mark.parametrize(
    "symbols",
    [
        ["600000.SZ"],
        ["600000"],
        ["600000.sh"],
    ],
)
def test_invalid_canonical_symbol_is_rejected(
    market_data: tuple[Path, pd.DataFrame],
    symbols: list[str],
) -> None:
    path, _ = market_data

    with pytest.raises(ValueError, match="invalid canonical symbol"):
        MarketDataLoader(path).load(symbols=symbols)


def test_duplicate_symbols_are_rejected(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    with pytest.raises(ValueError, match="must be unique"):
        MarketDataLoader(path).load(symbols=["000001.SZ", "000001.SZ"])


def test_legal_symbol_absent_from_dataset_is_rejected(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    with pytest.raises(ValueError, match="not present.*000002.SZ"):
        MarketDataLoader(path).load(symbols=["000002.SZ"])


def test_missing_parquet_path_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        MarketDataLoader(path).load()


def test_loaded_filter_result_remains_canonical(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(
        start_date="2024-01-03",
        symbols=["000001.SZ"],
    )

    assert tuple(result.columns) == CANONICAL_OHLCV_COLUMNS
    assert validate_ohlcv(result) is None


def test_filtering_preserves_rows_without_filling_missing_observations(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, original = market_data

    result = MarketDataLoader(path).load(
        start_date="2024-01-02",
        end_date="2024-01-04",
        symbols=["600000.SH"],
    )

    expected = original.loc[original["symbol"].eq("600000.SH")].reset_index(
        drop=True
    )
    pd.testing.assert_frame_equal(result, expected)
    assert pd.Timestamp("2024-01-03") not in set(result["date"])
    pd.testing.assert_frame_equal(pd.read_parquet(path), original)


def test_valid_filter_with_no_observations_returns_canonical_empty_frame(
    market_data: tuple[Path, pd.DataFrame],
) -> None:
    path, _ = market_data

    result = MarketDataLoader(path).load(
        start_date="2025-01-01",
        end_date="2025-01-31",
    )

    assert result.empty
    assert tuple(result.columns) == CANONICAL_OHLCV_COLUMNS
    assert validate_ohlcv(result) is None
