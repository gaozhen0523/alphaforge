#src/alphaforge/research/ic.py
"""Information coefficient calculations."""

from __future__ import annotations

import pandas as pd


def compute_daily_ic(
    df: pd.DataFrame,
    factor_col: str,
    return_col: str = "forward_return",
    min_obs: int = 5,
) -> pd.Series:
    """Return cross-sectional Spearman IC for each date."""

    if min_obs < 2:
        raise ValueError("min_obs must be at least 2")

    daily_ic = {}
    for date, group in df.groupby("date", sort=True):
        paired = group.loc[:, [factor_col, return_col]].dropna()
        daily_ic[date] = (
            paired[factor_col].corr(paired[return_col], method="spearman")
            if len(paired) >= min_obs
            else float("nan")
        )

    result = pd.Series(daily_ic, dtype="float64", name="ic")
    result.index.name = "date"
    return result


def summarize_ic(ic: pd.Series) -> pd.Series:
    """Summarize valid daily IC observations without annualizing ICIR."""

    valid = ic.dropna()
    mean_ic = valid.mean()
    ic_std = valid.std(ddof=1)
    if len(valid) > 1 and valid.nunique() == 1:
        ic_std = 0.0
    icir = (
        mean_ic / ic_std
        if pd.notna(ic_std) and ic_std != 0
        else float("nan")
    )

    return pd.Series(
        {
            "mean_ic": mean_ic,
            "ic_std": ic_std,
            "icir": icir,
            "n_obs": len(valid),
        }
    )


def summarize_yearly_ic(ic: pd.Series, factor: str) -> pd.DataFrame:
    """Summarize daily IC by the calendar year of its formation-date index."""

    rows = []
    for year, yearly_ic in ic.groupby(ic.index.year, sort=True):
        summary = summarize_ic(yearly_ic)
        rows.append(
            {
                "factor": factor,
                "year": int(year),
                "valid_ic_days": int(summary["n_obs"]),
                "mean_ic": summary["mean_ic"],
                "icir": summary["icir"],
            }
        )

    return pd.DataFrame(
        rows,
        columns=["factor", "year", "valid_ic_days", "mean_ic", "icir"],
    )
