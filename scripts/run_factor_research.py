"""Run the first production research report for the baseline factors."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.data import MarketDataLoader
from alphaforge.pipeline import (
    BASELINE_CONFIG_PATH,
    compute_baseline_factors,
    load_pipeline_config,
)
from alphaforge.research import (
    assign_quantiles,
    compute_daily_ic,
    compute_factor_correlation,
    compute_forward_return,
    compute_quantile_returns,
    summarize_ic,
    summarize_quantile_returns,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        default=BASELINE_CONFIG_PATH,
        help=f"pipeline TOML path (default: {BASELINE_CONFIG_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Loading config: {args.config}")
    config = load_pipeline_config(args.config)
    research_config = config["research"]
    data_path = config["data"]["processed_path"]

    print(f"Loading market data: {data_path}")
    market_data = MarketDataLoader(data_path).load()
    print("Computing baseline factors and forward returns...")
    df = compute_baseline_factors(market_data, config["factors"])
    df["forward_return"] = compute_forward_return(
        df,
        horizon=research_config["forward_horizon"],
    )
    factor_columns = research_config["factors"]
    n_quantiles = research_config["n_quantiles"]

    print("Production factor research")
    print(f"dataset: {data_path}")
    print(f"dataset rows: {len(df):,}")
    print(f"date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"symbol count: {df['symbol'].nunique():,}")
    print(
        "forward_return non-null count: "
        f"{int(df['forward_return'].notna().sum()):,}"
    )

    for factor_col in factor_columns:
        ic = compute_daily_ic(df, factor_col)
        ic_summary = summarize_ic(ic)

        factor_data = df.loc[
            :, ["date", factor_col, "forward_return"]
        ].copy()
        factor_data["quantile"] = assign_quantiles(
            factor_data,
            factor_col,
            n_quantiles=n_quantiles,
        )
        quantile_returns = compute_quantile_returns(
            factor_data,
            n_quantiles=n_quantiles,
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
        for quantile in range(1, n_quantiles + 1):
            name = f"q{quantile}_mean"
            print(f"{name}: {quantile_summary[name]:.8f}")
        print(
            "top_minus_bottom: "
            f"{quantile_summary['top_minus_bottom']:.8f}"
        )

    factor_correlation = compute_factor_correlation(
        df,
        factor_columns,
    )
    print("\nMean daily cross-sectional Spearman factor correlation")
    print(factor_correlation.to_string(float_format=lambda value: f"{value:.6f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
