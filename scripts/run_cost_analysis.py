#scripts/run_cost_analysis.py
"""Run Day 11 cost sensitivity for the frozen baseline strategy."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd

from alphaforge.analytics import run_cost_sensitivity, summarize_turnover
from alphaforge.backtest import run_backtest
from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum
from alphaforge.pipeline import load_pipeline_config
from alphaforge.portfolio import build_long_only_top_quantile_portfolio

DEFAULT_CONFIG_PATH = Path("configs/baseline.toml")
COST_SCENARIOS = (
    (0.0, 0.0),
    (2.5, 2.5),
    (5.0, 5.0),
    (10.0, 10.0),
    (15.0, 15.0),
    (25.0, 25.0),
)


def save_cost_analysis_outputs(
    sensitivity: pd.DataFrame,
    turnover: pd.Series,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist Day 11 tables without recomputing analysis."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "cost_sensitivity": directory / "cost_sensitivity.csv",
        "turnover_summary": directory / "turnover_summary.csv",
    }
    sensitivity.to_csv(paths["cost_sensitivity"], index=False)
    turnover_frame = pd.DataFrame([turnover.to_dict()])
    turnover_frame["execution_count"] = turnover_frame[
        "execution_count"
    ].astype(int)
    turnover_frame.to_csv(paths["turnover_summary"], index=False)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"pipeline TOML path (default: {DEFAULT_CONFIG_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_pipeline_config(args.config)
    factor_config = config["factors"]
    portfolio_config = config["portfolio"]
    periods_per_year = config["analytics"]["periods_per_year"]

    data = MarketDataLoader(config["data"]["processed_path"]).load()
    factor_name = f"momentum_{factor_config['momentum_window']}d"
    data[factor_name] = momentum(
        data,
        window=factor_config["momentum_window"],
    )
    portfolio = build_long_only_top_quantile_portfolio(
        data,
        portfolio_config["factor"],
        n_quantiles=portfolio_config["n_quantiles"],
    )
    sensitivity = run_cost_sensitivity(
        data,
        portfolio,
        COST_SCENARIOS,
        periods_per_year=periods_per_year,
    )

    baseline_cost = config["backtest"]
    _, baseline_daily = run_backtest(
        data,
        portfolio,
        transaction_cost_bps=baseline_cost["transaction_cost_bps"],
        slippage_bps=baseline_cost["slippage_bps"],
    )
    turnover = summarize_turnover(
        baseline_daily,
        periods_per_year=periods_per_year,
    )
    baseline = sensitivity.loc[
        sensitivity["transaction_cost_bps"].eq(
            baseline_cost["transaction_cost_bps"]
        )
        & sensitivity["slippage_bps"].eq(
            baseline_cost["slippage_bps"]
        )
    ].iloc[0]

    print("AlphaForge Day 11 cost analysis")
    print(f"Scenario count: {len(sensitivity)}")
    print(f"Baseline total turnover: {turnover['total_turnover']:.8f}")
    print(
        "Baseline total gross traded weight: "
        f"{turnover['total_gross_traded_weight']:.8f}"
    )
    print("\nFriction    Ann. return      Sharpe    Cum. return    Ending NAV")
    for row in sensitivity.itertuples(index=False):
        print(
            f"{row.total_friction_bps:>5.1f} bps"
            f"{row.annualized_return:>15.8%}"
            f"{row.sharpe:>12.8f}"
            f"{row.cumulative_return:>15.8%}"
            f"{row.ending_nav:>14.8f}"
        )
    print("\nGross baseline performance")
    print(f"Gross cumulative return: {baseline['gross_cumulative_return']:.8%}")
    print(f"Gross ending NAV: {baseline['gross_ending_nav']:.8f}")
    print(
        "Baseline gross vs net cumulative return gap: "
        f"{baseline['gross_net_cumulative_return_gap']:.8%}"
    )

    paths = save_cost_analysis_outputs(
        sensitivity,
        turnover,
        config["output"]["directory"],
    )
    print("\nOutputs")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
