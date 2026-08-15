#scripts/smoke_akshare_data.py
"""Manually smoke-test AkShare to canonical OHLCV conversion."""

from __future__ import annotations

import pandas as pd

from alphaforge.data import (
    fetch_akshare_daily_ohlcv,
    normalize_ohlcv,
    validate_ohlcv,
)

SYMBOLS = ("000001.SZ", "600000.SH")
START_DATE = "20240101"
END_DATE = "20240131"


def main() -> None:
    frames = []
    for symbol in SYMBOLS:
        frame = fetch_akshare_daily_ohlcv(
            symbol,
            START_DATE,
            END_DATE,
        )
        if frame.empty:
            raise RuntimeError(f"AkShare returned no rows for {symbol}")
        frames.append(frame)

    combined = normalize_ohlcv(pd.concat(frames, ignore_index=True))
    validate_ohlcv(combined)

    print(combined.head())
    print(combined.dtypes)
    print(f"validated {len(combined)} rows for {combined['symbol'].nunique()} symbols")


if __name__ == "__main__":
    main()
