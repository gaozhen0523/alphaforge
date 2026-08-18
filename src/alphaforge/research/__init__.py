"""Factor research utilities."""

from .correlation import compute_factor_correlation
from .ic import compute_daily_ic, summarize_ic, summarize_yearly_ic
from .quantiles import (
    assign_quantiles,
    compute_quantile_returns,
    summarize_quantile_returns,
)
from .ranking import cross_sectional_rank
from .returns import compute_decay_return, compute_forward_return
from .robustness import (
    ResearchRobustnessResult,
    compute_factor_decay_ic,
    run_research_robustness,
)

__all__ = [
    "assign_quantiles",
    "compute_decay_return",
    "compute_daily_ic",
    "compute_factor_decay_ic",
    "compute_factor_correlation",
    "compute_forward_return",
    "compute_quantile_returns",
    "cross_sectional_rank",
    "ResearchRobustnessResult",
    "run_research_robustness",
    "summarize_ic",
    "summarize_quantile_returns",
    "summarize_yearly_ic",
]
