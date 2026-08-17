from __future__ import annotations

import numpy as np
import pandas as pd

from alphaforge.backtest import run_backtest


def market_frame(
    dates: list[str], closes: dict[str, list[float | None]]
) -> pd.DataFrame:
    rows = []
    for symbol, prices in closes.items():
        for date, close in zip(pd.to_datetime(dates), prices):
            if close is not None:
                rows.append({"date": date, "symbol": symbol, "close": close})
    return pd.DataFrame(rows).sort_values(["date", "symbol"]).reset_index(drop=True)


def portfolio_frame(
    dates: list[str],
    symbols: list[str],
    decisions: dict[str, dict[str, float]],
) -> pd.DataFrame:
    current_target = {symbol: 0.0 for symbol in symbols}
    rows = []
    for date in pd.to_datetime(dates):
        date_key = str(date.date())
        is_rebalance = date_key in decisions
        if is_rebalance:
            current_target = decisions[date_key]
        for symbol in symbols:
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "target_weight": current_target[symbol],
                    "is_rebalance": is_rebalance,
                }
            )
    return pd.DataFrame(rows)


def test_decision_executes_after_next_close_without_look_ahead() -> None:
    dates = ["2024-01-05", "2024-01-08", "2024-01-09"]
    market = market_frame(dates, {"C": [100.0, 200.0, 220.0]})
    portfolio = portfolio_frame(
        dates, ["C"], {"2024-01-05": {"C": 1.0}}
    )

    positions, daily = run_backtest(
        market, portfolio, transaction_cost_bps=0.0, slippage_bps=0.0
    )

    np.testing.assert_allclose(daily["gross_return"], [0.0, 0.0, 0.1])
    assert daily.loc[1, "is_execution"]
    monday_trade = positions.loc[
        positions["date"].eq("2024-01-08"), "trade_weight"
    ].item()
    assert monday_trade == 1.0
    np.testing.assert_allclose(daily["nav"], [1.0, 1.0, 1.1])


def test_weights_drift_without_daily_rebalancing() -> None:
    dates = ["2024-01-04", "2024-01-05", "2024-01-08"]
    market = market_frame(
        dates,
        {"A": [100.0, 100.0, 110.0], "B": [100.0, 100.0, 100.0]},
    )
    portfolio = portfolio_frame(
        dates,
        ["A", "B"],
        {"2024-01-04": {"A": 0.5, "B": 0.5}},
    )

    positions, daily = run_backtest(
        market, portfolio, transaction_cost_bps=0.0, slippage_bps=0.0
    )
    monday = positions.loc[positions["date"].eq("2024-01-08")]

    np.testing.assert_allclose(
        monday["posttrade_weight"], [0.55 / 1.05, 0.50 / 1.05]
    )
    assert monday["trade_weight"].eq(0.0).all()
    no_trade_values = daily.loc[
        2, ["gross_traded_weight", "turnover", "total_cost"]
    ]
    assert no_trade_values.eq(0.0).all()


def test_scheduled_rebalance_trades_from_drifted_pretrade_weights() -> None:
    dates = ["2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"]
    market = market_frame(
        dates,
        {"A": [100.0, 100.0, 110.0, 110.0], "B": [100.0] * 4},
    )
    portfolio = portfolio_frame(
        dates,
        ["A", "B"],
        {
            "2024-01-04": {"A": 0.5, "B": 0.5},
            "2024-01-08": {"A": 0.5, "B": 0.5},
        },
    )

    positions, daily = run_backtest(
        market, portfolio, transaction_cost_bps=0.0, slippage_bps=0.0
    )
    monday = positions.loc[positions["date"].eq("2024-01-08")]
    tuesday = positions.loc[positions["date"].eq("2024-01-09")]

    np.testing.assert_allclose(
        monday["posttrade_weight"], [0.55 / 1.05, 0.50 / 1.05]
    )
    np.testing.assert_allclose(
        tuesday["trade_weight"], [0.5 - 0.55 / 1.05, 0.5 - 0.50 / 1.05]
    )
    np.testing.assert_allclose(daily.loc[3, "gross_traded_weight"], 1.0 / 21.0)
    np.testing.assert_allclose(daily.loc[3, "turnover"], 1.0 / 42.0)


def test_cash_to_stock_turnover_and_linear_costs() -> None:
    dates = ["2024-01-04", "2024-01-05"]
    market = market_frame(dates, {"A": [100.0, 100.0]})
    portfolio = portfolio_frame(
        dates, ["A"], {"2024-01-04": {"A": 1.0}}
    )

    _, daily = run_backtest(
        market, portfolio, transaction_cost_bps=5.0, slippage_bps=10.0
    )

    assert daily.loc[1, "gross_traded_weight"] == 1.0
    assert daily.loc[1, "turnover"] == 1.0
    np.testing.assert_allclose(daily.loc[1, "transaction_cost"], 0.0005)
    np.testing.assert_allclose(daily.loc[1, "slippage_cost"], 0.001)
    np.testing.assert_allclose(daily.loc[1, "total_cost"], 0.0015)
    np.testing.assert_allclose(daily.loc[1, "net_return"], -0.0015)
    np.testing.assert_allclose(daily.loc[1, "nav"], 0.9985)


def test_cost_and_nav_include_same_day_market_return_before_trade() -> None:
    dates = ["2024-01-04", "2024-01-05", "2024-01-08"]
    market = market_frame(dates, {"A": [100.0, 100.0, 110.0]})
    portfolio = portfolio_frame(
        dates,
        ["A"],
        {
            "2024-01-04": {"A": 1.0},
            "2024-01-05": {"A": 0.0},
        },
    )

    positions, daily = run_backtest(
        market, portfolio, transaction_cost_bps=50.0, slippage_bps=50.0
    )

    expected_net_return = 1.1 * 0.99 - 1.0
    np.testing.assert_allclose(daily.loc[2, "gross_return"], 0.1)
    assert daily.loc[2, "gross_traded_weight"] == 1.0
    assert daily.loc[2, "turnover"] == 1.0
    np.testing.assert_allclose(daily.loc[2, "net_return"], expected_net_return)
    np.testing.assert_allclose(daily.loc[2, "nav"], 0.99 * 1.1 * 0.99)
    monday_weight = positions.loc[
        positions["date"].eq("2024-01-08"), "posttrade_weight"
    ].item()
    assert monday_weight == 0.0


def test_missing_observation_uses_past_only_marking() -> None:
    dates = ["2024-01-04", "2024-01-05", "2024-01-08"]
    market = market_frame(
        dates,
        {"A": [100.0, None, 110.0], "B": [50.0, 50.0, 50.0]},
    )
    portfolio = portfolio_frame(dates, ["A", "B"], {})

    positions, _ = run_backtest(market, portfolio)
    a_returns = positions.loc[positions["symbol"].eq("A"), "asset_return"]

    np.testing.assert_allclose(a_returns, [0.0, 0.0, 0.1])


def test_final_decision_has_no_execution_without_later_global_date() -> None:
    dates = ["2024-01-04", "2024-01-05"]
    market = market_frame(dates, {"A": [100.0, 100.0]})
    portfolio = portfolio_frame(
        dates, ["A"], {"2024-01-05": {"A": 1.0}}
    )

    positions, daily = run_backtest(market, portfolio)

    assert not daily["is_execution"].any()
    assert positions["posttrade_weight"].eq(0.0).all()
    assert daily["total_cost"].eq(0.0).all()
