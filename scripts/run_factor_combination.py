#scripts/run_factor_combination.py
"""Run Day 12 factor-combination research and strategy comparisons."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from alphaforge.analytics import (
    summarize_performance,
    summarize_performance_by_period,
)
from alphaforge.backtest import run_backtest
from alphaforge.data import MarketDataLoader
from alphaforge.pipeline import (
    BASELINE_CONFIG_PATH,
    compute_baseline_factors,
    load_pipeline_config,
)
from alphaforge.portfolio import build_long_only_top_quantile_portfolio
from alphaforge.research import (
    assign_oos_period,
    assign_quantiles,
    combine_factors_by_rank,
    combine_factors_by_zscore,
    compute_daily_ic,
    compute_forward_return,
    compute_period_forward_return,
    compute_quantile_returns,
    run_out_of_sample_research,
    summarize_ic,
    summarize_quantile_returns,
)

OUTPUT_PERIOD_NAMES = {
    "is_2021_2023": "IS_2021_2023",
    "oos_2024": "OOS_2024",
    "oos_2025": "OOS_2025",
}


def summarize_full_sample_research(
    data: pd.DataFrame,
    factor_cols: Sequence[str],
    n_quantiles: int,
) -> pd.DataFrame:
    """Summarize factors with the established Day 3 research APIs."""

    rows = []
    for factor_col in factor_cols:
        daily_ic = compute_daily_ic(data, factor_col)
        ic_summary = summarize_ic(daily_ic)
        research_frame = data.loc[
            :, ["date", factor_col, "forward_return"]
        ].copy()
        research_frame["quantile"] = assign_quantiles(
            research_frame,
            factor_col,
            n_quantiles=n_quantiles,
        )
        quantile_returns = compute_quantile_returns(
            research_frame,
            n_quantiles=n_quantiles,
        )
        quantile_summary = summarize_quantile_returns(quantile_returns)
        quantile_means = {
            f"q{quantile}_mean": quantile_summary[f"q{quantile}_mean"]
            for quantile in range(1, n_quantiles + 1)
        }
        rows.append(
            {
                "factor": factor_col,
                "period": "FULL",
                "valid_ic_days": int(ic_summary["n_obs"]),
                "mean_ic": ic_summary["mean_ic"],
                "icir": ic_summary["icir"],
                **quantile_means,
                "q5_minus_q1": (
                    quantile_means[f"q{n_quantiles}_mean"]
                    - quantile_means["q1_mean"]
                ),
            }
        )
    return pd.DataFrame(rows)


def add_period_quantile_means(
    data: pd.DataFrame,
    period_research: pd.DataFrame,
    factor_cols: Sequence[str],
    horizon: int,
    n_quantiles: int,
) -> pd.DataFrame:
    """Add middle-quantile means using the established Day 3/10 APIs."""

    result = period_research.copy()
    for quantile in range(2, n_quantiles):
        result[f"q{quantile}_mean"] = float("nan")

    period = assign_oos_period(data["date"])
    forward_return = compute_period_forward_return(data, horizon=horizon)
    for factor_col in factor_cols:
        for period_name in OUTPUT_PERIOD_NAMES:
            in_period = period.eq(period_name)
            research_frame = data.loc[in_period, ["date", factor_col]].copy()
            research_frame["forward_return"] = forward_return.loc[in_period]
            research_frame["quantile"] = assign_quantiles(
                research_frame,
                factor_col,
                n_quantiles=n_quantiles,
            )
            quantile_returns = compute_quantile_returns(
                research_frame,
                n_quantiles=n_quantiles,
            )
            quantile_summary = summarize_quantile_returns(quantile_returns)
            output_row = result["factor"].eq(factor_col) & result["period"].eq(
                period_name
            )
            for quantile in range(2, n_quantiles):
                result.loc[output_row, f"q{quantile}_mean"] = quantile_summary[
                    f"q{quantile}_mean"
                ]
    return result


def run_factor_combination(
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run Day 12 research and continuous strategy comparisons."""

    factor_config = config["factors"]
    research_config = config["research"]
    portfolio_config = config["portfolio"]
    backtest_config = config["backtest"]
    annualization_factor = config["analytics"]["periods_per_year"]

    market_data = MarketDataLoader(config["data"]["processed_path"]).load()
    momentum_name = f"momentum_{factor_config['momentum_window']}d"
    reversal_name = f"reversal_{factor_config['reversal_window']}d"
    volatility_name = f"volatility_{factor_config['volatility_window']}d"
    data = compute_baseline_factors(market_data, factor_config)

    # Ex-ante directions only: reversal is already negative trailing return.
    factor_directions = {
        momentum_name: 1,
        reversal_name: 1,
        volatility_name: -1,
    }
    data["combined_rank"] = combine_factors_by_rank(data, factor_directions)
    data["combined_zscore"] = combine_factors_by_zscore(
        data,
        factor_directions,
    )

    factor_cols = [
        momentum_name,
        reversal_name,
        volatility_name,
        "combined_rank",
        "combined_zscore",
    ]
    data["forward_return"] = compute_forward_return(
        data,
        horizon=research_config["forward_horizon"],
    )
    full_research = summarize_full_sample_research(
        data,
        factor_cols,
        n_quantiles=research_config["n_quantiles"],
    )
    period_research = run_out_of_sample_research(
        data,
        factor_cols,
        horizon=research_config["forward_horizon"],
        n_quantiles=research_config["n_quantiles"],
    )
    period_research = add_period_quantile_means(
        data,
        period_research,
        factor_cols,
        horizon=research_config["forward_horizon"],
        n_quantiles=research_config["n_quantiles"],
    )
    period_research["period"] = period_research["period"].map(
        OUTPUT_PERIOD_NAMES
    )
    research_columns = [
        "factor",
        "period",
        "valid_ic_days",
        "mean_ic",
        "icir",
        *[
            f"q{quantile}_mean"
            for quantile in range(1, research_config["n_quantiles"] + 1)
        ],
        "q5_minus_q1",
    ]
    research = pd.concat(
        [full_research, period_research],
        ignore_index=True,
    ).loc[:, research_columns]

    strategy_rows = []
    strategies = (
        (momentum_name, "frozen_baseline"),
        ("combined_rank", "experimental"),
        ("combined_zscore", "experimental"),
    )
    for strategy, strategy_type in strategies:
        portfolio = build_long_only_top_quantile_portfolio(
            data,
            strategy,
            n_quantiles=portfolio_config["n_quantiles"],
        )
        _, daily_backtest = run_backtest(
            data,
            portfolio,
            transaction_cost_bps=backtest_config["transaction_cost_bps"],
            slippage_bps=backtest_config["slippage_bps"],
        )
        full_performance = summarize_performance(
            daily_backtest,
            annualization_factor=annualization_factor,
        )
        strategy_rows.append(
            {
                "strategy": strategy,
                "strategy_type": strategy_type,
                "period": "FULL",
                **full_performance.to_dict(),
            }
        )
        period_performance = summarize_performance_by_period(
            daily_backtest,
            annualization_factor=annualization_factor,
        )
        period_performance["period"] = period_performance["period"].map(
            OUTPUT_PERIOD_NAMES
        )
        for row in period_performance.to_dict("records"):
            strategy_rows.append(
                {
                    "strategy": strategy,
                    "strategy_type": strategy_type,
                    **row,
                }
            )

    return research, pd.DataFrame(strategy_rows)


def save_factor_combination_outputs(
    research: pd.DataFrame,
    strategy: pd.DataFrame,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Save the two compact Day 12 comparison tables."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "research": directory / "factor_combination_research.csv",
        "strategy": directory / "factor_combination_strategy.csv",
    }
    research.to_csv(paths["research"], index=False)
    strategy.to_csv(paths["strategy"], index=False)
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
    print("Running factor-combination research and backtests...")
    research, strategy = run_factor_combination(config)

    print("AlphaForge Day 12 factor combination")
    print("\nFactor research")
    print(
        research.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )
    print("\nStrategy comparison")
    print(
        strategy.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )

    print("\nSaving outputs...")
    paths = save_factor_combination_outputs(
        research,
        strategy,
        config["output"]["directory"],
    )
    print("\nOutputs")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("\nResults are retrospective chronological robustness evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
