#tests/test_research_robustness.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.research import (
    compute_decay_return,
    compute_factor_decay_ic,
    compute_forward_return,
    run_research_robustness,
    summarize_yearly_ic,
)


def test_lag_zero_decay_equals_one_step_forward_return() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-03",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-02",
                ]
            ),
            "symbol": ["A", "A", "B", "B"],
            "close": [110.0, 100.0, 45.0, 50.0],
        },
        index=[8, 3, 12, 5],
    )

    decay = compute_decay_return(frame, lag=0)
    forward = compute_forward_return(frame, horizon=1)

    pd.testing.assert_series_equal(
        decay.rename("forward_return"),
        forward,
    )


def test_decay_lags_select_the_correct_future_price_interval() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-02", periods=4),
            "symbol": ["A"] * 4,
            "close": [100.0, 110.0, 132.0, 171.6],
        }
    )

    assert compute_decay_return(frame, lag=0).iloc[0] == pytest.approx(0.1)
    assert compute_decay_return(frame, lag=1).iloc[0] == pytest.approx(0.2)
    assert compute_decay_return(frame, lag=2).iloc[0] == pytest.approx(0.3)


def test_decay_ic_uses_formation_date_factor_without_shifting() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    symbols = ["A", "B", "C"]
    close_by_date = [
        [100.0, 100.0, 100.0],
        [100.0, 100.0, 100.0],
        [101.0, 102.0, 103.0],
    ]
    factor_by_date = [
        [1.0, 2.0, 3.0],
        [3.0, 2.0, 1.0],
        [2.0, 1.0, 3.0],
    ]
    rows = []
    for date, closes, factors in zip(
        dates,
        close_by_date,
        factor_by_date,
        strict=True,
    ):
        for symbol, close, factor in zip(
            symbols,
            closes,
            factors,
            strict=True,
        ):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "close": close,
                    "factor": factor,
                }
            )
    frame = pd.DataFrame(rows)

    result = compute_factor_decay_ic(
        frame,
        ["factor"],
        lags=[1],
        min_obs=3,
    )

    formation_date_ic = result.loc[
        result["date"].eq(dates[0]),
        "ic",
    ].iloc[0]
    assert formation_date_ic == pytest.approx(1.0)


def test_yearly_ic_uses_factor_date_and_summarizes_each_year() -> None:
    daily_ic = pd.Series(
        [0.1, 0.2, 0.3, -0.1, np.nan, -0.2],
        index=pd.to_datetime(
            [
                "2023-01-03",
                "2023-06-30",
                "2023-12-29",
                "2024-01-02",
                "2024-06-28",
                "2024-12-30",
            ]
        ),
        name="ic",
    )
    daily_ic.index.name = "date"

    result = summarize_yearly_ic(daily_ic, "momentum_20d")

    assert result["year"].tolist() == [2023, 2024]
    assert result["factor"].tolist() == ["momentum_20d"] * 2
    assert result["valid_ic_days"].tolist() == [3, 2]
    assert result.loc[0, "mean_ic"] == pytest.approx(0.2)
    assert result.loc[0, "icir"] == pytest.approx(2.0)
    assert result.loc[1, "mean_ic"] == pytest.approx(-0.15)
    expected_2024_std = pd.Series([-0.1, -0.2]).std(ddof=1)
    assert result.loc[1, "icir"] == pytest.approx(-0.15 / expected_2024_std)


def test_robustness_runner_returns_all_requested_summary_dimensions() -> None:
    dates = pd.date_range("2024-01-02", periods=4)
    rows = []
    for day, date in enumerate(dates):
        for number, symbol in enumerate(["A", "B", "C", "D", "E"]):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "close": 100.0 + day * (number + 1),
                    "factor": float(number + 1),
                }
            )
    frame = pd.DataFrame(rows)

    result = run_research_robustness(
        frame,
        factor_cols=["factor"],
        horizons=[1, 2],
        decay_lags=[0, 1],
    )

    assert result.horizon_summary["horizon"].tolist() == [1, 2]
    assert result.decay_summary["lag"].tolist() == [0, 1]
    assert result.yearly_ic_summary["year"].tolist() == [2024]
    assert "q5_minus_q1_mean" in result.horizon_summary

    horizon_one_ic = result.horizon_daily_ic.loc[
        result.horizon_daily_ic["horizon"].eq(1),
        "ic",
    ].reset_index(drop=True)
    lag_zero_ic = result.decay_daily_ic.loc[
        result.decay_daily_ic["lag"].eq(0),
        "ic",
    ].reset_index(drop=True)
    pd.testing.assert_series_equal(horizon_one_ic, lag_zero_ic)
