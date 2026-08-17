#src/alphaforge/backtest/engine.py
"""Daily close-to-close backtest with explicit execution timing."""

from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    market_data: pd.DataFrame,
    portfolio: pd.DataFrame,
    transaction_cost_bps: float = 5.0,
    slippage_bps: float = 5.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run target-to-NAV accounting with next-global-date close execution.

    A target decided at close on date ``t`` is executed at the next global
    trading-date close. The old post-trade weights therefore earn date ``t+1``'s
    close-to-close return before the new target is installed.
    """

    positions = portfolio.loc[
        :, ["date", "symbol", "target_weight", "is_rebalance"]
    ].copy()
    positions = positions.sort_values(["date", "symbol"], kind="mergesort")

    observed_close = market_data.loc[:, ["date", "symbol", "close"]]
    positions = positions.merge(
        observed_close,
        on=["date", "symbol"],
        how="left",
        validate="one_to_one",
    )
    positions["marked_close"] = positions.groupby(
        "symbol", sort=False
    )["close"].ffill()
    positions["asset_return"] = (
        positions.groupby("symbol", sort=False)["marked_close"]
        .pct_change(fill_method=None)
        .fillna(0.0)
    )

    dates = pd.Index(positions["date"].drop_duplicates())
    symbols = pd.Index(positions["symbol"].drop_duplicates())
    n_dates = len(dates)
    n_symbols = len(symbols)

    target = positions["target_weight"].to_numpy().reshape(n_dates, n_symbols)
    asset_return = positions["asset_return"].to_numpy().reshape(
        n_dates, n_symbols
    )
    decision = (
        positions.groupby("date", sort=False)["is_rebalance"].first().to_numpy()
    )
    is_execution = np.zeros(n_dates, dtype=bool)
    is_execution[1:] = decision[:-1]

    execution_target = np.full((n_dates, n_symbols), np.nan)
    pretrade = np.zeros((n_dates, n_symbols))
    trade = np.zeros((n_dates, n_symbols))
    posttrade = np.zeros((n_dates, n_symbols))

    gross_return = np.zeros(n_dates)
    gross_traded_weight = np.zeros(n_dates)
    turnover = np.zeros(n_dates)
    transaction_cost = np.zeros(n_dates)
    slippage_cost = np.zeros(n_dates)
    total_cost = np.zeros(n_dates)
    net_return = np.zeros(n_dates)
    nav = np.zeros(n_dates)

    previous_posttrade = np.zeros(n_symbols)
    previous_nav = 1.0

    for day in range(n_dates):
        gross_return[day] = np.dot(previous_posttrade, asset_return[day])
        pretrade[day] = (
            previous_posttrade
            * (1.0 + asset_return[day])
            / (1.0 + gross_return[day])
        )

        if is_execution[day]:
            execution_target[day] = target[day - 1]
            trade[day] = execution_target[day] - pretrade[day]
            posttrade[day] = execution_target[day]
            gross_traded_weight[day] = np.abs(trade[day]).sum()
            cash_trade = posttrade[day].sum() - pretrade[day].sum()
            turnover[day] = 0.5 * (
                gross_traded_weight[day] + abs(cash_trade)
            )
        else:
            posttrade[day] = pretrade[day]

        transaction_cost[day] = (
            gross_traded_weight[day] * transaction_cost_bps / 10_000.0
        )
        slippage_cost[day] = (
            gross_traded_weight[day] * slippage_bps / 10_000.0
        )
        total_cost[day] = transaction_cost[day] + slippage_cost[day]
        net_return[day] = (
            (1.0 + gross_return[day]) * (1.0 - total_cost[day]) - 1.0
        )
        nav[day] = previous_nav * (1.0 + net_return[day])

        previous_posttrade = posttrade[day]
        previous_nav = nav[day]

    positions["execution_target_weight"] = execution_target.ravel()
    positions["pretrade_weight"] = pretrade.ravel()
    positions["trade_weight"] = trade.ravel()
    positions["posttrade_weight"] = posttrade.ravel()
    positions["is_execution"] = np.repeat(is_execution, n_symbols)
    positions = positions.loc[
        :,
        [
            "date",
            "symbol",
            "asset_return",
            "target_weight",
            "execution_target_weight",
            "pretrade_weight",
            "trade_weight",
            "posttrade_weight",
            "is_rebalance",
            "is_execution",
        ],
    ]

    summary = pd.DataFrame(
        {
            "date": dates,
            "is_execution": is_execution,
            "gross_return": gross_return,
            "gross_traded_weight": gross_traded_weight,
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "slippage_cost": slippage_cost,
            "total_cost": total_cost,
            "net_return": net_return,
            "nav": nav,
            "cumulative_pnl": nav - 1.0,
        }
    )
    return positions.reset_index(drop=True), summary
