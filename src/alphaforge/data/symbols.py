"""Source-independent AlphaForge A-share symbol contract."""

from __future__ import annotations

import re
from typing import Final

_CANONICAL_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?P<code>\d{6})\.(?P<exchange>SH|SZ|BJ)$"
)


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
    """Convert a six-digit A-share code to AlphaForge canonical form."""

    if not isinstance(code, str):
        raise TypeError("code must be a string")
    normalized = code.strip()
    exchange = _exchange_for_a_share_code(normalized)
    return f"{normalized}.{exchange}"


def validate_canonical_symbol(symbol: str) -> None:
    """Validate one exact AlphaForge canonical A-share symbol."""

    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string")
    match = _CANONICAL_SYMBOL_PATTERN.fullmatch(symbol)
    if match is None:
        raise ValueError(
            "canonical symbol must use six digits plus .SH, .SZ, or .BJ"
        )

    code = match.group("code")
    exchange = match.group("exchange")
    expected_exchange = _exchange_for_a_share_code(code)
    if exchange != expected_exchange:
        raise ValueError(
            f"symbol {symbol} has exchange {exchange}; expected {expected_exchange}"
        )
