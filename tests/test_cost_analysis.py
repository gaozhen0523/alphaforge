#tests/test_cost_analysis.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.analytics import (
    run_cost_sensitivity,
    summarize_performance,
    summarize_turnover,
)
from alphaforge.backtest import run_backtest


@pytest.fixture
def traded_strategy() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2024-01-02", periods=5)
    market = pd.DataFrame(
        {
            "date": list(dates) * 2,
            "symbol": ["A"] * 5 + ["B"] * 5,
            "close": [100.0, 100.0, 110.0, 110.0, 110.0]
            + [100.0, 100.0, 100.0, 100.0, 120.0],
        }
    ).sort_values(["date", "symbol"])

    rows = []
    for day, date in enumerate(dates):
        target = {"A": 1.0, "B": 0.0} if day < 2 else {
            "A": 0.0,
            "B": 1.0,
        }
        for symbol in ("A", "B"):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "target_weight": target[symbol],
                    "is_rebalance": day in (0, 2),
                }
            )
    return market.reset_index(drop=True), pd.DataFrame(rows)


def test_zero_cost_matches_gross_performance(
    traded_strategy: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    market, portfolio = traded_strategy
    _, daily = run_backtest(
        market,
        portfolio,
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
    )
    sensitivity = run_cost_sensitivity(market, portfolio, [(0.0, 0.0)])
    result = sensitivity.iloc[0]

    np.testing.assert_allclose(daily["net_return"], daily["gross_return"])
    assert result["gross_ending_nav"] == pytest.approx(
        result["ending_nav"]
    )
    assert result["gross_cumulative_return"] == pytest.approx(
        result["cumulative_return"]
    )


def test_higher_cost_reduces_performance(
    traded_strategy: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    market, portfolio = traded_strategy
    sensitivity = run_cost_sensitivity(
        market,
        portfolio,
        [(0.0, 0.0), (5.0, 5.0), (10.0, 10.0)],
    )

    assert sensitivity["ending_nav"].is_monotonic_decreasing
    assert sensitivity["cumulative_return"].is_monotonic_decreasing


def test_cost_does_not_change_trading(
    traded_strategy: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    market, portfolio = traded_strategy
    sensitivity = run_cost_sensitivity(
        market,
        portfolio,
        [(0.0, 0.0), (5.0, 5.0), (10.0, 10.0)],
    )

    assert sensitivity["total_gross_traded_weight"].nunique() == 1
    assert sensitivity["total_turnover"].nunique() == 1

    daily_results = [
        run_backtest(market, portfolio, cost, cost)[1]
        for cost in (0.0, 5.0, 10.0)
    ]
    for daily in daily_results[1:]:
        np.testing.assert_array_equal(
            daily["gross_traded_weight"],
            daily_results[0]["gross_traded_weight"],
        )
        np.testing.assert_array_equal(
            daily["turnover"], daily_results[0]["turnover"]
        )


def test_frozen_baseline_reproduces_existing_accounting(
    traded_strategy: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    market, portfolio = traded_strategy
    _, daily = run_backtest(
        market,
        portfolio,
        transaction_cost_bps=5.0,
        slippage_bps=5.0,
    )
    direct = summarize_performance(daily)
    sensitivity = run_cost_sensitivity(
        market,
        portfolio,
        [(5.0, 5.0)],
    ).iloc[0]

    assert sensitivity["annualized_return"] == pytest.approx(
        direct["annualized_return"]
    )
    assert sensitivity["annualized_volatility"] == pytest.approx(
        direct["annualized_volatility"]
    )
    assert sensitivity["sharpe"] == pytest.approx(direct["sharpe_ratio"])
    assert sensitivity["max_drawdown"] == pytest.approx(
        direct["max_drawdown"]
    )
    assert sensitivity["ending_nav"] == pytest.approx(direct["ending_nav"])
    assert sensitivity["cumulative_return"] == pytest.approx(
        direct["cumulative_return"]
    )

    turnover = summarize_turnover(daily)
    assert turnover["execution_count"] == 2
    assert turnover["total_gross_traded_weight"] == pytest.approx(3.0)
    assert turnover["total_turnover"] == pytest.approx(2.0)
