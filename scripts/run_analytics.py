"""Run Day 6 analytics on the production momentum backtest."""

from __future__ import annotations

from pathlib import Path

from alphaforge.analytics import summarize_performance
from alphaforge.backtest import run_backtest
from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum
from alphaforge.portfolio import build_long_only_top_quantile_portfolio

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")


def main() -> None:
    market_data = MarketDataLoader(DATA_PATH).load()
    market_data["momentum_20d"] = momentum(market_data, window=20)
    targets = build_long_only_top_quantile_portfolio(
        market_data, "momentum_20d"
    )
    _, daily = run_backtest(market_data, targets)
    summary = summarize_performance(daily)

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


if __name__ == "__main__":
    main()
