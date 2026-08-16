#tests/test_returns.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphaforge.research import compute_forward_return


def return_frame() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                ]
            ),
            "symbol": ["A", "A", "A", "B", "B", "B"],
            "close": [100.0, 110.0, 121.0, 50.0, 40.0, 60.0],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13], name="row_id"),
    )
    return frame


def test_single_symbol_forward_return_and_trailing_nan() -> None:
    frame = return_frame().iloc[:3]

    result = compute_forward_return(frame)

    np.testing.assert_allclose(result.iloc[:2], [0.1, 0.1])
    assert np.isnan(result.iloc[2])


def test_forward_return_is_isolated_by_symbol() -> None:
    frame = return_frame()

    result = compute_forward_return(frame)

    np.testing.assert_allclose(result.iloc[[0, 1, 3, 4]], [0.1, 0.1, -0.2, 0.5])
    assert result.iloc[[2, 5]].isna().all()


def test_unsorted_input_is_calculated_by_date_and_restored() -> None:
    frame = return_frame().iloc[[4, 2, 0, 5, 1, 3]]

    result = compute_forward_return(frame)

    expected = pd.Series(
        [0.5, np.nan, 0.1, np.nan, 0.1, -0.2],
        index=frame.index,
        name="forward_return",
    )
    pd.testing.assert_series_equal(result, expected)


def test_horizon_greater_than_one_uses_future_available_observations() -> None:
    frame = return_frame()

    result = compute_forward_return(frame, horizon=2)

    np.testing.assert_allclose(result.iloc[[0, 3]], [0.21, 0.2])
    assert result.iloc[[1, 2, 4, 5]].isna().all()


def test_output_index_matches_input_index_without_modifying_input() -> None:
    frame = return_frame().iloc[[4, 2, 0, 5, 1, 3]]
    original = frame.copy()

    result = compute_forward_return(frame)

    assert result.index.equals(frame.index)
    pd.testing.assert_frame_equal(frame, original)


@pytest.mark.parametrize("horizon", [0, -1])
def test_non_positive_horizon_is_rejected(horizon: int) -> None:
    with pytest.raises(ValueError, match="horizon must be positive"):
        compute_forward_return(return_frame(), horizon=horizon)
