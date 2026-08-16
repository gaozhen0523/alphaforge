from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.research import compute_factor_correlation


def correlation_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 5 + ["2024-01-03"] * 5),
            "factor_a": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
            "factor_b": [1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0],
            "factor_c": [5.0, 4.0, 3.0, 2.0, 1.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13, 34, 2, 55, 1], name="row_id"),
    )


def pairwise_nan_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 5),
            "factor_a": [1.0, 2.0, 3.0, 4.0, np.nan],
            "factor_b": [1.0, 2.0, 3.0, np.nan, 5.0],
            "factor_c": [np.nan, 2.0, 3.0, 4.0, 5.0],
        }
    )


def test_perfect_positive_factor_correlation() -> None:
    frame = correlation_frame().iloc[:5]

    result = compute_factor_correlation(frame, ["factor_a", "factor_b"])

    assert result.loc["factor_a", "factor_b"] == pytest.approx(1.0)


def test_perfect_negative_factor_correlation() -> None:
    frame = correlation_frame().iloc[:5]

    result = compute_factor_correlation(frame, ["factor_a", "factor_c"])

    assert result.loc["factor_a", "factor_c"] == pytest.approx(-1.0)


def test_daily_correlations_are_equally_averaged() -> None:
    result = compute_factor_correlation(
        correlation_frame(),
        ["factor_a", "factor_b"],
    )

    assert result.loc["factor_a", "factor_b"] == pytest.approx(0.0)


def test_pairwise_nan_handling_does_not_require_complete_cases() -> None:
    result = compute_factor_correlation(
        pairwise_nan_frame(),
        ["factor_a", "factor_b", "factor_c"],
        min_obs=3,
    )

    assert result.loc["factor_a", "factor_b"] == pytest.approx(1.0)
    assert result.loc["factor_a", "factor_c"] == pytest.approx(1.0)
    assert result.loc["factor_b", "factor_c"] == pytest.approx(1.0)


def test_insufficient_paired_observations_returns_nan() -> None:
    result = compute_factor_correlation(
        pairwise_nan_frame(),
        ["factor_a", "factor_b"],
        min_obs=4,
    )

    assert np.isnan(result.loc["factor_a", "factor_b"])


def test_factor_correlation_output_is_symmetric() -> None:
    result = compute_factor_correlation(
        correlation_frame(),
        ["factor_a", "factor_b", "factor_c"],
    )

    pd.testing.assert_frame_equal(result, result.T)


def test_factor_order_matches_input_order() -> None:
    factor_cols = ["factor_c", "factor_a", "factor_b"]

    result = compute_factor_correlation(correlation_frame(), factor_cols)

    assert result.index.tolist() == factor_cols
    assert result.columns.tolist() == factor_cols


def test_unsorted_input_does_not_affect_factor_correlation() -> None:
    frame = correlation_frame()
    shuffled = frame.iloc[[7, 2, 9, 0, 6, 4, 5, 1, 8, 3]]
    factor_cols = ["factor_a", "factor_b", "factor_c"]

    result = compute_factor_correlation(shuffled, factor_cols)
    expected = compute_factor_correlation(frame, factor_cols)

    pd.testing.assert_frame_equal(result, expected)


def test_factor_correlation_does_not_modify_input() -> None:
    frame = correlation_frame()
    original = frame.copy()

    compute_factor_correlation(frame, ["factor_a", "factor_b", "factor_c"])

    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("min_obs", [1, 0, -1])
def test_min_obs_below_two_is_rejected(min_obs: int) -> None:
    with pytest.raises(ValueError, match="min_obs must be at least 2"):
        compute_factor_correlation(
            correlation_frame(),
            ["factor_a", "factor_b"],
            min_obs=min_obs,
        )
