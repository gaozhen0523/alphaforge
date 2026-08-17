#scripts/run_backtest.py
"""Run the production momentum target portfolio through the Day 5 backtest."""

from __future__ import annotations

from pathlib import Path

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
    positions, daily = run_backtest(market_data, targets)

    decision_count = targets.loc[targets["is_rebalance"], "date"].nunique()
    gross_cumulative_return = (1.0 + daily["gross_return"]).prod() - 1.0

    print("Production backtest")
    print(f"dataset: {DATA_PATH}")
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


if __name__ == "__main__":
    main()
