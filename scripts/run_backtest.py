#scripts/run_backtest.py
"""Run the production momentum target portfolio through the Day 5 backtest."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.backtest import run_backtest
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
    backtest_config = config["backtest"]
    data_path = config["data"]["processed_path"]

    print(f"Loading market data: {data_path}")
    raw_market_data = MarketDataLoader(data_path).load()
    print("Computing baseline factors and portfolio...")
    market_data = compute_baseline_factors(
        raw_market_data,
        config["factors"],
    )
    targets = build_long_only_top_quantile_portfolio(
        market_data,
        portfolio_config["factor"],
        n_quantiles=portfolio_config["n_quantiles"],
    )
    print("Running backtest...")
    positions, daily = run_backtest(
        market_data,
        targets,
        transaction_cost_bps=backtest_config["transaction_cost_bps"],
        slippage_bps=backtest_config["slippage_bps"],
    )

    decision_count = targets.loc[targets["is_rebalance"], "date"].nunique()
    gross_cumulative_return = (1.0 + daily["gross_return"]).prod() - 1.0

    print("Production backtest")
    print(f"dataset: {data_path}")
    print(f"position rows: {len(positions):,}")
    print(f"symbols: {positions['symbol'].nunique():,}")
    print(
        f"date range: {positions['date'].min().date()} to "
        f"{positions['date'].max().date()}"
    )
    print(f"decision count: {decision_count:,}")
    print(f"execution count: {int(daily['is_execution'].sum()):,}")
    print(
        "gross traded weight (total/mean/max): "
        f"{daily['gross_traded_weight'].sum():.8f}/"
        f"{daily['gross_traded_weight'].mean():.8f}/"
        f"{daily['gross_traded_weight'].max():.8f}"
    )
    print(
        "turnover (total/mean/max): "
        f"{daily['turnover'].sum():.8f}/"
        f"{daily['turnover'].mean():.8f}/"
        f"{daily['turnover'].max():.8f}"
    )
    print(f"total transaction cost: {daily['transaction_cost'].sum():.8f}")
    print(f"total slippage cost: {daily['slippage_cost'].sum():.8f}")
    print(f"gross cumulative return: {gross_cumulative_return:.8%}")
    print(f"net cumulative return: {daily['cumulative_pnl'].iloc[-1]:.8%}")
    print(f"ending NAV: {daily['nav'].iloc[-1]:.8f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
