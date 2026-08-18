#scripts/run_data_quality.py
"""Report quality diagnostics for the production processed OHLCV dataset."""

from __future__ import annotations

from pathlib import Path

from alphaforge.data import MarketDataLoader, summarize_ohlcv_quality

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")


def main() -> None:
    data = MarketDataLoader(DATA_PATH).load()
    summary = summarize_ohlcv_quality(data)

    print("Production data quality")
    print(f"dataset: {DATA_PATH}")
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


if __name__ == "__main__":
    main()
