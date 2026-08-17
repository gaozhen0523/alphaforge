#tests/test_analytics.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.analytics import (
    annualized_return,
    annualized_volatility,
    max_drawdown,
    sharpe_ratio,
    summarize_performance,
)
from alphaforge.backtest import run_backtest


def test_annualized_return_uses_compounded_growth() -> None:
    daily_return = pd.Series([0.10, 0.10])

    result = annualized_return(daily_return, annualization_factor=2)

    assert result == pytest.approx(0.21)


def test_volatility_and_sharpe_use_sample_std_and_sqrt_annualization() -> None:
    daily_return = pd.Series([0.01, -0.02, 0.03])
    expected_std = np.std(daily_return, ddof=1)

    volatility = annualized_volatility(
        daily_return, annualization_factor=252
    )
    sharpe = sharpe_ratio(daily_return, annualization_factor=252)

    assert volatility == pytest.approx(expected_std * np.sqrt(252))
    assert sharpe == pytest.approx(
        daily_return.mean() / expected_std * np.sqrt(252)
    )


def test_max_drawdown_uses_running_nav_peak() -> None:
    nav = pd.Series([1.0, 1.2, 0.9, 1.1])

    assert max_drawdown(nav) == pytest.approx(-0.25)


def test_flat_portfolio_metrics() -> None:
    daily_return = pd.Series([0.0, 0.0, 0.0])
    nav = pd.Series([1.0, 1.0, 1.0])

    assert annualized_return(daily_return) == 0.0
    assert annualized_volatility(daily_return) == 0.0
    assert max_drawdown(nav) == 0.0
    assert np.isnan(sharpe_ratio(daily_return))


def test_summary_directly_consumes_backtest_daily_output() -> None:
    dates = pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-08"])
    market = pd.DataFrame(
        {
            "date": dates,
            "symbol": ["A", "A", "A"],
            "close": [100.0, 100.0, 110.0],
        }
    )
    portfolio = pd.DataFrame(
        {
            "date": dates,
            "symbol": ["A", "A", "A"],
            "target_weight": [1.0, 1.0, 1.0],
            "is_rebalance": [True, False, False],
        }
    )
    _, daily = run_backtest(
        market,
        portfolio,
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
    )

    result = summarize_performance(daily)

    assert result["ending_nav"] == pytest.approx(daily["nav"].iloc[-1])
    assert result["cumulative_return"] == pytest.approx(0.10)
    assert result["total_turnover"] == pytest.approx(daily["turnover"].sum())
    assert result["average_daily_turnover"] == pytest.approx(
        daily["turnover"].mean()
    )
    assert result["annualized_turnover"] == pytest.approx(
        daily["turnover"].mean() * 252
    )
    assert result["annualized_volatility"] >= 0.0
    assert result["max_drawdown"] <= 0.0
