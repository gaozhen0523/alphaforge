#scripts/run_data_quality.py
"""Report quality diagnostics for the production processed OHLCV dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.data import MarketDataLoader, summarize_ohlcv_quality
from alphaforge.pipeline import BASELINE_CONFIG_PATH, load_pipeline_config


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
    data = MarketDataLoader(data_path).load()
    print("Summarizing data quality...")
    summary = summarize_ohlcv_quality(data)

    print("Production data quality")
    print(f"dataset: {data_path}")
    print(f"rows: {summary['rows']:,}")
    print(f"symbols: {summary['symbols']:,}")
    print(f"global dates: {summary['global_dates']:,}")
    print(f"duplicate pairs: {summary['duplicate_pairs']:,}")
    print(f"invalid observations: {summary['invalid_observations']:,}")
    print(f"expected panel rows: {summary['expected_panel_rows']:,}")
    print(f"observed unique rows: {summary['observed_unique_rows']:,}")
    print(f"missing observations: {summary['missing_observations']:,}")
    print(f"coverage ratio: {summary['coverage_ratio']:.4%}")
    print(
        "internal missing observations: "
        f"{summary['internal_missing_observations']:,}"
    )
    print(
        "boundary missing observations: "
        f"{summary['boundary_missing_observations']:,}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
