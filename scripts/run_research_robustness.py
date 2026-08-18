#scripts/run_research_robustness.py
"""Run Day 9 robustness analysis for the three baseline factors."""

from __future__ import annotations

from pathlib import Path

from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum, reversal, volatility
from alphaforge.research import (
    ResearchRobustnessResult,
    run_research_robustness,
)

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")
OUTPUT_DIR = Path("outputs/baseline")
FACTOR_COLUMNS = ("momentum_20d", "reversal_5d", "volatility_20d")
HORIZONS = (1, 2, 5, 10)
DECAY_LAGS = (0, 1, 2, 3, 4, 5, 10)


def save_research_robustness_outputs(
    result: ResearchRobustnessResult,
    output_dir: str | Path = OUTPUT_DIR,
) -> dict[str, Path]:
    """Persist compact Day 9 summaries without recomputing research."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "horizons": directory / "research_horizons.csv",
        "decay": directory / "factor_decay.csv",
        "yearly_ic": directory / "yearly_ic_stability.csv",
    }
    result.horizon_summary.to_csv(paths["horizons"], index=False)
    result.decay_summary.to_csv(paths["decay"], index=False)
    result.yearly_ic_summary.to_csv(paths["yearly_ic"], index=False)
    return paths


def main() -> int:
    data = MarketDataLoader(DATA_PATH).load()
    data["momentum_20d"] = momentum(data, window=20)
    data["reversal_5d"] = reversal(data, window=5)
    data["volatility_20d"] = volatility(data, window=20)

    result = run_research_robustness(
        data,
        FACTOR_COLUMNS,
        horizons=HORIZONS,
        decay_lags=DECAY_LAGS,
    )

    print("AlphaForge Day 9 research robustness")
    print(f"Dataset: {DATA_PATH}")
    print("\nMulti-horizon research")
    print(
        result.horizon_summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )
    print("\nFactor decay")
    print(
        result.decay_summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )
    print("\nYearly horizon-1 IC stability")
    print(
        result.yearly_ic_summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.8f}",
        )
    )

    paths = save_research_robustness_outputs(result)
    print("\nOutputs")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print("\nNotes")
    print("Longer-horizon forward returns overlap across formation dates.")
    print("ICIR is descriptive here, not a strict significance test.")
    print("Horizons use future available observations, not calendar sessions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
