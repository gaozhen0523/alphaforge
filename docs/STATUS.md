# Current Status

## Week / Day

Week 1 / Day 1 — Data

## Completed

- Repository initialization
- Python environment
- C++17 / CMake / pybind11 base environment configuration
- Canonical daily OHLCV contract, normalization, validation, and unit-test coverage
- Day 1 data-source review and AkShare MVP recommendation
- Minimal AkShare Sina daily adapter fixed to the MVP hfq price contract
- Offline adapter unit tests and a two-symbol real-data smoke-test script
- EastMoney `stock_zh_a_hist` rejected by the current network; Sina selected as primary
- Frozen CSI 300 snapshot workflow using AkShare/CSIndex current constituents
- Sequential, rate-controlled bulk OHLCV acquisition with explicit failure summaries
- Consolidated canonical Parquet persistence with strict read-back validation
- Bulk CLI publishes the official Parquet only when every requested symbol succeeds
- Offline tests for universe parsing, aggregation, pacing, failures, limits, duplicates,
  and Parquet round trips

## Verification

- User-reported baseline: `uv run pytest` passed 20 tests.
- User-reported real-data smoke test: 44 validated rows for two symbols.
- The new frozen-universe/bulk/Parquet tests are pending local execution because
  `uv` is not available on the Codex sandbox PATH.

## Current Task

- Generate and commit one real CSI 300 snapshot, then run a limited real bulk
  download before the full manual acquisition.

## Next

- Run the full offline suite locally with `uv run pytest`.
- Generate the frozen snapshot with
  `uv run python scripts/snapshot_csi300_universe.py`.
- Run `scripts/download_market_data.py` with `--limit 5` over a short date range.
- After the smoke acquisition succeeds, manually download the full frozen universe.
