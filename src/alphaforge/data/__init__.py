#src/alphaforge/data/__init__.py
"""Canonical market-data contracts for AlphaForge."""

from .akshare import (
    AkShareUpstreamDataError,
    akshare_to_canonical_symbol,
    canonical_to_akshare_symbol,
    fetch_akshare_daily_ohlcv,
)
from .bulk import (
    BulkDownloadResult,
    DownloadFailure,
    download_daily_ohlcv,
    write_canonical_parquet,
)
from .loader import MarketDataLoader
from .schema import (
    CANONICAL_OHLCV_COLUMNS,
    CANONICAL_OHLCV_DTYPES,
    OHLCVValidationError,
    normalize_ohlcv,
    validate_ohlcv,
)
from .symbols import a_share_code_to_canonical_symbol, validate_canonical_symbol
from .universe import (
    CSI300_INDEX_CODE,
    UniverseSnapshotError,
    fetch_current_csi300_snapshot,
    load_universe_symbols,
    normalize_csi300_constituents,
    write_csi300_snapshot,
)

__all__ = [
    "CANONICAL_OHLCV_COLUMNS",
    "CANONICAL_OHLCV_DTYPES",
    "CSI300_INDEX_CODE",
    "AkShareUpstreamDataError",
    "BulkDownloadResult",
    "DownloadFailure",
    "MarketDataLoader",
    "OHLCVValidationError",
    "UniverseSnapshotError",
    "a_share_code_to_canonical_symbol",
    "akshare_to_canonical_symbol",
    "canonical_to_akshare_symbol",
    "download_daily_ohlcv",
    "fetch_current_csi300_snapshot",
    "fetch_akshare_daily_ohlcv",
    "load_universe_symbols",
    "normalize_ohlcv",
    "normalize_csi300_constituents",
    "validate_ohlcv",
    "validate_canonical_symbol",
    "write_canonical_parquet",
    "write_csi300_snapshot",
]
