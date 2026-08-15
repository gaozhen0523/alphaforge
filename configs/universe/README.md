# Frozen Universe Snapshots

Generate the Week 1 CSI 300 snapshot manually:

```bash
uv run python scripts/snapshot_csi300_universe.py
```

Commit the resulting `csi300_<snapshot_date>.csv` and pass that exact file to the
bulk downloader. Do not resolve current constituents during downstream research or
backtests.

These snapshots contain current membership as of their recorded source date. They
are not point-in-time historical universes and therefore introduce survivorship
and membership bias when used over earlier price history.
