#tests/test_factor_combination.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.backtest import run_backtest
from alphaforge.portfolio import build_long_only_top_quantile_portfolio
from alphaforge.research import (
    combine_factors_by_rank,
    combine_factors_by_zscore,
    compute_forward_return,
    cross_sectional_zscore,
    run_out_of_sample_research,
)
from scripts.run_factor_combination import (
    add_period_quantile_means,
    summarize_full_sample_research,
)


FACTOR_DIRECTIONS = {
    "momentum_20d": 1,
    "reversal_5d": 1,
    "volatility_20d": -1,
}


def two_date_factor_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 3 + ["2024-01-03"] * 3),
            "symbol": ["A", "B", "C"] * 2,
            "momentum_20d": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0],
            "reversal_5d": [2.0, 4.0, 6.0, 20.0, 40.0, 60.0],
            "volatility_20d": [3.0, 2.0, 1.0, 3000.0, 2000.0, 1000.0],
        }
    )


def test_normalization_is_cross_sectional_by_date() -> None:
    frame = two_date_factor_frame()

    zscore = cross_sectional_zscore(frame, "momentum_20d")
    ranked = combine_factors_by_rank(frame, FACTOR_DIRECTIONS)
    combined_zscore = combine_factors_by_zscore(frame, FACTOR_DIRECTIONS)

    np.testing.assert_allclose(zscore.iloc[:3], zscore.iloc[3:])
    np.testing.assert_allclose(ranked.iloc[:3], ranked.iloc[3:])
    np.testing.assert_allclose(combined_zscore.iloc[:3], combined_zscore.iloc[3:])


def test_zero_cross_sectional_std_produces_nan_zscore() -> None:
    frame = two_date_factor_frame()
    frame["momentum_20d"] = 1.0

    result = cross_sectional_zscore(frame, "momentum_20d")

    assert result.isna().all()


@pytest.mark.parametrize(
    ("combine", "factor_col", "direction", "expected_best"),
    [
        (combine_factors_by_rank, "momentum_20d", 1, "C"),
        (combine_factors_by_rank, "volatility_20d", -1, "C"),
        (combine_factors_by_zscore, "momentum_20d", 1, "C"),
        (combine_factors_by_zscore, "volatility_20d", -1, "C"),
    ],
)
def test_ex_ante_direction_controls_score_order(
    combine,
    factor_col: str,
    direction: int,
    expected_best: str,
) -> None:
    frame = two_date_factor_frame().iloc[:3]

    score = combine(frame, {factor_col: direction})

    assert frame.loc[score.idxmax(), "symbol"] == expected_best


def test_combinations_require_every_factor_to_be_valid() -> None:
    frame = two_date_factor_frame().iloc[:3].copy()
    frame.loc[0, "momentum_20d"] = np.nan
    frame.loc[1, "reversal_5d"] = np.nan
    frame.loc[2, "volatility_20d"] = np.nan

    ranked = combine_factors_by_rank(frame, FACTOR_DIRECTIONS)
    zscore = combine_factors_by_zscore(frame, FACTOR_DIRECTIONS)

    assert ranked.isna().all()
    assert zscore.isna().all()


def test_future_factor_changes_do_not_change_past_combinations() -> None:
    frame = two_date_factor_frame()
    past = frame["date"].eq("2024-01-02")
    expected_rank = combine_factors_by_rank(frame, FACTOR_DIRECTIONS).loc[past]
    expected_zscore = combine_factors_by_zscore(frame, FACTOR_DIRECTIONS).loc[past]
    changed = frame.copy()
    changed.loc[~past, list(FACTOR_DIRECTIONS)] = [
        [900.0, -20.0, 7.0],
        [-100.0, 50.0, 1.0],
        [3.0, 800.0, 99.0],
    ]

    actual_rank = combine_factors_by_rank(changed, FACTOR_DIRECTIONS).loc[past]
    actual_zscore = combine_factors_by_zscore(changed, FACTOR_DIRECTIONS).loc[past]

    pd.testing.assert_series_equal(actual_rank, expected_rank)
    pd.testing.assert_series_equal(actual_zscore, expected_zscore)


def test_research_outputs_expose_every_quantile_mean() -> None:
    rows = []
    period_dates = (
        ("2023-12-28", "2023-12-29"),
        ("2024-12-30", "2024-12-31"),
        ("2025-12-30", "2025-12-31"),
    )
    for first_date, second_date in period_dates:
        for number, symbol in enumerate(["A", "B", "C", "D", "E"], start=1):
            rows.extend(
                [
                    {
                        "date": pd.Timestamp(first_date),
                        "symbol": symbol,
                        "close": 100.0,
                        "factor": float(number),
                    },
                    {
                        "date": pd.Timestamp(second_date),
                        "symbol": symbol,
                        "close": 100.0 + number,
                        "factor": float(number),
                    },
                ]
            )
    data = (
        pd.DataFrame(rows)
        .sort_values(["date", "symbol"])
        .reset_index(drop=True)
    )
    data["forward_return"] = compute_forward_return(data)

    full = summarize_full_sample_research(data, ["factor"], n_quantiles=5)
    period = run_out_of_sample_research(data, ["factor"])
    period = add_period_quantile_means(
        data,
        period,
        ["factor"],
        horizon=1,
        n_quantiles=5,
    )

    quantile_columns = [f"q{quantile}_mean" for quantile in range(1, 6)]
    assert set(quantile_columns).issubset(full.columns)
    assert set(quantile_columns).issubset(period.columns)
    np.testing.assert_allclose(
        period[quantile_columns],
        [[0.01, 0.02, 0.03, 0.04, 0.05]] * 3,
    )
    np.testing.assert_allclose(period["q5_minus_q1"], 0.04)


@pytest.mark.parametrize(
    ("combine", "factor_col"),
    [
        (combine_factors_by_rank, "combined_rank"),
        (combine_factors_by_zscore, "combined_zscore"),
    ],
)
def test_composite_integrates_with_existing_portfolio_and_backtest_timing(
    combine,
    factor_col: str,
) -> None:
    dates = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"]
    )
    rows = []
    for date in dates:
        for number in range(10):
            rows.append(
                {
                    "date": date,
                    "symbol": f"S{number:02d}",
                    "close": 110.0 if date == dates[-1] and number >= 8 else 100.0,
                    "momentum_20d": float(number),
                    "reversal_5d": float(number),
                    "volatility_20d": float(10 - number),
                }
            )
    market = pd.DataFrame(rows)
    market[factor_col] = combine(market, FACTOR_DIRECTIONS)

    portfolio = build_long_only_top_quantile_portfolio(market, factor_col)
    _, daily = run_backtest(
        market,
        portfolio,
        transaction_cost_bps=0.0,
        slippage_bps=0.0,
    )

    assert daily.loc[2, "is_execution"]
    np.testing.assert_allclose(daily["gross_return"], [0.0, 0.0, 0.0, 0.1])
