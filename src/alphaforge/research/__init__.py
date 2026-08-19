"""Factor research utilities."""

from alphaforge.periods import OOS_PERIODS, assign_oos_period

from .combination import (
    combine_factors_by_rank,
    combine_factors_by_zscore,
    cross_sectional_zscore,
)
from .correlation import compute_factor_correlation
from .ic import compute_daily_ic, summarize_ic, summarize_yearly_ic
from .quantiles import (
    assign_quantiles,
    compute_quantile_returns,
    summarize_quantile_returns,
)
from .ranking import cross_sectional_rank
from .returns import compute_decay_return, compute_forward_return
from .out_of_sample import (
    compute_period_forward_return,
    run_out_of_sample_research,
)
from .robustness import (
    ResearchRobustnessResult,
    compute_factor_decay_ic,
    run_research_robustness,
)

__all__ = [
    "assign_quantiles",
    "combine_factors_by_rank",
    "combine_factors_by_zscore",
    "compute_decay_return",
    "compute_daily_ic",
    "compute_factor_decay_ic",
    "compute_factor_correlation",
    "compute_forward_return",
    "compute_period_forward_return",
    "compute_quantile_returns",
    "cross_sectional_rank",
    "cross_sectional_zscore",
    "OOS_PERIODS",
    "ResearchRobustnessResult",
    "run_research_robustness",
    "run_out_of_sample_research",
    "assign_oos_period",
    "summarize_ic",
    "summarize_quantile_returns",
    "summarize_yearly_ic",
]
