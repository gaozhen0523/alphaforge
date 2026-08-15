from __future__ import annotations

import pytest

from alphaforge.data.symbols import (
    a_share_code_to_canonical_symbol,
    validate_canonical_symbol,
)


@pytest.mark.parametrize(
    "symbol",
    ["000001.SZ", "600000.SH", "430047.BJ"],
)
def test_valid_canonical_symbols_pass(symbol: str) -> None:
    assert validate_canonical_symbol(symbol) is None


@pytest.mark.parametrize(
    "symbol",
    [
        "600000.SZ",
        "000001.SH",
        "430047.SH",
        "600000.sh",
        "600000",
        " 600000.SH",
    ],
)
def test_invalid_canonical_symbols_are_rejected(symbol: str) -> None:
    with pytest.raises(ValueError):
        validate_canonical_symbol(symbol)


@pytest.mark.parametrize(
    ("code", "canonical"),
    [
        ("000001", "000001.SZ"),
        ("600000", "600000.SH"),
        ("430047", "430047.BJ"),
    ],
)
def test_a_share_code_converts_to_canonical_symbol(
    code: str,
    canonical: str,
) -> None:
    assert a_share_code_to_canonical_symbol(code) == canonical


def test_unsupported_a_share_code_prefix_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        a_share_code_to_canonical_symbol("200001")
