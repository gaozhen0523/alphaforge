from __future__ import annotations

import numpy as np
import pandas as pd

from alphaforge.research import cross_sectional_rank


def ranking_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-02",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-03",
                    "2024-01-03",
                ]
            ),
            "symbol": ["A", "B", "C", "A", "B", "C"],
            "factor": [30.0, 10.0, 20.0, 4.0, 2.0, 6.0],
        },
        index=pd.Index([8, 3, 12, 5, 21, 13], name="row_id"),
    )


def test_single_date_ranking() -> None:
    frame = ranking_frame().iloc[:3]

    result = cross_sectional_rank(frame, "factor")

    np.testing.assert_allclose(result, [1.0, 1.0 / 3.0, 2.0 / 3.0])


def test_multiple_dates_are_ranked_independently() -> None:
    frame = ranking_frame()

    result = cross_sectional_rank(frame, "factor")

    np.testing.assert_allclose(
        result,
        [1.0, 1.0 / 3.0, 2.0 / 3.0, 2.0 / 3.0, 1.0 / 3.0, 1.0],
    )


def test_nan_factor_is_preserved() -> None:
    frame = ranking_frame().iloc[:3].copy()
    frame.loc[3, "factor"] = np.nan

    result = cross_sectional_rank(frame, "factor")

    np.testing.assert_allclose(result.loc[[8, 12]], [1.0, 0.5])
    assert np.isnan(result.loc[3])


def test_ties_use_average_rank() -> None:
    frame = ranking_frame().iloc[:3].copy()
    frame["factor"] = [10.0, 10.0, 30.0]

    result = cross_sectional_rank(frame, "factor")

    np.testing.assert_allclose(result, [0.5, 0.5, 1.0])


def test_unsorted_input_is_ranked_within_each_date() -> None:
    frame = ranking_frame().iloc[[4, 2, 0, 5, 1, 3]]

    result = cross_sectional_rank(frame, "factor")

    np.testing.assert_allclose(
        result,
        [1.0 / 3.0, 2.0 / 3.0, 1.0, 1.0, 1.0 / 3.0, 2.0 / 3.0],
    )


def test_output_index_and_row_order_match_input() -> None:
    frame = ranking_frame().iloc[[4, 2, 0, 5, 1, 3]]

    result = cross_sectional_rank(frame, "factor")

    assert result.index.equals(frame.index)


def test_input_dataframe_is_unchanged() -> None:
    frame = ranking_frame()
    original = frame.copy()

    cross_sectional_rank(frame, "factor")

    pd.testing.assert_frame_equal(frame, original)
