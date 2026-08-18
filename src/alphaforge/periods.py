#src/alphaforge/periods.py
"""Fixed chronological periods shared by Day 10 research and analytics."""

from __future__ import annotations

import pandas as pd


OOS_PERIODS = (
    (
        "is_2021_2023",
        pd.Timestamp("2021-01-01"),
        pd.Timestamp("2023-12-31"),
    ),
    ("oos_2024", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31")),
    ("oos_2025", pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31")),
)


def assign_oos_period(dates: pd.Series) -> pd.Series:
    """Assign the fixed Day 10 period from each formation date."""

    dates = pd.to_datetime(dates)
    result = pd.Series(pd.NA, index=dates.index, dtype="string", name="period")
    for period, start, end in OOS_PERIODS:
        result.loc[dates.between(start, end)] = period
    return result
