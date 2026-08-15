#src/alphaforge/data/akshare.py
"""Minimal AkShare adapter for canonical daily A-share OHLCV data."""

from __future__ import annotations

import re
from typing import Final

import akshare as ak
import pandas as pd

from .schema import normalize_ohlcv

_SINA_PRICE_ADJUSTMENT: Final[str] = "hfq"
_SINA_DAILY_COLUMNS: Final[tuple[str, ...]] = (
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
_SINA_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<exchange>sh|sz|bj)(?P<code>\d{6})$"
)
_CANONICAL_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<code>\d{6})\.(?P<exchange>SH|SZ|BJ)$"
)


class AkShareUpstreamDataError(RuntimeError):
    """Raised when AkShare returns no usable upstream market data."""


def _exchange_for_a_share_code(code: str) -> str:
    if not re.fullmatch(r"\d{6}", code):
        raise ValueError("A-share code must contain exactly six digits")
    if code.startswith("6"):
        return "SH"
    if code.startswith(("0", "3")):
        return "SZ"
    if code.startswith(("4", "8", "92")):
        return "BJ"
    raise ValueError(f"unsupported A-share symbol prefix: {code}")


def a_share_code_to_canonical_symbol(code: str) -> str:
    """Convert a six-digit mainland A-share code to canonical form."""

    if not isinstance(code, str):
        raise TypeError("code must be a string")
    normalized = code.strip()
    exchange = _exchange_for_a_share_code(normalized)
    return f"{normalized}.{exchange}"


def akshare_to_canonical_symbol(symbol: str) -> str:
    """Convert a Sina-form AkShare symbol to canonical form."""

    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string")
    normalized = symbol.strip().lower()
    match = _SINA_SYMBOL_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError("Sina symbol must use sh, sz, or bj plus six digits")

    code = match.group("code")
    exchange = match.group("exchange").upper()
    expected_exchange = _exchange_for_a_share_code(code)
    if exchange != expected_exchange:
        raise ValueError(
            f"symbol {normalized} has exchange {exchange}; expected {expected_exchange}"
        )
    return f"{code}.{exchange}"


def canonical_to_akshare_symbol(symbol: str) -> str:
    """Convert a canonical A-share symbol to Sina's market-prefixed form."""

    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string")
    normalized = symbol.strip().upper()
    match = _CANONICAL_SYMBOL_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError("canonical symbol must use six digits plus .SH, .SZ, or .BJ")

    code = match.group("code")
    exchange = match.group("exchange")
    expected_exchange = _exchange_for_a_share_code(code)
    if exchange != expected_exchange:
        raise ValueError(
            f"symbol {normalized} has exchange {exchange}; expected {expected_exchange}"
        )
    return f"{exchange.lower()}{code}"


def fetch_akshare_daily_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch one symbol's hfq-adjusted Sina daily bars as canonical OHLCV.

    ``symbol`` uses AlphaForge's canonical format. Sina volume is already in
    shares.
    """

    external_symbol = canonical_to_akshare_symbol(symbol)
    source = ak.stock_zh_a_daily(
        symbol=external_symbol,
        start_date=start_date,
        end_date=end_date,
        adjust=_SINA_PRICE_ADJUSTMENT,
    )

    if source.empty:
        raise AkShareUpstreamDataError(
            "AkShare stock_zh_a_daily returned no rows for "
            f"{symbol} from {start_date} to {end_date} "
            f"with adjust={_SINA_PRICE_ADJUSTMENT}"
        )

    missing = [column for column in _SINA_DAILY_COLUMNS if column not in source]
    if missing:
        raise AkShareUpstreamDataError(
            f"AkShare stock_zh_a_daily is missing required columns: {missing}"
        )

    canonical = source.loc[:, list(_SINA_DAILY_COLUMNS)].copy()
    canonical.insert(1, "symbol", akshare_to_canonical_symbol(external_symbol))
    return normalize_ohlcv(canonical)
