from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphaforge.analytics import summarize_performance_by_period
from alphaforge.backtest import run_backtest
from alphaforge.factors import momentum
from alphaforge.research import (
    assign_oos_period,
    compute_period_forward_return,
    run_out_of_sample_research,
)
from scripts.run_out_of_sample import save_out_of_sample_outputs


EXPECTED_PERIODS = ["is_2021_2023", "oos_2024", "oos_2025"]


def test_chronological_period_assignment_is_global_by_date() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2023-12-29",
                    "2023-12-29",
                    "2024-01-02",
                    "2024-01-02",
                    "2025-01-02",
                    "2025-01-02",
                ]
            ),
            "symbol": ["A", "B"] * 3,
        }
    )
    frame["period"] = assign_oos_period(frame["date"])

    assert frame.groupby("date")["period"].nunique().eq(1).all()
    period_dates = frame.groupby("period", sort=False)["date"].agg(["min", "max"])
    assert period_dates.loc["is_2021_2023", "max"] < period_dates.loc[
        "oos_2024", "min"
    ]
    assert period_dates.loc["oos_2024", "max"] < period_dates.loc[
        "oos_2025", "min"
    ]


def test_full_history_factor_preserves_lookback_at_oos_start() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2023-12-27", "2023-12-28", "2023-12-29", "2024-01-02"]
            ),
            "symbol": ["A"] * 4,
            "close": [100.0, 110.0, 121.0, 133.1],
        }
    )

    frame["momentum_2d"] = momentum(frame, window=2)

    oos_start = frame.loc[frame["date"].eq("2024-01-02"), "momentum_2d"].item()
    assert oos_start == pytest.approx(133.1 / 110.0 - 1.0)


def test_research_forward_return_does_not_cross_period_boundary() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-12-30", "2024-12-31", "2025-01-02"]),
            "symbol": ["A"] * 3,
            "close": [100.0, 110.0, 121.0],
        }
    )

    result = compute_period_forward_return(frame)

    assert result.iloc[0] == pytest.approx(0.10)
    assert np.isnan(result.iloc[1])
    assert np.isnan(result.iloc[2])


def test_backtest_state_and_delayed_execution_cross_analytics_boundary() -> None:
    dates = pd.to_datetime(["2023-12-29", "2024-01-02", "2024-01-03"])
    market = pd.DataFrame(
        {"date": dates, "symbol": ["A"] * 3, "close": [100.0, 110.0, 121.0]}
    )
    portfolio = pd.DataFrame(
        {
            "date": dates,
            "symbol": ["A"] * 3,
            "target_weight": [1.0, 1.0, 1.0],
            "is_rebalance": [True, False, False],
        }
    )

    positions, daily = run_backtest(
        market,
        portfolio,
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
    )

    assert daily.loc[1, "is_execution"]
    assert positions.loc[1, "posttrade_weight"] == 1.0
    assert daily.loc[2, "gross_return"] == pytest.approx(0.10)
    assert daily.loc[2, "nav"] == pytest.approx(1.10)


def test_period_performance_compounds_local_returns_not_absolute_nav() -> None:
    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2023-12-28",
                    "2023-12-29",
                    "2024-01-02",
                    "2024-01-03",
                    "2025-01-02",
                    "2025-01-03",
                ]
            ),
            "net_return": [0.01, 0.02, 0.10, -0.05, -0.02, 0.03],
            "turnover": [0.0, 0.1, 0.2, 0.0, 0.3, 0.1],
            "nav": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        }
    )

    result = summarize_performance_by_period(daily, annualization_factor=2)
    result = result.set_index("period")

    expected_2024_nav = 1.10 * 0.95
    assert result.loc["oos_2024", "ending_nav"] == pytest.approx(
        expected_2024_nav
    )
    assert result.loc["oos_2024", "cumulative_return"] == pytest.approx(
        expected_2024_nav - 1.0
    )
    assert result.loc["oos_2024", "ending_nav"] != daily.loc[3, "nav"]


def test_oos_summaries_and_saved_outputs_include_all_periods(
    tmp_path: Path,
) -> None:
    period_dates = [
        ("2023-12-28", "2023-12-29"),
        ("2024-12-30", "2024-12-31"),
        ("2025-12-30", "2025-12-31"),
    ]
    rows = []
    for first_date, second_date in period_dates:
        for number, symbol in enumerate(["A", "B", "C", "D", "E"], start=1):
            rows.append(
                {
                    "date": pd.Timestamp(first_date),
                    "symbol": symbol,
                    "close": 100.0,
                    "factor": float(number),
                }
            )
            rows.append(
                {
                    "date": pd.Timestamp(second_date),
                    "symbol": symbol,
                    "close": 100.0 + number,
                    "factor": float(number),
                }
            )
    factor_data = pd.DataFrame(rows).sort_values(["date", "symbol"])
    factor_summary = run_out_of_sample_research(factor_data, ["factor"])
    np.testing.assert_allclose(
        factor_summary["q5_minus_q1"],
        factor_summary["q5_mean"] - factor_summary["q1_mean"],
    )

    daily = pd.DataFrame(
        {
            "date": [pd.Timestamp(dates[0]) for dates in period_dates],
            "net_return": [0.01, 0.02, 0.03],
            "turnover": [0.1, 0.2, 0.3],
            "nav": [1.01, 1.0302, 1.061106],
        }
    )
    performance = summarize_performance_by_period(daily)

    assert factor_summary["period"].tolist() == EXPECTED_PERIODS
    assert performance["period"].tolist() == EXPECTED_PERIODS
    assert factor_summary.columns.tolist() == [
        "factor",
        "period",
        "valid_ic_days",
        "mean_ic",
        "icir",
        "q1_mean",
        "q5_mean",
        "q5_minus_q1",
    ]
    assert performance.columns.tolist() == [
        "period",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "total_turnover",
        "average_daily_turnover",
        "annualized_turnover",
        "ending_nav",
        "cumulative_return",
    ]

    paths = save_out_of_sample_outputs(factor_summary, performance, tmp_path)
    assert paths["factor_research"].name == "oos_factor_research.csv"
    assert paths["performance"].name == "oos_performance.csv"
    saved_factor = pd.read_csv(paths["factor_research"])
    saved_performance = pd.read_csv(paths["performance"])
    assert saved_factor["period"].tolist() == EXPECTED_PERIODS
    assert saved_performance["period"].tolist() == EXPECTED_PERIODS
