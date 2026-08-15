#src/alphaforge/data/__init__.py
"""Canonical market-data contracts for AlphaForge."""

from .akshare import (
    AkShareUpstreamDataError,
    akshare_to_canonical_symbol,
    canonical_to_akshare_symbol,
    fetch_akshare_daily_ohlcv,
)
from .schema import (
    CANONICAL_OHLCV_COLUMNS,
    CANONICAL_OHLCV_DTYPES,
    OHLCVValidationError,
    normalize_ohlcv,
    validate_ohlcv,
)

__all__ = [
    "CANONICAL_OHLCV_COLUMNS",
    "CANONICAL_OHLCV_DTYPES",
    "AkShareUpstreamDataError",
    "OHLCVValidationError",
    "akshare_to_canonical_symbol",
    "canonical_to_akshare_symbol",
    "fetch_akshare_daily_ohlcv",
    "normalize_ohlcv",
    "validate_ohlcv",
]
