#src/alphaforge/analytics/metrics.py
"""Performance metrics for backtest daily summaries."""

from __future__ import annotations

import numpy as np
import pandas as pd


def annualized_return(
    daily_return: pd.Series,
    annualization_factor: int = 252,
) -> float:
    """Return compounded annualized growth from period returns.

    Each value is one completed return period. The starting NAV immediately
    before the first value is 1.0, matching the backtest daily-summary contract.
    """

    ending_nav = (1.0 + daily_return).prod()
    return float(ending_nav ** (annualization_factor / len(daily_return)) - 1.0)


def annualized_volatility(
    daily_return: pd.Series,
    annualization_factor: int = 252,
) -> float:
    """Return sample volatility annualized from daily net returns."""

    return float(daily_return.std(ddof=1) * np.sqrt(annualization_factor))


def sharpe_ratio(
    daily_return: pd.Series,
    annualization_factor: int = 252,
) -> float:
    """Return the zero-risk-free-rate annualized Sharpe ratio."""

    daily_volatility = daily_return.std(ddof=1)
    if daily_volatility == 0:
        return float("nan")
    return float(
        daily_return.mean() / daily_volatility * np.sqrt(annualization_factor)
    )


def max_drawdown(nav: pd.Series, starting_nav: float = 1.0) -> float:
    """Return the worst peak-to-trough NAV drawdown as a non-positive value."""

    nav_path = pd.concat(
        [pd.Series([starting_nav], dtype=float), nav.reset_index(drop=True)],
        ignore_index=True,
    )
    drawdown = nav_path.div(nav_path.cummax()).sub(1.0)
    return float(drawdown.min())


def summarize_performance(
    daily_summary: pd.DataFrame,
    annualization_factor: int = 252,
) -> pd.Series:
    """Summarize return, risk, NAV, and existing Day 5 turnover output."""

    daily_return = daily_summary["net_return"]
    nav = daily_summary["nav"]
    turnover = daily_summary["turnover"]
    ending_nav = float(nav.iloc[-1])
    average_daily_turnover = float(turnover.mean())

    return pd.Series(
        {
            "annualized_return": annualized_return(
                daily_return, annualization_factor
            ),
            "annualized_volatility": annualized_volatility(
                daily_return, annualization_factor
            ),
            "sharpe_ratio": sharpe_ratio(daily_return, annualization_factor),
            "max_drawdown": max_drawdown(nav),
            "total_turnover": float(turnover.sum()),
            "average_daily_turnover": average_daily_turnover,
            "annualized_turnover": average_daily_turnover
            * annualization_factor,
            "ending_nav": ending_nav,
            "cumulative_return": ending_nav - 1.0,
        },
        dtype=float,
    )
