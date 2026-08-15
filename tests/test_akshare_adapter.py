#tests/test_akshare_adapter.py
from __future__ import annotations

import pandas as pd
import pytest

from alphaforge.data import (
    CANONICAL_OHLCV_COLUMNS,
    AkShareUpstreamDataError,
    validate_ohlcv,
)
from alphaforge.data.akshare import (
    akshare_to_canonical_symbol,
    canonical_to_akshare_symbol,
    fetch_akshare_daily_ohlcv,
)


@pytest.mark.parametrize(
    ("external", "canonical"),
    [
        ("sz000001", "000001.SZ"),
        ("sh600000", "600000.SH"),
        ("bj430047", "430047.BJ"),
    ],
)
def test_symbol_mapping_round_trip(external: str, canonical: str) -> None:
    assert akshare_to_canonical_symbol(external) == canonical
    assert canonical_to_akshare_symbol(canonical) == external


def test_canonical_symbol_with_wrong_exchange_is_rejected() -> None:
    with pytest.raises(ValueError, match="expected SH"):
        canonical_to_akshare_symbol("600000.SZ")


def test_fetch_maps_akshare_response_to_canonical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-02"],
            "open": [10.0, 9.5],
            "close": [10.5, 10.0],
            "high": [11.0, 10.2],
            "low": [9.8, 9.2],
            "volume": [12_300, 45_600],
            "amount": [1_000_000.0, 2_000_000.0],
            "outstanding_share": [1_000_000, 1_000_000],
            "turnover": [0.0123, 0.0456],
        }
    )
    call_arguments: dict[str, str] = {}

    def fake_stock_zh_a_daily(**kwargs: str) -> pd.DataFrame:
        call_arguments.update(kwargs)
        return source

    monkeypatch.setattr(
        "alphaforge.data.akshare.ak.stock_zh_a_daily",
        fake_stock_zh_a_daily,
    )

    result = fetch_akshare_daily_ohlcv(
        "600000.SH",
        start_date="20240101",
        end_date="20240131",
    )

    assert call_arguments == {
        "symbol": "sh600000",
        "start_date": "20240101",
        "end_date": "20240131",
        "adjust": "hfq",
    }
    assert tuple(result.columns) == CANONICAL_OHLCV_COLUMNS
    assert "amount" not in result
    assert "outstanding_share" not in result
    assert "turnover" not in result
    assert result["symbol"].tolist() == ["600000.SH", "600000.SH"]
    assert result.loc[0, ["open", "high", "low", "close"]].tolist() == [
        9.5,
        10.2,
        9.2,
        10.0,
    ]
    assert result["volume"].tolist() == [45_600.0, 12_300.0]
    assert result["date"].tolist() == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]
    assert validate_ohlcv(result) is None


def test_empty_akshare_response_has_clear_upstream_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "alphaforge.data.akshare.ak.stock_zh_a_daily",
        lambda **_: pd.DataFrame(),
    )

    with pytest.raises(AkShareUpstreamDataError, match="returned no rows"):
        fetch_akshare_daily_ohlcv("000001.SZ", "20240101", "20240131")


def test_missing_sina_column_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "open": [10.0],
            "high": [11.0],
            "low": [9.0],
            "close": [10.5],
        }
    )
    monkeypatch.setattr(
        "alphaforge.data.akshare.ak.stock_zh_a_daily",
        lambda **_: source,
    )

    with pytest.raises(AkShareUpstreamDataError, match="volume"):
        fetch_akshare_daily_ohlcv("000001.SZ", "20240101", "20240131")
