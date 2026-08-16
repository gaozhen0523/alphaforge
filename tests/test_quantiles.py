from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.research import (
    assign_quantiles,
    compute_quantile_returns,
    summarize_quantile_returns,
)


def quantile_frame() -> pd.DataFrame:
    dates = pd.to_datetime(["2024-01-02"] * 5 + ["2024-01-03"] * 5)
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": ["A", "B", "C", "D", "E"] * 2,
            "factor": [10.0, 20.0, 30.0, 40.0, 50.0, 50.0, 40.0, 30.0, 20.0, 10.0],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13, 34, 2, 55, 1], name="row_id"),
    )


def test_basic_single_date_assignment() -> None:
    result = assign_quantiles(quantile_frame().iloc[:5], "factor")

    expected = pd.Series(
        [1, 2, 3, 4, 5],
        index=quantile_frame().index[:5],
        dtype="Int64",
        name="quantile",
    )
    pd.testing.assert_series_equal(result, expected)


def test_q1_is_lowest_and_qn_is_highest() -> None:
    frame = quantile_frame().iloc[:5]

    result = assign_quantiles(frame, "factor")

    assert result.loc[frame["factor"].idxmin()] == 1
    assert result.loc[frame["factor"].idxmax()] == 5


def test_multiple_dates_are_assigned_independently() -> None:
    result = assign_quantiles(quantile_frame(), "factor")

    expected = pd.Series(
        [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
        index=quantile_frame().index,
        dtype="Int64",
        name="quantile",
    )
    pd.testing.assert_series_equal(result, expected)


def test_nan_factor_produces_missing_quantile() -> None:
    frame = quantile_frame().iloc[:5].copy()
    frame.loc[12, "factor"] = np.nan

    result = assign_quantiles(frame, "factor")

    assert pd.isna(result.loc[12])
    assert result.dtype == "Int64"


def test_tied_factor_values_are_not_split() -> None:
    frame = quantile_frame().iloc[:5].copy()
    frame["factor"] = [10.0, 20.0, 20.0, 40.0, 50.0]

    result = assign_quantiles(frame, "factor")

    assert result.loc[3] == result.loc[12] == 3


def test_unsorted_input_preserves_index_and_row_order() -> None:
    frame = quantile_frame().iloc[[7, 2, 9, 0, 6, 4, 5, 1, 8, 3]]

    result = assign_quantiles(frame, "factor")

    expected = pd.Series(
        [3, 3, 1, 1, 4, 5, 5, 2, 2, 4],
        index=frame.index,
        dtype="Int64",
        name="quantile",
    )
    pd.testing.assert_series_equal(result, expected)


def test_custom_three_quantiles() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 6),
            "factor": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )

    result = assign_quantiles(frame, "factor", n_quantiles=3)

    expected = pd.Series([1, 1, 2, 2, 3, 3], dtype="Int64", name="quantile")
    pd.testing.assert_series_equal(result, expected)


@pytest.mark.parametrize("n_quantiles", [1, 0, -1])
def test_fewer_than_two_quantiles_is_rejected(n_quantiles: int) -> None:
    with pytest.raises(ValueError, match="n_quantiles must be at least 2"):
        assign_quantiles(quantile_frame(), "factor", n_quantiles=n_quantiles)


def test_input_dataframe_is_unchanged() -> None:
    frame = quantile_frame()
    original = frame.copy()

    assign_quantiles(frame, "factor")

    pd.testing.assert_frame_equal(frame, original)


def quantile_return_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-02",
                    "2024-01-02",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-03",
                    "2024-01-03",
                    "2024-01-03",
                ]
            ),
            "quantile": pd.array([1, 1, 5, 5, 1, 1, 5, 5], dtype="Int64"),
            "forward_return": [0.01, 0.03, 0.10, 0.20, -0.02, 0.02, -0.10, 0.10],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13, 34, 2], name="row_id"),
    )


def test_single_date_quantile_arithmetic_means() -> None:
    result = compute_quantile_returns(quantile_return_frame().iloc[:4])

    assert result.loc[pd.Timestamp("2024-01-02"), 1] == pytest.approx(0.02)
    assert result.loc[pd.Timestamp("2024-01-02"), 5] == pytest.approx(0.15)


def test_multiple_dates_are_aggregated_independently() -> None:
    result = compute_quantile_returns(quantile_return_frame())

    np.testing.assert_allclose(result.loc[:, [1, 5]], [[0.02, 0.15], [0.0, 0.0]])


def test_nan_returns_are_ignored_within_quantile() -> None:
    frame = quantile_return_frame().iloc[:4].copy()
    frame.loc[3, "forward_return"] = np.nan

    result = compute_quantile_returns(frame)

    assert result.loc[pd.Timestamp("2024-01-02"), 1] == pytest.approx(0.01)


def test_missing_quantile_for_date_remains_nan() -> None:
    result = compute_quantile_returns(quantile_return_frame())

    assert np.isnan(result.loc[pd.Timestamp("2024-01-02"), 3])
    assert np.isnan(result.loc[pd.Timestamp("2024-01-03"), 3])


def test_output_always_contains_all_quantile_columns() -> None:
    result = compute_quantile_returns(quantile_return_frame())

    assert result.columns.tolist() == [1, 2, 3, 4, 5]
    assert result.columns.name == "quantile"


def test_unsorted_input_produces_date_sorted_output() -> None:
    frame = quantile_return_frame().iloc[[6, 1, 4, 0, 7, 3, 5, 2]]

    result = compute_quantile_returns(frame)

    expected_index = pd.DatetimeIndex(
        ["2024-01-02", "2024-01-03"],
        name="date",
    )
    assert result.index.equals(expected_index)
    np.testing.assert_allclose(result.loc[:, [1, 5]], [[0.02, 0.15], [0.0, 0.0]])


def test_custom_number_of_quantiles() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 3),
            "quantile": pd.Series([1, 2, 3], dtype="Int64"),
            "forward_return": [0.01, 0.02, 0.03],
        }
    )

    result = compute_quantile_returns(frame, n_quantiles=3)

    assert result.columns.tolist() == [1, 2, 3]
    np.testing.assert_allclose(result.iloc[0], [0.01, 0.02, 0.03])


@pytest.mark.parametrize("n_quantiles", [1, 0, -1])
def test_quantile_returns_rejects_fewer_than_two_quantiles(
    n_quantiles: int,
) -> None:
    with pytest.raises(ValueError, match="n_quantiles must be at least 2"):
        compute_quantile_returns(
            quantile_return_frame(),
            n_quantiles=n_quantiles,
        )


def test_compute_quantile_returns_does_not_modify_input() -> None:
    frame = quantile_return_frame()
    original = frame.copy()

    compute_quantile_returns(frame)

    pd.testing.assert_frame_equal(frame, original)


def daily_quantile_return_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            1: [0.01, 0.03, np.nan],
            2: [0.02, 0.04, 0.06],
            3: [0.00, 0.10, 0.20],
            4: [-0.01, 0.01, 0.03],
            5: [0.10, np.nan, 0.30],
        },
        index=pd.date_range("2024-01-02", periods=3, name="date"),
    ).rename_axis("quantile", axis="columns")


def test_quantile_mean_returns_are_calculated_over_dates() -> None:
    result = summarize_quantile_returns(daily_quantile_return_matrix())

    expected = pd.Series(
        {
            "q1_mean": 0.02,
            "q2_mean": 0.04,
            "q3_mean": 0.10,
            "q4_mean": 0.01,
            "q5_mean": 0.20,
            "top_minus_bottom": 0.09,
        }
    )
    pd.testing.assert_series_equal(result, expected)


def test_quantile_summary_ignores_nan_daily_observations() -> None:
    result = summarize_quantile_returns(daily_quantile_return_matrix())

    assert result["q1_mean"] == pytest.approx(0.02)
    assert result["q5_mean"] == pytest.approx(0.20)


def test_top_minus_bottom_uses_paired_daily_spreads() -> None:
    result = summarize_quantile_returns(daily_quantile_return_matrix())

    assert result["top_minus_bottom"] == pytest.approx(0.09)


def test_paired_spread_differs_from_difference_of_independent_means() -> None:
    quantile_returns = daily_quantile_return_matrix()

    result = summarize_quantile_returns(quantile_returns)
    difference_of_means = quantile_returns[5].mean() - quantile_returns[1].mean()

    assert difference_of_means == pytest.approx(0.18)
    assert result["top_minus_bottom"] == pytest.approx(0.09)
    assert result["top_minus_bottom"] != pytest.approx(difference_of_means)


def test_quantile_summary_supports_custom_number_of_quantiles() -> None:
    quantile_returns = daily_quantile_return_matrix().loc[:, [1, 2, 3]]

    result = summarize_quantile_returns(quantile_returns)

    assert result.index.tolist() == [
        "q1_mean",
        "q2_mean",
        "q3_mean",
        "top_minus_bottom",
    ]
    assert result["top_minus_bottom"] == pytest.approx(0.03)


def test_summarize_quantile_returns_does_not_modify_input() -> None:
    quantile_returns = daily_quantile_return_matrix()
    original = quantile_returns.copy()

    summarize_quantile_returns(quantile_returns)

    pd.testing.assert_frame_equal(quantile_returns, original)
