#src/alphaforge/analytics/cost_analysis.py
"""Cost sensitivity and turnover summaries for a frozen strategy."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from alphaforge.backtest import run_backtest

from .metrics import summarize_performance


def summarize_turnover(
    daily_summary: pd.DataFrame,
    periods_per_year: int = 252,
) -> pd.Series:
    """Summarize existing Day 5 turnover and traded-weight outputs.

    Execution-level statistics use the existing Day 5 ``is_execution`` flag,
    including scheduled executions whose resulting trade weight is zero.
    """

    executions = daily_summary.loc[
        daily_summary["is_execution"],
        "gross_traded_weight",
    ]
    turnover = daily_summary["turnover"]
    average_daily_turnover = float(turnover.mean())

    return pd.Series(
        {
            "execution_count": int(len(executions)),
            "total_gross_traded_weight": float(
                daily_summary["gross_traded_weight"].sum()
            ),
            "mean_execution_gross_traded_weight": float(
                executions.mean()
            ),
            "median_execution_gross_traded_weight": float(
                executions.median()
            ),
            "max_execution_gross_traded_weight": float(
                executions.max()
            ),
            "total_turnover": float(turnover.sum()),
            "average_daily_turnover": average_daily_turnover,
            "annualized_turnover": average_daily_turnover
            * periods_per_year,
        }
    )


def run_cost_sensitivity(
    market_data: pd.DataFrame,
    portfolio: pd.DataFrame,
    cost_scenarios: Iterable[tuple[float, float]],
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Evaluate fixed trading decisions under linear friction assumptions.

    Each scenario reuses ``run_backtest`` and ``summarize_performance``. The
    ``total_cost_load`` output is the arithmetic sum of daily cost rates, not
    the direct compounded NAV loss.
    """

    rows = []
    for transaction_cost_bps, slippage_bps in cost_scenarios:
        _, daily = run_backtest(
            market_data,
            portfolio,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
        )
        performance = summarize_performance(
            daily,
            annualization_factor=periods_per_year,
        )
        gross_ending_nav = float((1.0 + daily["gross_return"]).prod())

        rows.append(
            {
                "transaction_cost_bps": float(transaction_cost_bps),
                "slippage_bps": float(slippage_bps),
                "total_friction_bps": float(
                    transaction_cost_bps + slippage_bps
                ),
                "annualized_return": performance["annualized_return"],
                "annualized_volatility": performance[
                    "annualized_volatility"
                ],
                "sharpe": performance["sharpe_ratio"],
                "max_drawdown": performance["max_drawdown"],
                "cumulative_return": performance["cumulative_return"],
                "ending_nav": performance["ending_nav"],
                "gross_cumulative_return": gross_ending_nav - 1.0,
                "gross_ending_nav": gross_ending_nav,
                "gross_net_cumulative_return_gap": (
                    gross_ending_nav - 1.0
                    - performance["cumulative_return"]
                ),
                "total_gross_traded_weight": float(
                    daily["gross_traded_weight"].sum()
                ),
                "total_turnover": performance["total_turnover"],
                "average_daily_turnover": performance[
                    "average_daily_turnover"
                ],
                "annualized_turnover": performance[
                    "annualized_turnover"
                ],
                "total_cost_load": float(daily["total_cost"].sum()),
            }
        )

    return pd.DataFrame(rows)
