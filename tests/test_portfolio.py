#tests/test_portfolio.py
from __future__ import annotations

import numpy as np
import pandas as pd

from alphaforge.portfolio import build_long_only_top_quantile_portfolio


def factor_frame(dates: list[str]) -> pd.DataFrame:
    rows = []
    symbols = [f"S{number:02d}" for number in range(10)]
    for date in pd.to_datetime(dates):
        for number, symbol in enumerate(symbols):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "factor": float(number),
                }
            )
    return pd.DataFrame(rows)


def test_weekly_global_rebalance_and_no_daily_reselection() -> None:
    frame = factor_frame(
        ["2024-01-02", "2024-01-04", "2024-01-08", "2024-01-10", "2024-01-12"]
    )
    frame.loc[frame["date"].eq("2024-01-10"), "factor"] *= -1.0
    frame.loc[frame["date"].eq("2024-01-12"), "factor"] *= -1.0

    result = build_long_only_top_quantile_portfolio(frame, "factor")

    rebalance_dates = result.loc[
        result["is_rebalance"], "date"
    ].drop_duplicates()
    expected_dates = pd.Series(pd.to_datetime(["2024-01-04", "2024-01-12"]))
    pd.testing.assert_series_equal(
        rebalance_dates.reset_index(drop=True),
        expected_dates,
        check_names=False,
    )

    thursday = result.loc[result["date"].eq("2024-01-04")]
    wednesday = result.loc[result["date"].eq("2024-01-10")]
    friday = result.loc[result["date"].eq("2024-01-12")]
    assert set(thursday.loc[thursday["signal"].eq(1), "symbol"]) == {
        "S08",
        "S09",
    }
    assert set(wednesday.loc[wednesday["signal"].eq(1), "symbol"]) == {
        "S08",
        "S09",
    }
    assert set(friday.loc[friday["signal"].eq(1), "symbol"]) == {"S00", "S01"}
    active_weight_sum = (
        result.groupby("date")["target_weight"].sum().loc[lambda value: value.gt(0.0)]
    )
    np.testing.assert_allclose(active_weight_sum, 1.0)


def test_missing_factor_and_portfolio_invariants() -> None:
    frame = factor_frame(
        ["2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12"]
    )
    frame.loc[
        frame["date"].eq("2024-01-12") & frame["symbol"].eq("S09"),
        "factor",
    ] = np.nan

    result = build_long_only_top_quantile_portfolio(frame, "factor")
    decision = result.loc[result["date"].eq("2024-01-12")]

    selected = decision.loc[decision["signal"].eq(1)]
    unselected = decision.loc[decision["signal"].eq(0)]
    assert set(selected["symbol"]) == {"S07", "S08"}
    np.testing.assert_allclose(selected["target_weight"], [0.5, 0.5])
    assert unselected["target_weight"].eq(0.0).all()
    assert decision.loc[decision["symbol"].eq("S09"), "signal"].item() == 0
    assert result["target_weight"].ge(0.0).all()
    assert decision["target_weight"].sum() == 1.0


def test_missing_symbol_row_is_zeroed_at_next_global_rebalance() -> None:
    frame = factor_frame(
        ["2024-01-04", "2024-01-12", "2024-01-15", "2024-01-19"]
    )
    frame = frame.loc[
        ~(frame["date"].eq("2024-01-12") & frame["symbol"].eq("S09"))
    ]
    frame.loc[frame["date"].eq("2024-01-12"), "factor"] = frame.loc[
        frame["date"].eq("2024-01-12"), "factor"
    ].where(frame.loc[frame["date"].eq("2024-01-12"), "symbol"].eq("S08"), 0.0)

    result = build_long_only_top_quantile_portfolio(frame, "factor")

    missing_decision = result.loc[
        result["date"].eq("2024-01-12") & result["symbol"].eq("S09")
    ].iloc[0]
    following_monday = result.loc[
        result["date"].eq("2024-01-15") & result["symbol"].eq("S09")
    ].iloc[0]
    prior_decision = result.loc[
        result["date"].eq("2024-01-04") & result["symbol"].eq("S09")
    ].iloc[0]
    assert prior_decision["signal"] == 1
    assert pd.isna(missing_decision["factor"])
    assert missing_decision["signal"] == 0
    assert missing_decision["target_weight"] == 0.0
    assert following_monday["signal"] == 0
    assert following_monday["target_weight"] == 0.0
    assert len(result) == frame["date"].nunique() * frame["symbol"].nunique()
