#tests/test_data_quality.py
from __future__ import annotations

import pandas as pd
import pytest

from alphaforge.data import normalize_ohlcv, summarize_ohlcv_quality


def test_unbalanced_panel_quality_summary() -> None:
    observed = {
        "000001.SZ": ("2024-01-02", "2024-01-04", "2024-01-05"),
        "600000.SH": ("2024-01-03", "2024-01-04"),
        "430001.BJ": ("2024-01-05",),
    }
    rows = [
        {
            "date": date,
            "symbol": symbol,
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.5,
            "volume": 1_000.0,
        }
        for symbol, dates in observed.items()
        for date in dates
    ]
    frame = normalize_ohlcv(pd.DataFrame(rows))

    summary = summarize_ohlcv_quality(frame)

    assert summary == {
        "rows": 6,
        "symbols": 3,
        "global_dates": 4,
        "expected_panel_rows": 12,
        "observed_unique_rows": 6,
        "missing_observations": 6,
        "coverage_ratio": pytest.approx(0.5),
        "duplicate_pairs": 0,
        "invalid_observations": 0,
        "internal_missing_observations": 1,
        "boundary_missing_observations": 5,
    }
