# Current Status

## Week / Day

Week 1 / Day 1 — Data

## Completed

- Repository initialization
- Python environment
- C++17 / CMake / pybind11 base environment configuration
- Canonical daily OHLCV contract, normalization, validation, and unit-test coverage
- Source-independent canonical A-share symbol contract shared by schema, universe,
  loader, and source adapters
- Day 1 data-source review and AkShare MVP recommendation
- Minimal AkShare Sina daily adapter fixed to the MVP hfq price contract
- Offline adapter unit tests and a two-symbol real-data smoke-test script
- EastMoney `stock_zh_a_hist` rejected by the current network; Sina selected as primary
- Frozen CSI 300 snapshot workflow using AkShare/CSIndex current constituents
- Sequential, rate-controlled bulk OHLCV acquisition with explicit failure summaries
- Consolidated canonical Parquet persistence with strict read-back validation
- Bulk CLI publishes the official Parquet only when every requested symbol succeeds
- Thin canonical `MarketDataLoader` with inclusive date/symbol filtering and
  explicit missing-symbol and empty-result semantics
- Offline tests for universe parsing, aggregation, pacing, failures, limits, duplicates,
  and Parquet round trips
- Offline MarketDataLoader tests covering filtering, validation, missing symbols,
  missing files, preserved observations, and canonical empty results

## Verification

- User-reported full pre-loader suite: 42+ tests passed with `uv run pytest`.
- User-reported real smoke dataset: 110 canonical rows for five symbols over 22
  trading days at `data/processed/ohlcv_hfq_smoke.parquet`.
- New MarketDataLoader tests are pending local execution because `uv` is not
  available on the Codex sandbox PATH.

## Current Task

- MarketDataLoader implementation is complete; local offline verification remains.

## Next

- Run `uv run pytest tests/test_market_data_loader.py` and then `uv run pytest`.
- Close Day 1 after the loader tests pass, then proceed to Day 2 factors.
