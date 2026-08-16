"""Run the first production research report for the baseline factors."""

from __future__ import annotations

from pathlib import Path

from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum, reversal, volatility
from alphaforge.research import (
    assign_quantiles,
    compute_daily_ic,
    compute_factor_correlation,
    compute_forward_return,
    compute_quantile_returns,
    summarize_ic,
    summarize_quantile_returns,
)

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")
FACTOR_COLUMNS = ("momentum_20d", "reversal_5d", "volatility_20d")


def main() -> None:
    df = MarketDataLoader(DATA_PATH).load()
    df["momentum_20d"] = momentum(df, window=20)
    df["reversal_5d"] = reversal(df, window=5)
    df["volatility_20d"] = volatility(df, window=20)
    df["forward_return"] = compute_forward_return(df, horizon=1)

    print("Production factor research")
    print(f"dataset: {DATA_PATH}")
    print(f"dataset rows: {len(df):,}")
    print(f"date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"symbol count: {df['symbol'].nunique():,}")
    print(
        "forward_return non-null count: "
        f"{int(df['forward_return'].notna().sum()):,}"
    )

    for factor_col in FACTOR_COLUMNS:
        ic = compute_daily_ic(df, factor_col)
        ic_summary = summarize_ic(ic)

        factor_data = df.loc[
            :, ["date", factor_col, "forward_return"]
        ].copy()
        factor_data["quantile"] = assign_quantiles(
            factor_data,
            factor_col,
            n_quantiles=5,
        )
        quantile_returns = compute_quantile_returns(
            factor_data,
            n_quantiles=5,
        )
        quantile_summary = summarize_quantile_returns(quantile_returns)

        paired_count = int(
            df.loc[:, [factor_col, "forward_return"]].notna().all(axis=1).sum()
        )
        print(f"\n{factor_col}")
        print(
            "factor non-null observations: "
            f"{int(df[factor_col].notna().sum()):,}"
        )
        print(
            "paired non-null factor/forward-return observations: "
            f"{paired_count:,}"
        )
        print(f"valid IC days: {int(ic.notna().sum()):,}")
        print(f"mean_ic: {ic_summary['mean_ic']:.8f}")
        print(f"ic_std: {ic_summary['ic_std']:.8f}")
        print(f"icir: {ic_summary['icir']:.8f}")
        for quantile in range(1, 6):
            name = f"q{quantile}_mean"
            print(f"{name}: {quantile_summary[name]:.8f}")
        print(
            "top_minus_bottom: "
            f"{quantile_summary['top_minus_bottom']:.8f}"
        )

    factor_correlation = compute_factor_correlation(
        df,
        list(FACTOR_COLUMNS),
    )
    print("\nMean daily cross-sectional Spearman factor correlation")
    print(factor_correlation.to_string(float_format=lambda value: f"{value:.6f}"))


if __name__ == "__main__":
    main()
