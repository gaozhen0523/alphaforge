#src/alphaforge/data/bulk.py
"""Sequential, rate-controlled market-data acquisition and persistence."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path

import pandas as pd

from .akshare import fetch_akshare_daily_ohlcv
from .schema import CANONICAL_OHLCV_COLUMNS, normalize_ohlcv, validate_ohlcv

DailyFetcher = Callable[[str, str, str], pd.DataFrame]
Sleeper = Callable[[float], None]


@dataclass(frozen=True)
class DownloadFailure:
    """One symbol that could not be fetched or normalized."""

    symbol: str
    error_type: str
    reason: str


@dataclass(frozen=True)
class BulkDownloadResult:
    """Canonical successful rows plus explicitly recorded failures."""

    data: pd.DataFrame
    requested_symbols: tuple[str, ...]
    failures: tuple[DownloadFailure, ...]

    @property
    def succeeded_symbols(self) -> tuple[str, ...]:
        failed = {failure.symbol for failure in self.failures}
        return tuple(
            symbol for symbol in self.requested_symbols if symbol not in failed
        )


def _validate_date_range(start_date: str, end_date: str) -> None:
    parsed: list[datetime] = []
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        if not isinstance(value, str):
            raise TypeError(f"{label} must be a string")
        try:
            date = datetime.strptime(value, "%Y%m%d")
        except ValueError as exc:
            raise ValueError(f"{label} must use YYYYMMDD") from exc
        if date.strftime("%Y%m%d") != value:
            raise ValueError(f"{label} must use YYYYMMDD")
        parsed.append(date)
    if parsed[0] > parsed[1]:
        raise ValueError("start_date must be on or before end_date")


def _empty_canonical_frame() -> pd.DataFrame:
    return normalize_ohlcv(pd.DataFrame(columns=CANONICAL_OHLCV_COLUMNS))


def download_daily_ohlcv(
    symbols: Iterable[str],
    start_date: str,
    end_date: str,
    *,
    delay_seconds: float = 2.0,
    fetcher: DailyFetcher = fetch_akshare_daily_ohlcv,
    sleep: Sleeper = time.sleep,
) -> BulkDownloadResult:
    """Download symbols sequentially, spacing attempts and retaining failures."""

    _validate_date_range(start_date, end_date)
    if not isinstance(delay_seconds, (int, float)) or isinstance(
        delay_seconds, bool
    ):
        raise TypeError("delay_seconds must be numeric")
    delay_seconds = float(delay_seconds)
    if not isfinite(delay_seconds) or delay_seconds < 0:
        raise ValueError("delay_seconds must be finite and non-negative")

    requested_symbols = tuple(symbols)
    frames: list[pd.DataFrame] = []
    failures: list[DownloadFailure] = []

    for position, symbol in enumerate(requested_symbols):
        if position > 0 and delay_seconds > 0:
            sleep(delay_seconds)
        try:
            frame = normalize_ohlcv(fetcher(symbol, start_date, end_date))
            if frame.empty:
                raise ValueError("fetcher returned no rows")
            returned_symbols = set(frame["symbol"].tolist())
            if returned_symbols != {symbol}:
                raise ValueError(
                    f"fetcher returned symbols {sorted(returned_symbols)}"
                )
            frames.append(frame)
        except Exception as exc:
            failures.append(
                DownloadFailure(
                    symbol=symbol,
                    error_type=type(exc).__name__,
                    reason=str(exc),
                )
            )

    combined = (
        normalize_ohlcv(pd.concat(frames, ignore_index=True))
        if frames
        else _empty_canonical_frame()
    )
    return BulkDownloadResult(
        data=combined,
        requested_symbols=requested_symbols,
        failures=tuple(failures),
    )


def write_canonical_parquet(frame: pd.DataFrame, path: Path) -> pd.DataFrame:
    """Write one consolidated Parquet file and strictly validate its read-back."""

    normalized = normalize_ohlcv(frame)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_parquet(output_path, index=False)

    read_back = pd.read_parquet(output_path)
    validate_ohlcv(read_back)
    pd.testing.assert_frame_equal(
        read_back,
        normalized,
        check_dtype=True,
        check_exact=True,
    )
    return read_back
