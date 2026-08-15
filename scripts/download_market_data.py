#scripts/download_market_data.py
"""Manually download a frozen universe to one canonical Parquet dataset."""

from __future__ import annotations

import argparse
import logging
from math import isfinite
from pathlib import Path
from typing import Sequence

from alphaforge.data.bulk import download_daily_ohlcv, write_canonical_parquet
from alphaforge.data.universe import load_universe_symbols

LOGGER = logging.getLogger(__name__)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if not isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("must be finite and non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Sequentially download hfq daily OHLCV for a frozen universe and "
            "write one canonical Parquet file."
        )
    )
    parser.add_argument("--universe", required=True, type=Path)
    parser.add_argument("--start-date", required=True, help="inclusive YYYYMMDD")
    parser.add_argument("--end-date", required=True, help="inclusive YYYYMMDD")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/ohlcv_hfq.parquet"),
    )
    parser.add_argument(
        "--delay",
        type=_non_negative_float,
        default=2.0,
        help="seconds between sequential symbol requests (default: 2.0)",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        help="download only the first N frozen symbols",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    symbols = load_universe_symbols(args.universe, limit=args.limit)
    result = download_daily_ohlcv(
        symbols,
        args.start_date,
        args.end_date,
        delay_seconds=args.delay,
    )

    for failure in result.failures:
        LOGGER.error(
            "symbol=%s error_type=%s reason=%s",
            failure.symbol,
            failure.error_type,
            failure.reason,
        )

    if result.failures:
        LOGGER.error(
            "summary requested=%d succeeded=%d failures=%d rows=%d; "
            "official output not written",
            len(result.requested_symbols),
            len(result.succeeded_symbols),
            len(result.failures),
            len(result.data),
        )
        return 1

    if result.data.empty:
        LOGGER.error(
            "summary requested=%d succeeded=0 failures=%d rows=0; no Parquet written",
            len(result.requested_symbols),
            len(result.failures),
        )
        return 1

    write_canonical_parquet(result.data, args.output)
    LOGGER.info(
        "summary requested=%d succeeded=%d failures=%d rows=%d output=%s",
        len(result.requested_symbols),
        len(result.succeeded_symbols),
        len(result.failures),
        len(result.data),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
