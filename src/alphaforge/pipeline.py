#src/alphaforge/pipeline.py
"""Config-driven orchestration for the AlphaForge baseline workflow."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from alphaforge.analytics import summarize_performance
from alphaforge.backtest import run_backtest
from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum, reversal, volatility
from alphaforge.portfolio import build_long_only_top_quantile_portfolio
from alphaforge.research import (
    assign_quantiles,
    compute_daily_ic,
    compute_factor_correlation,
    compute_forward_return,
    compute_quantile_returns,
    summarize_ic,
    summarize_quantile_returns,
)

BASELINE_CONFIG_PATH = Path("configs/baseline.toml")


@dataclass(frozen=True)
class FactorResearchResult:
    """IC and quantile outputs for one factor."""

    daily_ic: pd.Series
    ic_summary: pd.Series
    quantile_returns: pd.DataFrame
    quantile_summary: pd.Series


@dataclass(frozen=True)
class PipelineResult:
    """Structured outputs from every stage of the baseline pipeline."""

    factor_data: pd.DataFrame
    factor_research: dict[str, FactorResearchResult]
    factor_correlation: pd.DataFrame
    portfolio: pd.DataFrame
    positions: pd.DataFrame
    daily_backtest: pd.DataFrame
    performance: pd.Series


def load_pipeline_config(path: str | Path) -> dict[str, Any]:
    """Load one pipeline definition from a TOML file."""

    with Path(path).open("rb") as config_file:
        return tomllib.load(config_file)


def compute_baseline_factors(
    market_data: pd.DataFrame,
    factor_config: Mapping[str, Any],
) -> pd.DataFrame:
    """Return market data with the three configured baseline factors."""

    result = market_data.copy()
    momentum_window = factor_config["momentum_window"]
    reversal_window = factor_config["reversal_window"]
    volatility_window = factor_config["volatility_window"]
    result[f"momentum_{momentum_window}d"] = momentum(
        result,
        window=momentum_window,
    )
    result[f"reversal_{reversal_window}d"] = reversal(
        result,
        window=reversal_window,
    )
    result[f"volatility_{volatility_window}d"] = volatility(
        result,
        window=volatility_window,
    )
    return result


def run_pipeline(config: Mapping[str, Any]) -> PipelineResult:
    """Run data -> factors -> research -> portfolio -> backtest -> analytics.

    This function only wires the established Day 1-6 public APIs. In particular,
    target decisions still execute at the next global trading-date close inside
    ``run_backtest``.
    """

    factor_config = config["factors"]
    research_config = config["research"]
    portfolio_config = config["portfolio"]
    backtest_config = config["backtest"]
    analytics_config = config["analytics"]

    market_data = MarketDataLoader(config["data"]["processed_path"]).load()
    factor_data = compute_baseline_factors(
        market_data,
        factor_config,
    )
    factor_data["forward_return"] = compute_forward_return(
        factor_data, horizon=research_config["forward_horizon"]
    )

    research_factors = list(research_config["factors"])
    n_research_quantiles = research_config["n_quantiles"]
    factor_research = {}
    for factor_name in research_factors:
        daily_ic = compute_daily_ic(factor_data, factor_name)
        research_frame = factor_data.loc[
            :, ["date", factor_name, "forward_return"]
        ].copy()
        research_frame["quantile"] = assign_quantiles(
            research_frame,
            factor_name,
            n_quantiles=n_research_quantiles,
        )
        quantile_returns = compute_quantile_returns(
            research_frame,
            n_quantiles=n_research_quantiles,
        )
        factor_research[factor_name] = FactorResearchResult(
            daily_ic=daily_ic,
            ic_summary=summarize_ic(daily_ic),
            quantile_returns=quantile_returns,
            quantile_summary=summarize_quantile_returns(quantile_returns),
        )

    factor_correlation = compute_factor_correlation(
        factor_data, research_factors
    )
    portfolio = build_long_only_top_quantile_portfolio(
        factor_data,
        portfolio_config["factor"],
        n_quantiles=portfolio_config["n_quantiles"],
    )
    positions, daily_backtest = run_backtest(
        factor_data,
        portfolio,
        transaction_cost_bps=backtest_config["transaction_cost_bps"],
        slippage_bps=backtest_config["slippage_bps"],
    )
    performance = summarize_performance(
        daily_backtest,
        annualization_factor=analytics_config["periods_per_year"],
    )

    return PipelineResult(
        factor_data=factor_data,
        factor_research=factor_research,
        factor_correlation=factor_correlation,
        portfolio=portfolio,
        positions=positions,
        daily_backtest=daily_backtest,
        performance=performance,
    )
