#scripts/run_out_of_sample.py
"""Run Day 10 factor and frozen-strategy out-of-sample evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd

from alphaforge.analytics import summarize_performance_by_period
from alphaforge.backtest import run_backtest
from alphaforge.data import MarketDataLoader
from alphaforge.pipeline import (
    BASELINE_CONFIG_PATH,
    compute_baseline_factors,
    load_pipeline_config,
)
from alphaforge.portfolio import build_long_only_top_quantile_portfolio
from alphaforge.research import run_out_of_sample_research


def save_out_of_sample_outputs(
    factor_research: pd.DataFrame,
    performance: pd.DataFrame,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist Day 10 comparison tables without recomputing results."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "factor_research": directory / "oos_factor_research.csv",
        "performance": directory / "oos_performance.csv",
    }
    factor_research.to_csv(paths["factor_research"], index=False)
    performance.to_csv(paths["performance"], index=False)
    return paths


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

    factor_config = config["factors"]
    research_config = config["research"]
    portfolio_config = config["portfolio"]
    backtest_config = config["backtest"]

    data_path = config["data"]["processed_path"]
    print(f"Loading market data: {data_path}")
    market_data = MarketDataLoader(data_path).load()
    print("Computing baseline factors...")
    data = compute_baseline_factors(market_data, factor_config)

    print("Running period-local factor research...")
    factor_research = run_out_of_sample_research(
        data,
        research_config["factors"],
        horizon=research_config["forward_horizon"],
        n_quantiles=research_config["n_quantiles"],
    )

    print("Running continuous baseline backtest...")
    portfolio = build_long_only_top_quantile_portfolio(
        data,
        portfolio_config["factor"],
        n_quantiles=portfolio_config["n_quantiles"],
    )
    _, daily_backtest = run_backtest(
        data,
        portfolio,
        transaction_cost_bps=backtest_config["transaction_cost_bps"],
        slippage_bps=backtest_config["slippage_bps"],
    )
    performance = summarize_performance_by_period(
        daily_backtest,
        annualization_factor=config["analytics"]["periods_per_year"],
    )

    print("AlphaForge Day 10 out-of-sample evaluation")
    print("\nFactor research")
    print(
        factor_research.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )
    print("\nFrozen baseline strategy performance")
    print(
        performance.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )

    print("\nSaving outputs...")
    paths = save_out_of_sample_outputs(
        factor_research,
        performance,
        config["output"]["directory"],
    )
    print("\nOutputs")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("\nNotes")
    print("Research labels are period-local; trading state is continuous.")
    print("Results are evaluated only and do not modify the frozen baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
