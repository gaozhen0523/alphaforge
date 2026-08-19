"""Run Day 6 analytics on the production momentum backtest."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.analytics import summarize_performance
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
    print("Running backtest and analytics...")
    _, daily = run_backtest(
        market_data,
        targets,
        transaction_cost_bps=backtest_config["transaction_cost_bps"],
        slippage_bps=backtest_config["slippage_bps"],
    )
    summary = summarize_performance(
        daily,
        annualization_factor=config["analytics"]["periods_per_year"],
    )

    print("Performance summary")
    print("-------------------")
    print(f"Annualized return: {summary['annualized_return']:.8%}")
    print(
        "Annualized volatility: "
        f"{summary['annualized_volatility']:.8%}"
    )
    print(f"Sharpe ratio: {summary['sharpe_ratio']:.8f}")
    print(f"Max drawdown: {summary['max_drawdown']:.8%}")
    print(f"Total turnover: {summary['total_turnover']:.8f}")
    print(
        "Average daily turnover: "
        f"{summary['average_daily_turnover']:.8f}"
    )
    print(f"Annualized turnover: {summary['annualized_turnover']:.8f}")
    print(f"Ending NAV: {summary['ending_nav']:.8f}")
    print(f"Cumulative return: {summary['cumulative_return']:.8%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
