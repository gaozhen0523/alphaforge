"""Build and inspect the production weekly baseline target portfolio."""

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
from alphaforge.portfolio import build_long_only_top_quantile_portfolio


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
    portfolio_config = config["portfolio"]
    data_path = config["data"]["processed_path"]

    print(f"Loading market data: {data_path}")
    market_data = MarketDataLoader(data_path).load()
    print("Computing baseline factors and portfolio...")
    df = compute_baseline_factors(market_data, config["factors"])
    portfolio = build_long_only_top_quantile_portfolio(
        df,
        portfolio_config["factor"],
        n_quantiles=portfolio_config["n_quantiles"],
    )

    rebalance_dates = portfolio.loc[
        portfolio["is_rebalance"], "date"
    ].drop_duplicates()
    selected_count = (
        portfolio.loc[portfolio["is_rebalance"]]
        .groupby("date")["signal"]
        .sum()
    )
    weight_sum = portfolio.groupby("date")["target_weight"].sum()
    active_weight_sum = weight_sum.loc[weight_sum.gt(0.0)]
    non_unit_active_dates = int(
        active_weight_sum.sub(1.0).abs().gt(1e-12).sum()
    )

    print("Production target portfolio")
    print(f"dataset: {data_path}")
    print(f"rows: {len(portfolio):,}")
    print(f"symbols: {portfolio['symbol'].nunique():,}")
    print(
        f"date range: {portfolio['date'].min().date()} to "
        f"{portfolio['date'].max().date()}"
    )
    print(f"rebalance count: {len(rebalance_dates):,}")
    print(f"first rebalance date: {rebalance_dates.iloc[0].date()}")
    print(f"last rebalance date: {rebalance_dates.iloc[-1].date()}")
    print(
        "selected count on rebalance dates "
        f"(min/median/max): {int(selected_count.min())}/"
        f"{selected_count.median():.1f}/{int(selected_count.max())}"
    )
    print(
        "target weight (min/max): "
        f"{portfolio['target_weight'].min():.8f}/"
        f"{portfolio['target_weight'].max():.8f}"
    )
    print(
        "negative weight count: "
        f"{int(portfolio['target_weight'].lt(0.0).sum()):,}"
    )
    print(
        "active cross-sectional weight sum (min/max): "
        f"{active_weight_sum.min():.12f}/{active_weight_sum.max():.12f}"
    )
    print(f"non-unit active dates: {non_unit_active_dates:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
