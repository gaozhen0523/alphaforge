from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest

from alphaforge.data import normalize_ohlcv
from alphaforge.data.bulk import BulkDownloadResult, DownloadFailure
from scripts import download_market_data


def one_bar(symbol: str) -> pd.DataFrame:
    return normalize_ohlcv(
        pd.DataFrame(
            {
                "date": ["2024-01-02"],
                "symbol": [symbol],
                "open": [10.0],
                "high": [11.0],
                "low": [9.0],
                "close": [10.5],
                "volume": [1_000],
            }
        )
    )


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    result: BulkDownloadResult,
) -> tuple[int, Path, list[Path]]:
    output = tmp_path / "ohlcv_hfq.parquet"
    writes: list[Path] = []
    monkeypatch.setattr(
        download_market_data,
        "load_universe_symbols",
        lambda _path, limit: list(result.requested_symbols),
    )
    monkeypatch.setattr(
        download_market_data,
        "download_daily_ohlcv",
        lambda *_args, **_kwargs: result,
    )
    monkeypatch.setattr(
        download_market_data,
        "write_canonical_parquet",
        lambda _frame, path: writes.append(path),
    )

    exit_code = download_market_data.main(
        [
            "--universe",
            str(tmp_path / "universe.csv"),
            "--start-date",
            "20240101",
            "--end-date",
            "20240131",
            "--output",
            str(output),
        ]
    )
    return exit_code, output, writes


def test_partial_failure_does_not_write_official_parquet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    result = BulkDownloadResult(
        data=one_bar("000001.SZ"),
        requested_symbols=("000001.SZ", "600000.SH"),
        failures=(
            DownloadFailure("600000.SH", "RuntimeError", "upstream unavailable"),
        ),
    )

    with caplog.at_level(logging.ERROR):
        exit_code, output, writes = run_main(monkeypatch, tmp_path, result)

    assert exit_code == 1
    assert writes == []
    assert not output.exists()
    assert "requested=2 succeeded=1 failures=1 rows=1" in caplog.text
    assert "official output not written" in caplog.text


def test_all_failed_does_not_write_official_parquet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    empty = normalize_ohlcv(
        pd.DataFrame(
            columns=("date", "symbol", "open", "high", "low", "close", "volume")
        )
    )
    result = BulkDownloadResult(
        data=empty,
        requested_symbols=("000001.SZ", "600000.SH"),
        failures=(
            DownloadFailure("000001.SZ", "RuntimeError", "first failure"),
            DownloadFailure("600000.SH", "RuntimeError", "second failure"),
        ),
    )

    with caplog.at_level(logging.ERROR):
        exit_code, output, writes = run_main(monkeypatch, tmp_path, result)

    assert exit_code == 1
    assert writes == []
    assert not output.exists()
    assert "requested=2 succeeded=0 failures=2 rows=0" in caplog.text


def test_all_successful_writes_official_parquet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = BulkDownloadResult(
        data=one_bar("000001.SZ"),
        requested_symbols=("000001.SZ",),
        failures=(),
    )

    exit_code, output, writes = run_main(monkeypatch, tmp_path, result)

    assert exit_code == 0
    assert writes == [output]
