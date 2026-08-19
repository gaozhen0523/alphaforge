#scripts/run_research_robustness.py
"""Run Day 9 robustness analysis for the three baseline factors."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.data import MarketDataLoader
from alphaforge.pipeline import (
    BASELINE_CONFIG_PATH,
    compute_baseline_factors,
    load_pipeline_config,
)
from alphaforge.research import (
    ResearchRobustnessResult,
    run_research_robustness,
)

HORIZONS = (1, 2, 5, 10)
DECAY_LAGS = (0, 1, 2, 3, 4, 5, 10)


def save_research_robustness_outputs(
    result: ResearchRobustnessResult,
    output_dir: str | Path,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        default=BASELINE_CONFIG_PATH,
        help=f"pipeline TOML path (default: {BASELINE_CONFIG_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Loading config: {args.config}")
    config = load_pipeline_config(args.config)

    data_path = config["data"]["processed_path"]
    print(f"Loading market data: {data_path}")
    market_data = MarketDataLoader(data_path).load()
    print("Computing baseline factors...")
    data = compute_baseline_factors(market_data, config["factors"])

    print("Running robustness research...")
    result = run_research_robustness(
        data,
        config["research"]["factors"],
        horizons=HORIZONS,
        decay_lags=DECAY_LAGS,
    )

    print("AlphaForge Day 9 research robustness")
    print(f"Dataset: {data_path}")
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

    print("\nSaving outputs...")
    paths = save_research_robustness_outputs(
        result,
        config["output"]["directory"],
    )
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
