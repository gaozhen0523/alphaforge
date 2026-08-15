from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from alphaforge.data.universe import (
    UniverseSnapshotError,
    fetch_current_csi300_snapshot,
    load_universe_symbols,
    normalize_csi300_constituents,
    write_csi300_snapshot,
)


def csindex_source() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "\u65e5\u671f": ["2026-08-14", "2026-08-14"],
            "\u6307\u6570\u4ee3\u7801": ["000300", "000300"],
            "\u6210\u5206\u5238\u4ee3\u7801": ["600000", "000001"],
            "\u6210\u5206\u5238\u540d\u79f0": [
                "\u6d66\u53d1\u94f6\u884c",
                "\u5e73\u5b89\u94f6\u884c",
            ],
            "\u4ea4\u6613\u6240": [
                "\u4e0a\u6d77\u8bc1\u5238\u4ea4\u6613\u6240",
                "\u6df1\u5733\u8bc1\u5238\u4ea4\u6613\u6240",
            ],
        }
    )


def test_csi300_constituents_become_canonical_frozen_snapshot() -> None:
    snapshot = normalize_csi300_constituents(csindex_source())

    assert snapshot.to_dict(orient="records") == [
        {
            "snapshot_date": "2026-08-14",
            "symbol": "000001.SZ",
            "name": "\u5e73\u5b89\u94f6\u884c",
        },
        {
            "snapshot_date": "2026-08-14",
            "symbol": "600000.SH",
            "name": "\u6d66\u53d1\u94f6\u884c",
        },
    ]


def test_current_snapshot_uses_csindex_interface_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = pd.DataFrame(
        {
            "\u65e5\u671f": ["2026-08-14"] * 300,
            "\u6210\u5206\u5238\u4ee3\u7801": [
                f"600{number:03d}" for number in range(300)
            ],
            "\u6210\u5206\u5238\u540d\u79f0": [
                f"member-{number}" for number in range(300)
            ],
        }
    )
    calls: list[str] = []

    def fake_constituents(*, symbol: str) -> pd.DataFrame:
        calls.append(symbol)
        return source

    monkeypatch.setattr(
        "alphaforge.data.universe.ak.index_stock_cons_csindex",
        fake_constituents,
    )

    snapshot = fetch_current_csi300_snapshot()

    assert calls == ["000300"]
    assert len(snapshot) == 300
    assert snapshot["symbol"].iloc[[0, -1]].tolist() == [
        "600000.SH",
        "600299.SH",
    ]


def test_snapshot_rejects_mixed_source_dates() -> None:
    source = csindex_source()
    source.loc[1, "\u65e5\u671f"] = "2026-08-13"

    with pytest.raises(UniverseSnapshotError, match="one snapshot_date"):
        normalize_csi300_constituents(source)


def test_snapshot_csv_is_date_stamped_and_loads_canonical_symbols(
    tmp_path: Path,
) -> None:
    snapshot = normalize_csi300_constituents(csindex_source())

    path = write_csi300_snapshot(snapshot, tmp_path)

    assert path.name == "csi300_2026-08-14.csv"
    assert load_universe_symbols(path) == ["000001.SZ", "600000.SH"]


def test_universe_limit_preserves_frozen_order(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    normalize_csi300_constituents(csindex_source()).to_csv(path, index=False)

    assert load_universe_symbols(path, limit=1) == ["000001.SZ"]


def test_universe_limit_none_loads_all_symbols(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    normalize_csi300_constituents(csindex_source()).to_csv(path, index=False)

    assert load_universe_symbols(path, limit=None) == [
        "000001.SZ",
        "600000.SH",
    ]


def test_universe_rejects_duplicate_symbols(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    pd.DataFrame({"symbol": ["000001.SZ", "000001.SZ"]}).to_csv(
        path, index=False
    )

    with pytest.raises(UniverseSnapshotError, match="must be unique"):
        load_universe_symbols(path)


def test_universe_rejects_noncanonical_symbol(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    pd.DataFrame({"symbol": ["600000.SZ"]}).to_csv(path, index=False)

    with pytest.raises(UniverseSnapshotError, match="invalid canonical"):
        load_universe_symbols(path)


@pytest.mark.parametrize("limit", [True, False, 1.0, 1.5, 0, -1])
def test_universe_limit_must_be_positive_integer(
    tmp_path: Path,
    limit: object,
) -> None:
    path = tmp_path / "universe.csv"
    pd.DataFrame({"symbol": ["000001.SZ"]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="positive"):
        load_universe_symbols(path, limit=limit)  # type: ignore[arg-type]
