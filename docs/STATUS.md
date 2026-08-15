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

## Verification

- Tests are pending local execution with `uv run pytest`; Codex sandbox cannot
  access the existing uv-managed Python environment.

## Current Task

- Market Data Layer: real-data smoke verification and persistence remain

## Next

- Run the adapter unit tests and real-data smoke test locally.
- Define the full Week 1 frozen static universe.
- Validate and store a small OHLCV dataset as Parquet in a separate step.
