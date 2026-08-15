# scripts/snapshot_csi300_universe.py
"""Generate a frozen, date-stamped CSI 300 universe snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from alphaforge.data.universe import (
    fetch_current_csi300_snapshot,
    write_csi300_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch the current CSI 300 membership and freeze it as CSV."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("configs/universe"),
        help="snapshot directory (default: configs/universe)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = fetch_current_csi300_snapshot()
    output_path = write_csi300_snapshot(snapshot, args.output_dir)
    print(
        f"wrote {len(snapshot)} CSI 300 symbols for "
        f"snapshot_date={snapshot['snapshot_date'].iloc[0]} to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
