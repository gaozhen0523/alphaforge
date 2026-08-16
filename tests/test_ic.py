#tests/test_ic.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.research import compute_daily_ic, summarize_ic


def ic_frame() -> pd.DataFrame:
    dates = pd.to_datetime(["2024-01-02"] * 5 + ["2024-01-03"] * 5)
    return pd.DataFrame(
        {
            "date": dates,
            "factor": [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
            "forward_return": [1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13, 34, 2, 55, 1], name="row_id"),
    )


def test_perfect_positive_spearman_ic() -> None:
    frame = ic_frame().iloc[:5]

    result = compute_daily_ic(frame, "factor")

    assert result.iloc[0] == pytest.approx(1.0)


def test_perfect_negative_spearman_ic() -> None:
    frame = ic_frame().iloc[5:]

    result = compute_daily_ic(frame, "factor")

    assert result.iloc[0] == pytest.approx(-1.0)


def test_multiple_dates_are_calculated_independently() -> None:
    result = compute_daily_ic(ic_frame(), "factor")

    np.testing.assert_allclose(result, [1.0, -1.0])


def test_pairwise_nan_handling() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"] * 5),
            "factor": [1.0, 2.0, np.nan, 4.0, 5.0],
            "forward_return": [1.0, np.nan, 3.0, 4.0, 2.0],
        }
    )

    result = compute_daily_ic(frame, "factor", min_obs=3)

    assert result.iloc[0] == pytest.approx(0.5)


def test_fewer_than_minimum_valid_observations_returns_nan() -> None:
    frame = ic_frame().iloc[:4]

    result = compute_daily_ic(frame, "factor", min_obs=5)

    assert np.isnan(result.iloc[0])


def test_constant_factor_returns_nan() -> None:
    frame = ic_frame().iloc[:5].copy()
    frame["factor"] = 1.0

    result = compute_daily_ic(frame, "factor")

    assert np.isnan(result.iloc[0])


def test_unsorted_input_produces_date_sorted_ic_series() -> None:
    frame = ic_frame().iloc[[7, 2, 9, 0, 6, 4, 5, 1, 8, 3]]

    result = compute_daily_ic(frame, "factor")

    expected = pd.Series(
        [1.0, -1.0],
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        name="ic",
    )
    expected.index.name = "date"
    pd.testing.assert_series_equal(result, expected)


def test_input_dataframe_is_unchanged() -> None:
    frame = ic_frame()
    original = frame.copy()

    compute_daily_ic(frame, "factor")

    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("min_obs", [1, 0, -1])
def test_min_obs_below_two_is_rejected(min_obs: int) -> None:
    with pytest.raises(ValueError, match="min_obs must be at least 2"):
        compute_daily_ic(ic_frame(), "factor", min_obs=min_obs)


def test_summarize_ic_calculates_mean_sample_std_and_icir() -> None:
    ic = pd.Series([0.1, 0.2, 0.3])

    result = summarize_ic(ic)

    assert list(result.index) == ["mean_ic", "ic_std", "icir", "n_obs"]
    assert result["mean_ic"] == pytest.approx(0.2)
    assert result["ic_std"] == pytest.approx(0.1)
    assert result["icir"] == pytest.approx(2.0)
    assert result["n_obs"] == 3


def test_summarize_ic_ignores_nan_observations() -> None:
    ic = pd.Series([0.1, np.nan, 0.3])

    result = summarize_ic(ic)

    valid = pd.Series([0.1, 0.3])
    expected_std = valid.std(ddof=1)
    assert result["mean_ic"] == pytest.approx(valid.mean())
    assert result["ic_std"] == pytest.approx(expected_std)
    assert result["icir"] == pytest.approx(valid.mean() / expected_std)
    assert result["n_obs"] == 2


def test_summarize_ic_returns_nan_icir_for_zero_std() -> None:
    result = summarize_ic(pd.Series([0.2, 0.2, 0.2]))

    assert result["ic_std"] == 0.0
    assert np.isnan(result["icir"])


def test_summarize_ic_single_observation_has_nan_std_and_icir() -> None:
    result = summarize_ic(pd.Series([np.nan, 0.25, np.nan]))

    assert result["mean_ic"] == pytest.approx(0.25)
    assert np.isnan(result["ic_std"])
    assert np.isnan(result["icir"])
    assert result["n_obs"] == 1


def test_summarize_ic_all_nan_has_no_valid_observations() -> None:
    result = summarize_ic(pd.Series([np.nan, np.nan]))

    assert np.isnan(result["mean_ic"])
    assert np.isnan(result["ic_std"])
    assert np.isnan(result["icir"])
    assert result["n_obs"] == 0


def test_summarize_ic_does_not_modify_input() -> None:
    ic = pd.Series([0.1, np.nan, 0.3], name="ic")
    original = ic.copy()

    summarize_ic(ic)

    pd.testing.assert_series_equal(ic, original)

def test_constant_return_returns_nan() -> None:
    frame = ic_frame().iloc[:5].copy()
    frame["forward_return"] = 1.0

    result = compute_daily_ic(frame, "factor")

    assert np.isnan(result.iloc[0])
