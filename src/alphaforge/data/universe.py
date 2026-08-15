#src/alphaforge/data/universe.py
"""Frozen CSI 300 universe snapshot creation and parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import akshare as ak
import pandas as pd

from .akshare import (
    a_share_code_to_canonical_symbol,
    canonical_to_akshare_symbol,
)

CSI300_INDEX_CODE: Final[str] = "000300"
CSI300_MEMBER_COUNT: Final[int] = 300
UNIVERSE_COLUMNS: Final[tuple[str, ...]] = (
    "snapshot_date",
    "symbol",
    "name",
)
_CSINDEX_COLUMNS: Final[dict[str, str]] = {
    "\u65e5\u671f": "snapshot_date",
    "\u6210\u5206\u5238\u4ee3\u7801": "code",
    "\u6210\u5206\u5238\u540d\u79f0": "name",
}


class UniverseSnapshotError(ValueError):
    """Raised when a universe snapshot is incomplete or malformed."""


def normalize_csi300_constituents(source: pd.DataFrame) -> pd.DataFrame:
    """Convert an AkShare CSIndex constituent response to a frozen snapshot."""

    if not isinstance(source, pd.DataFrame):
        raise TypeError("source must be a pandas DataFrame")
    if source.empty:
        raise UniverseSnapshotError("CSI 300 constituent response is empty")

    missing = [column for column in _CSINDEX_COLUMNS if column not in source]
    if missing:
        raise UniverseSnapshotError(
            f"CSI 300 constituent response is missing columns: {missing}"
        )

    selected = source.loc[:, list(_CSINDEX_COLUMNS)].rename(
        columns=_CSINDEX_COLUMNS
    )
    try:
        dates = pd.to_datetime(selected["snapshot_date"], errors="raise")
    except (TypeError, ValueError) as exc:
        raise UniverseSnapshotError("snapshot_date contains invalid values") from exc
    if isinstance(dates.dtype, pd.DatetimeTZDtype):
        raise UniverseSnapshotError("snapshot_date must be timezone-naive")
    dates = dates.dt.normalize()
    if dates.isna().any() or dates.nunique() != 1:
        raise UniverseSnapshotError(
            "CSI 300 response must contain exactly one snapshot_date"
        )

    codes = selected["code"].astype("string").str.strip()
    if codes.isna().any() or not codes.str.fullmatch(r"\d{6}").all():
        raise UniverseSnapshotError(
            "constituent codes must contain exactly six digits"
        )
    try:
        symbols = codes.map(a_share_code_to_canonical_symbol).astype("string")
    except (TypeError, ValueError) as exc:
        raise UniverseSnapshotError("constituent code cannot be canonicalized") from exc

    names = selected["name"].astype("string").str.strip()
    if names.isna().any() or names.eq("").any():
        raise UniverseSnapshotError("constituent names must not be missing")

    snapshot = pd.DataFrame(
        {
            "snapshot_date": dates.dt.strftime("%Y-%m-%d").astype("string"),
            "symbol": symbols,
            "name": names,
        }
    ).sort_values("symbol", kind="mergesort", ignore_index=True)

    if snapshot["symbol"].duplicated().any():
        raise UniverseSnapshotError("constituent symbols must be unique")
    return snapshot.loc[:, list(UNIVERSE_COLUMNS)]


def fetch_current_csi300_snapshot() -> pd.DataFrame:
    """Fetch and normalize the current CSI 300 membership for snapshotting only."""

    source = ak.index_stock_cons_csindex(symbol=CSI300_INDEX_CODE)
    snapshot = normalize_csi300_constituents(source)
    if len(snapshot) != CSI300_MEMBER_COUNT:
        raise UniverseSnapshotError(
            f"expected {CSI300_MEMBER_COUNT} CSI 300 members, got {len(snapshot)}"
        )
    return snapshot


def write_csi300_snapshot(snapshot: pd.DataFrame, output_dir: Path) -> Path:
    """Write a normalized snapshot to a date-stamped, Git-friendly CSV."""

    if tuple(snapshot.columns) != UNIVERSE_COLUMNS:
        raise UniverseSnapshotError(
            f"snapshot columns must be ordered as {UNIVERSE_COLUMNS}"
        )
    if snapshot.empty or snapshot["snapshot_date"].nunique() != 1:
        raise UniverseSnapshotError("snapshot must contain one snapshot_date")

    snapshot_date = str(snapshot["snapshot_date"].iloc[0])
    try:
        parsed_date = pd.Timestamp(snapshot_date)
    except ValueError as exc:
        raise UniverseSnapshotError("snapshot_date is invalid") from exc
    if parsed_date.strftime("%Y-%m-%d") != snapshot_date:
        raise UniverseSnapshotError("snapshot_date must use YYYY-MM-DD")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"csi300_{snapshot_date}.csv"
    snapshot.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def load_universe_symbols(path: Path, limit: int | None = None) -> list[str]:
    """Load, validate, and optionally limit canonical symbols from a frozen CSV."""

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer or None")

    universe = pd.read_csv(Path(path), dtype={"symbol": "string"})
    if "symbol" not in universe:
        raise UniverseSnapshotError("universe CSV must contain a symbol column")
    if universe.empty:
        raise UniverseSnapshotError("universe CSV must contain at least one symbol")

    symbols = universe["symbol"].astype("string").str.strip().str.upper()
    if symbols.isna().any() or symbols.eq("").any():
        raise UniverseSnapshotError("universe symbols must not be missing")
    if symbols.duplicated().any():
        raise UniverseSnapshotError("universe symbols must be unique")

    validated: list[str] = []
    for symbol in symbols:
        try:
            canonical_to_akshare_symbol(str(symbol))
        except (TypeError, ValueError) as exc:
            raise UniverseSnapshotError(
                f"invalid canonical universe symbol: {symbol}"
            ) from exc
        validated.append(str(symbol))

    return validated[:limit]
