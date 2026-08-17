"""Run the config-driven AlphaForge baseline pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from alphaforge.pipeline import (
    PipelineResult,
    load_pipeline_config,
    run_pipeline,
)

DEFAULT_CONFIG_PATH = Path("configs/baseline.toml")


def save_pipeline_outputs(
    result: PipelineResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Persist the minimum useful baseline artifacts from existing results."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "factor_research": directory / "factor_research.csv",
        "daily_backtest": directory / "daily_backtest.parquet",
        "performance": directory / "performance.json",
    }

    factor_rows = []
    for factor_name, research in result.factor_research.items():
        factor_rows.append(
            {
                "factor": factor_name,
                "valid_ic_days": int(research.ic_summary["n_obs"]),
                "mean_ic": float(research.ic_summary["mean_ic"]),
                "icir": float(research.ic_summary["icir"]),
                "q5_minus_q1_mean": float(
                    research.quantile_summary["top_minus_bottom"]
                ),
            }
        )
    pd.DataFrame(factor_rows).to_csv(paths["factor_research"], index=False)
    result.daily_backtest.to_parquet(paths["daily_backtest"], index=False)

    performance = {
        metric: float(value) for metric, value in result.performance.items()
    }
    with paths["performance"].open("w", encoding="utf-8") as output_file:
        json.dump(performance, output_file, indent=2, allow_nan=False)
        output_file.write("\n")

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
    result = run_pipeline(config)

    data = result.factor_data
    daily = result.daily_backtest
    performance = result.performance

    print("AlphaForge baseline pipeline")
    print(f"Config: {args.config}")

    print("\nData")
    print(f"Rows: {len(data):,}")
    print(f"Symbols: {data['symbol'].nunique():,}")
    print(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")

    print("\nFactor Research")
    print("Factor                 IC days     Mean IC        ICIR      Q5-Q1")
    for factor_name, research in result.factor_research.items():
        ic_summary = research.ic_summary
        print(
            f"{factor_name:<22}"
            f"{int(ic_summary['n_obs']):>8,}"
            f"{ic_summary['mean_ic']:>13.8f}"
            f"{ic_summary['icir']:>12.8f}"
            f"{research.quantile_summary['top_minus_bottom']:>12.8f}"
        )

    decision_count = result.portfolio.loc[
        result.portfolio["is_rebalance"], "date"
    ].nunique()
    print("\nPortfolio")
    print(f"Decision count: {decision_count:,}")

    print("\nBacktest")
    print(f"Execution count: {int(daily['is_execution'].sum()):,}")
    print(f"Total turnover: {daily['turnover'].sum():.8f}")
    print(f"Ending NAV: {performance['ending_nav']:.8f}")
    print(f"Cumulative return: {performance['cumulative_return']:.8%}")

    print("\nAnalytics")
    print(f"Annualized return: {performance['annualized_return']:.8%}")
    print(
        "Annualized volatility: "
        f"{performance['annualized_volatility']:.8%}"
    )
    print(f"Sharpe ratio: {performance['sharpe_ratio']:.8f}")
    print(f"Max drawdown: {performance['max_drawdown']:.8%}")
    print(f"Annualized turnover: {performance['annualized_turnover']:.8f}")

    output_paths = save_pipeline_outputs(result, config["output"]["directory"])
    print("\nOutputs")
    print(f"Factor research: {output_paths['factor_research']}")
    print(f"Daily backtest: {output_paths['daily_backtest']}")
    print(f"Performance: {output_paths['performance']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
