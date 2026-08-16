"""Print simple sanity checks for the baseline price factors."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum, reversal, volatility

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")
FACTOR_COLUMNS = ("momentum_20d", "reversal_5d", "volatility_20d")
DISPLAY_COLUMNS = ("date", "symbol", "close", *FACTOR_COLUMNS)


def main() -> None:
    df = MarketDataLoader(DATA_PATH).load()
    factors = {
        "momentum_20d": momentum(df, window=20),
        "reversal_5d": reversal(df, window=5),
        "volatility_20d": volatility(df, window=20),
    }

    print("Input summary")
    print(f"rows: {len(df):,}")
    print(f"unique symbols: {df['symbol'].nunique():,}")
    print(f"date range: {df['date'].min().date()} to {df['date'].max().date()}")

    summary = {}
    for name, values in factors.items():
        nan_count = int(values.isna().sum())
        summary[name] = {
            "non-null count": int(values.notna().sum()),
            "NaN count": nan_count,
            "NaN ratio": nan_count / len(values),
            "min": values.min(),
            "median": values.median(),
            "mean": values.mean(),
            "max": values.max(),
            "inf count": int(np.isinf(values.to_numpy()).sum()),
        }

    print("\nFactor summary")
    print(pd.DataFrame.from_dict(summary, orient="index").to_string())

    report = df.loc[:, ["date", "symbol", "close"]].copy()
    for name, values in factors.items():
        report[name] = values

    symbols = sorted(df["symbol"].unique())
    for symbol in (symbols[0], symbols[-1]):
        observations = (
            report.loc[report["symbol"].eq(symbol), list(DISPLAY_COLUMNS)]
            .sort_values("date")
            .tail(5)
        )
        print(f"\nLast 5 observations: {symbol}")
        print(observations.to_string(index=False))

    top_momentum = report.loc[
        report["momentum_20d"].abs().nlargest(10).index,
        list(DISPLAY_COLUMNS),
    ]
    print("\nTop 10 absolute momentum")
    print(top_momentum.to_string(index=False))

    top_reversal = report.loc[
        report["reversal_5d"].abs().nlargest(10).index,
        list(DISPLAY_COLUMNS),
    ]
    print("\nTop 10 absolute reversal")
    print(top_reversal.to_string(index=False))

    print("\nTop 10 volatility")
    top_volatility = report.nlargest(10, "volatility_20d").loc[
        :, list(DISPLAY_COLUMNS)
    ]
    print(top_volatility.to_string(index=False))


if __name__ == "__main__":
    main()
