#src/alphaforge/research/robustness.py
"""Descriptive robustness analysis for baseline factor research."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from .ic import compute_daily_ic, summarize_ic, summarize_yearly_ic
from .quantiles import (
    assign_quantiles,
    compute_quantile_returns,
    summarize_quantile_returns,
)
from .returns import compute_decay_return, compute_forward_return


@dataclass(frozen=True)
class ResearchRobustnessResult:
    """Structured horizon, decay, and yearly IC robustness results."""

    horizon_summary: pd.DataFrame
    decay_summary: pd.DataFrame
    yearly_ic_summary: pd.DataFrame
    horizon_daily_ic: pd.DataFrame
    decay_daily_ic: pd.DataFrame


def compute_factor_decay_ic(
    df: pd.DataFrame,
    factor_cols: Sequence[str],
    lags: Sequence[int],
    price_col: str = "close",
    min_obs: int = 5,
) -> pd.DataFrame:
    """Compute daily decay IC while keeping factor values at formation date.

    For each lag, ``factor(t)`` is paired with the one-observation return from
    ``t + lag`` to ``t + lag + 1``. Both offsets use each symbol's future
    available observations.
    """

    factor_cols = tuple(factor_cols)
    rows = []
    for lag in lags:
        decay_return = compute_decay_return(
            df,
            lag=lag,
            price_col=price_col,
        )
        for factor_col in factor_cols:
            research_frame = df.loc[:, ["date", factor_col]].copy()
            research_frame["decay_return"] = decay_return
            daily_ic = compute_daily_ic(
                research_frame,
                factor_col,
                return_col="decay_return",
                min_obs=min_obs,
            )
            rows.append(
                pd.DataFrame(
                    {
                        "factor": factor_col,
                        "date": daily_ic.index,
                        "lag": lag,
                        "ic": daily_ic.to_numpy(),
                    }
                )
            )

    return pd.concat(rows, ignore_index=True).loc[
        :, ["factor", "date", "lag", "ic"]
    ]


def run_research_robustness(
    df: pd.DataFrame,
    factor_cols: Sequence[str],
    horizons: Sequence[int] = (1, 2, 5, 10),
    decay_lags: Sequence[int] = (0, 1, 2, 3, 4, 5, 10),
    price_col: str = "close",
    min_obs: int = 5,
) -> ResearchRobustnessResult:
    """Run descriptive multi-horizon, decay, and yearly IC analysis.

    Yearly stability uses the horizon-1 daily IC series and groups it by the
    calendar year of the factor formation date.
    """

    if 1 not in horizons:
        raise ValueError("horizons must include 1 for yearly IC stability")

    factor_cols = tuple(factor_cols)
    horizon_rows = []
    horizon_daily_rows = []
    horizon_one_ic = {}
    quantiles = {
        factor_col: assign_quantiles(
            df.loc[:, ["date", factor_col]],
            factor_col,
            n_quantiles=5,
        )
        for factor_col in factor_cols
    }

    for horizon in horizons:
        forward_return = compute_forward_return(
            df,
            horizon=horizon,
            price_col=price_col,
        )
        for factor_col in factor_cols:
            research_frame = df.loc[:, ["date", factor_col]].copy()
            research_frame["forward_return"] = forward_return
            daily_ic = compute_daily_ic(
                research_frame,
                factor_col,
                min_obs=min_obs,
            )
            ic_summary = summarize_ic(daily_ic)

            quantile_frame = research_frame.loc[
                :, ["date", "forward_return"]
            ].copy()
            quantile_frame["quantile"] = quantiles[factor_col]
            quantile_returns = compute_quantile_returns(
                quantile_frame,
                n_quantiles=5,
            )
            quantile_summary = summarize_quantile_returns(quantile_returns)

            horizon_rows.append(
                {
                    "factor": factor_col,
                    "horizon": horizon,
                    "valid_ic_days": int(ic_summary["n_obs"]),
                    "mean_ic": ic_summary["mean_ic"],
                    "icir": ic_summary["icir"],
                    "q5_minus_q1_mean": quantile_summary[
                        "top_minus_bottom"
                    ],
                }
            )
            horizon_daily_rows.append(
                pd.DataFrame(
                    {
                        "factor": factor_col,
                        "horizon": horizon,
                        "date": daily_ic.index,
                        "ic": daily_ic.to_numpy(),
                    }
                )
            )
            if horizon == 1:
                horizon_one_ic[factor_col] = daily_ic

    decay_daily_ic = compute_factor_decay_ic(
        df,
        factor_cols,
        decay_lags,
        price_col=price_col,
        min_obs=min_obs,
    )
    decay_rows = []
    for (factor_col, lag), lag_data in decay_daily_ic.groupby(
        ["factor", "lag"],
        sort=True,
    ):
        ic_summary = summarize_ic(lag_data["ic"])
        decay_rows.append(
            {
                "factor": factor_col,
                "lag": int(lag),
                "valid_ic_days": int(ic_summary["n_obs"]),
                "mean_ic": ic_summary["mean_ic"],
                "icir": ic_summary["icir"],
            }
        )

    yearly_ic_summary = pd.concat(
        [
            summarize_yearly_ic(horizon_one_ic[factor_col], factor_col)
            for factor_col in factor_cols
        ],
        ignore_index=True,
    )

    horizon_summary = pd.DataFrame(horizon_rows).sort_values(
        ["factor", "horizon"],
        ignore_index=True,
    )
    decay_summary = pd.DataFrame(decay_rows).sort_values(
        ["factor", "lag"],
        ignore_index=True,
    )
    horizon_daily_ic = pd.concat(horizon_daily_rows, ignore_index=True)

    return ResearchRobustnessResult(
        horizon_summary=horizon_summary,
        decay_summary=decay_summary,
        yearly_ic_summary=yearly_ic_summary,
        horizon_daily_ic=horizon_daily_ic,
        decay_daily_ic=decay_daily_ic,
    )
